import os
import re
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date

from db_utils import get_db, clean_doc, db_is_up, next_id
from auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
    require_role
)
from core.services.government_api import GovernmentAPIClient

# Global tracker for Government API health & auto-sync state
AUTO_SYNC_STATE = {
    "status": "INITIALIZING",
    "is_online": False,
    "last_checked": None,
    "last_successful_sync": None,
    "records_synced_last_run": 0,
    "total_records_synced": 0,
    "probe_message": "Starting background heartbeat probe...",
    "poll_interval_seconds": int(os.getenv("GOV_API_POLL_INTERVAL", "300"))
}

async def auto_sync_worker():
    """
    Autonomous background worker for government mandi price polling.
    """
    await asyncio.sleep(2)
    api_client = GovernmentAPIClient()
    
    while True:
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            AUTO_SYNC_STATE["last_checked"] = now_str
            
            is_online, msg = await asyncio.to_thread(api_client.check_health, timeout=3)
            AUTO_SYNC_STATE["is_online"] = is_online
            AUTO_SYNC_STATE["probe_message"] = msg
            
            if is_online:
                AUTO_SYNC_STATE["status"] = "SYNCING"
                count = await asyncio.to_thread(api_client.sync_market_prices)
                AUTO_SYNC_STATE["status"] = "ONLINE"
                AUTO_SYNC_STATE["last_successful_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                AUTO_SYNC_STATE["records_synced_last_run"] = count
                AUTO_SYNC_STATE["total_records_synced"] += count
            else:
                AUTO_SYNC_STATE["status"] = "OFFLINE"
        except Exception as e:
            AUTO_SYNC_STATE["status"] = "ERROR"
            AUTO_SYNC_STATE["probe_message"] = f"Error: {e}"
            
        await asyncio.sleep(AUTO_SYNC_STATE["poll_interval_seconds"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = asyncio.create_task(auto_sync_worker())
    yield
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="AgriScan API",
    description="Offline-First AI Crop Disease & Pest Detection, Knowledge Advisory, and Market Intelligence API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    login_id: str = Field(..., min_length=3, max_length=100) # Phone number or email
    password: str = Field(..., min_length=6)
    preferred_language: Optional[str] = "en" # "en", "hi", "gu"

class LoginRequest(BaseModel):
    login_id: str
    password: str

class LocationModel(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    region: Optional[str] = None

class ScanItem(BaseModel):
    client_uuid: str
    device_id: Optional[str] = None
    class_key: str
    crop_id: Optional[int] = None
    confidence: float
    language: Optional[str] = "en"
    location: Optional[LocationModel] = None
    scanned_at: Optional[str] = None
    user_id: Optional[Any] = None

class SyncScansRequest(BaseModel):
    scans: List[ScanItem]

# -------------------------------------------------------------
# HEALTH & SYSTEM ROUTES
# -------------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to AgriScan API (Offline-First AI Crop Disease Detection)",
        "version": "2.0.0",
        "database_connected": db_is_up(),
        "auto_sync_status": AUTO_SYNC_STATE["status"]
    }

@app.get("/api/health", tags=["System"])
def get_health():
    """Confirms the database is reachable and returns server health status."""
    is_up = db_is_up()
    return {
        "status": "healthy" if is_up else "degraded",
        "database": "connected" if is_up else "disconnected",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0.0"
    }

@app.get("/api/sync-status", tags=["Intelligence"])
def get_sync_status():
    return AUTO_SYNC_STATE

# -------------------------------------------------------------
# AUTHENTICATION ROUTES (Section 5.7)
# -------------------------------------------------------------

@app.post("/api/auth/register", tags=["Auth"])
def register_user(req: RegisterRequest):
    """
    Registers a new farmer account: validates input, hashes password with bcrypt,
    creates account in MongoDB, and returns signed JWT token.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    raw_login = req.login_id.strip()
    is_email = "@" in raw_login
    normalized_login = raw_login.lower() if is_email else re.sub(r"[^\d]", "", raw_login)

    if not is_email and len(normalized_login) != 10:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid 10-digit mobile number or email address."
        )

    # Check for existing account
    existing = db.users.find_one({"login_id": normalized_login})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this mobile number or email already exists. Please log in."
        )

    new_id = next_id("user_id")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user_doc = {
        "id": new_id,
        "name": req.name.strip(),
        "login_id": normalized_login,
        "password_hash": hash_password(req.password),
        "role": "farmer",
        "preferred_language": req.preferred_language or "en",
        "created_at": now_str,
        "last_login": now_str
    }

    db.users.insert_one(user_doc)

    token = create_access_token(
        user_id=new_id,
        role="farmer",
        login_id=normalized_login,
        name=req.name.strip()
    )

    clean_user = clean_doc(user_doc)
    clean_user.pop("password_hash", None)

    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": token,
        "user": clean_user
    }

@app.post("/api/auth/login", tags=["Auth"])
def login_user(req: LoginRequest):
    """
    Authenticates farmer or officer. Returns generic error on failure to prevent enumeration.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    raw_login = req.login_id.strip()
    normalized_login = raw_login.lower() if "@" in raw_login else re.sub(r"[^\d]", "", raw_login)

    user = db.users.find_one({"login_id": normalized_login})
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number/email or password."
        )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.users.update_one({"id": user["id"]}, {"$set": {"last_login": now_str}})

    token = create_access_token(
        user_id=user["id"],
        role=user.get("role", "farmer"),
        login_id=user["login_id"],
        name=user.get("name", "Farmer")
    )

    clean_user = clean_doc(user)
    clean_user.pop("password_hash", None)

    return {
        "status": "success",
        "token": token,
        "user": clean_user
    }

@app.get("/api/auth/me", tags=["Auth"])
def get_profile(current_user: dict = Depends(get_current_user)):
    """Validates saved token and returns user profile."""
    return current_user

# -------------------------------------------------------------
# ADVISORY & KNOWLEDGE BASE ROUTES (Section 5.1 & 5.2)
# -------------------------------------------------------------

@app.get("/api/advisory", tags=["Advisory"])
def get_all_advisory(
    crop_id: Optional[int] = Query(None, description="Filter by crop ID (e.g. 6 for Tomato)"),
    class_key: Optional[str] = Query(None, description="Filter by exact model class key")
):
    """
    Returns full multilingual disease and pest knowledge documents.
    Used to build the offline advisory.json bundle and for live refreshes when online.
    """
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = {}
        if crop_id is not None:
            query["crop_id"] = crop_id
        if class_key:
            query["class_key"] = class_key

        docs = list(db.disease_info.find(query, {"_id": 0}))
        return [clean_doc(d) for d in docs]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# SCANS & FIELD REPORTS SYNC (Section 5.2 & 5.5)
# -------------------------------------------------------------

@app.post("/api/scans/sync", tags=["Scans"])
def sync_scans(
    payload: SyncScansRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Accepts a batch of scans from the mobile app's outbox.
    Idempotent: uses client_uuid so retried uploads never create duplicates.
    Accepts anonymous guest scans (user_id = null) and authenticated scans (user_id from token).
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    synced_count = 0

    for scan in payload.scans:
        scan_dict = scan.dict()
        client_uuid = scan_dict.get("client_uuid")
        if not client_uuid:
            continue

        # If user is logged in, attach their user_id securely from the JWT token
        if current_user and current_user.get("id"):
            scan_dict["user_id"] = current_user["id"]
        elif scan_dict.get("user_id"):
            pass
        elif "user_id" not in scan_dict:
            scan_dict["user_id"] = None

        if not scan_dict.get("scanned_at"):
            scan_dict["scanned_at"] = now_str
        scan_dict["synced_at"] = now_str

        # Upsert by client_uuid
        db.scans.update_one(
            {"client_uuid": client_uuid},
            {
                "$set": scan_dict,
                "$setOnInsert": {"created_in_db": now_str}
            },
            upsert=True
        )
        synced_count += 1

    return {
        "status": "success",
        "synced_count": synced_count,
        "total_received": len(payload.scans),
        "message": f"Successfully processed {synced_count} scan(s)."
    }

@app.get("/api/scans/mine", tags=["Scans"])
def get_my_scans(current_user: dict = Depends(get_current_user)):
    """
    Returns the signed-in user's own scan history with disease knowledge details.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = current_user["id"]
    scans = list(db.scans.find({"user_id": user_id}, {"_id": 0}).sort("scanned_at", -1))

    # Enrich scans with disease title and severity
    disease_cache = {d["class_key"]: d for d in db.disease_info.find({}, {"_id": 0})}
    enriched = []
    for s in scans:
        cleaned = clean_doc(s)
        ck = cleaned.get("class_key")
        if ck in disease_cache:
            d_info = disease_cache[ck]
            cleaned["disease_name"] = d_info.get("name", {}).get("en", ck)
            cleaned["severity"] = d_info.get("severity", "medium")
            cleaned["kind"] = d_info.get("kind", "Disease")
            cleaned["recommended_technical_names"] = d_info.get("recommended_technical_names", [])
        enriched.append(cleaned)

    return enriched

@app.get("/api/scans/stats", tags=["Scans"])
def get_scans_stats(officer: dict = Depends(require_role(["officer"]))):
    """
    Aggregated outbreak analytics for the Field Reports dashboard. Restricted to Officers.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    total_scans = db.scans.count_documents({})

    # Aggregate by class_key
    disease_pipeline = [
        {"$group": {"_id": "$class_key", "count": {"$sum": 1}, "avg_confidence": {"$avg": "$confidence"}}},
        {"$sort": {"count": -1}}
    ]
    disease_counts = list(db.scans.aggregate(disease_pipeline))

    # Disease info mapping
    disease_map = {d["class_key"]: d for d in db.disease_info.find({}, {"_id": 0})}
    crops_map = {c["id"]: c["crop_name"] for c in db.master_crops.find({}, {"id": 1, "crop_name": 1, "_id": 0})}

    by_disease = []
    for dc in disease_counts:
        ck = dc["_id"]
        info = disease_map.get(ck, {})
        by_disease.append({
            "class_key": ck,
            "disease_name": info.get("name", {}).get("en", ck),
            "crop_id": info.get("crop_id"),
            "crop_name": crops_map.get(info.get("crop_id"), "General"),
            "kind": info.get("kind", "Disease"),
            "severity": info.get("severity", "medium"),
            "count": dc["count"],
            "avg_confidence": round(dc.get("avg_confidence") or 0.0, 1)
        })

    # Aggregate by crop
    crop_pipeline = [
        {"$match": {"crop_id": {"$ne": None, "$gt": 0}}},
        {"$group": {"_id": "$crop_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    crop_counts = list(db.scans.aggregate(crop_pipeline))
    by_crop = [
        {
            "crop_id": cc["_id"],
            "crop_name": crops_map.get(cc["_id"], f"Crop {cc['_id']}"),
            "count": cc["count"]
        }
        for cc in crop_counts
    ]

    # Recent field scans
    recent = list(db.scans.find({}, {"_id": 0}).sort("scanned_at", -1).limit(20))
    cleaned_recent = []
    for r in recent:
        item = clean_doc(r)
        ck = item.get("class_key")
        info = disease_map.get(ck, {})
        item["disease_name"] = info.get("name", {}).get("en", ck)
        item["severity"] = info.get("severity", "medium")
        cleaned_recent.append(item)

    return {
        "total_scans": total_scans,
        "by_disease": by_disease,
        "by_crop": by_crop,
        "recent_scans": cleaned_recent,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# -------------------------------------------------------------
# CROPS & CROP DETAILS (Section 3 & 5)
# -------------------------------------------------------------

@app.get("/api/crops", tags=["Crops"])
def get_crops():
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        coll = db.master_crops if db.master_crops.count_documents({}) > 0 else db.crops
        results = list(coll.find({}, {"_id": 0}))
        return [clean_doc(r) for r in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crops/{crop_id}", tags=["Crops"])
def get_crop_detail(crop_id: int):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        coll = db.master_crops if db.master_crops.count_documents({}) > 0 else db.crops
        crop = coll.find_one({"id": crop_id}, {"_id": 0})
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")

        # Attach common diseases for this crop
        diseases = list(db.disease_info.find({"crop_id": crop_id}, {"_id": 0}))
        crop_data = clean_doc(crop)
        crop_data["diseases"] = [clean_doc(d) for d in diseases]
        return crop_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# INPUT PRODUCTS & COMPARISON
# -------------------------------------------------------------

@app.get("/api/products", tags=["Products"])
def get_products(category: Optional[str] = None, brand: Optional[str] = None):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
            
        coll = db.input_products if db.input_products.count_documents({}) > 0 else db.products
        match_conditions = {}
        if category:
            match_conditions["category"] = category
        if brand:
            match_conditions["brand_name"] = brand

        results = list(coll.find(match_conditions, {"_id": 0}))
        return [clean_doc(r) for r in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compare", tags=["Intelligence"])
def compare_products(technical_name: str):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
            
        coll = db.input_products if db.input_products.count_documents({}) > 0 else db.products
        
        # Regex search for technical name
        pipeline = [
            {
                "$match": {
                    "technical_name": {"$regex": f"^{re.escape(technical_name.strip())}$", "$options": "i"}
                }
            },
            {
                "$addFields": {
                    "price_per_unit": {
                        "$cond": [
                            {"$and": [{"$ne": ["$unit_value", None]}, {"$gt": ["$unit_value", 0]}]},
                            {"$divide": ["$price", "$unit_value"]},
                            "$price"
                        ]
                    }
                }
            },
            {
                "$sort": {"price_per_unit": 1}
            },
            {
                "$project": {"_id": 0}
            }
        ]
        results = list(coll.aggregate(pipeline))
        return [clean_doc(r) for r in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# MANDI RATES & MARKET PULSE
# -------------------------------------------------------------

DEFAULT_MANDI_BENCHMARKS = {
    "Wheat": [
        {"state": "Punjab", "district": "Ludhiana", "mandi_name": "Khanna Mandi", "modal_price": 2275.0, "min_price": 2250.0, "max_price": 2320.0},
        {"state": "Haryana", "district": "Karnal", "mandi_name": "Karnal Mandi", "modal_price": 2290.0, "min_price": 2260.0, "max_price": 2340.0},
        {"state": "Madhya Pradesh", "district": "Indore", "mandi_name": "Indore Mandi", "modal_price": 2420.0, "min_price": 2380.0, "max_price": 2490.0},
        {"state": "Gujarat", "district": "Rajkot", "mandi_name": "Rajkot APMC", "modal_price": 2510.0, "min_price": 2450.0, "max_price": 2580.0},
        {"state": "Rajasthan", "district": "Kota", "mandi_name": "Kota Mandi", "modal_price": 2350.0, "min_price": 2310.0, "max_price": 2400.0},
    ],
    "Rice": [
        {"state": "Haryana", "district": "Karnal", "mandi_name": "Taraori Mandi", "modal_price": 3850.0, "min_price": 3700.0, "max_price": 4050.0},
        {"state": "Punjab", "district": "Amritsar", "mandi_name": "Amritsar APMC", "modal_price": 3920.0, "min_price": 3780.0, "max_price": 4100.0},
        {"state": "Andhra Pradesh", "district": "Krishna", "mandi_name": "Vijayawada Mandi", "modal_price": 2450.0, "min_price": 2400.0, "max_price": 2550.0},
    ],
    "Cotton": [
        {"state": "Gujarat", "district": "Rajkot", "mandi_name": "Rajkot APMC", "modal_price": 7250.0, "min_price": 7000.0, "max_price": 7500.0},
        {"state": "Maharashtra", "district": "Amravati", "mandi_name": "Amravati Mandi", "modal_price": 7180.0, "min_price": 6950.0, "max_price": 7400.0},
        {"state": "Telangana", "district": "Warangal", "mandi_name": "Warangal APMC", "modal_price": 7320.0, "min_price": 7100.0, "max_price": 7550.0},
    ],
    "Maize": [
        {"state": "Karnataka", "district": "Davangere", "mandi_name": "Davangere APMC", "modal_price": 2150.0, "min_price": 2080.0, "max_price": 2240.0},
        {"state": "Madhya Pradesh", "district": "Chhindwara", "mandi_name": "Chhindwara Mandi", "modal_price": 2100.0, "min_price": 2020.0, "max_price": 2190.0},
    ],
    "Potato": [
        {"state": "Uttar Pradesh", "district": "Agra", "mandi_name": "Agra Mandi", "modal_price": 1450.0, "min_price": 1380.0, "max_price": 1550.0},
        {"state": "Gujarat", "district": "Banaskantha", "mandi_name": "Deesa Mandi", "modal_price": 1600.0, "min_price": 1500.0, "max_price": 1720.0},
    ],
    "Tomato": [
        {"state": "Karnataka", "district": "Kolar", "mandi_name": "Kolar APMC", "modal_price": 1850.0, "min_price": 1600.0, "max_price": 2100.0},
        {"state": "Maharashtra", "district": "Nashik", "mandi_name": "Nashik Mandi", "modal_price": 1920.0, "min_price": 1750.0, "max_price": 2150.0},
    ]
}

@app.get("/api/mandi/{crop_id}", tags=["Mandi"])
def get_mandi_rates(
    crop_id: int, 
    state: Optional[str] = None, 
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        db = get_db()
        filter_query = {"crop_id": crop_id}
        if state:
            filter_query["state"] = {"$regex": f"^{state.strip()}$", "$options": "i"}
        if district:
            filter_query["district"] = {"$regex": f"^{district.strip()}$", "$options": "i"}
        if start_date and end_date:
            filter_query["price_date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            filter_query["price_date"] = {"$gte": start_date}
        elif end_date:
            filter_query["price_date"] = {"$lte": end_date}

        results = []
        if db is not None:
            results = list(db.mandi_prices.find(filter_query, {"_id": 0}).sort("price_date", -1).limit(100))

        if not results:
            crop_name = ""
            if db is not None:
                c_coll = db.master_crops if db.master_crops.count_documents({}) > 0 else db.crops
                c_doc = c_coll.find_one({"id": crop_id})
                if c_doc:
                    crop_name = c_doc.get("crop_name", "")

            benchmarks = DEFAULT_MANDI_BENCHMARKS.get(crop_name, [])
            today_str = date.today().strftime("%Y-%m-%d")
            results = [
                {
                    "crop_id": crop_id,
                    "state": b["state"],
                    "district": b["district"],
                    "mandi_name": b["mandi_name"],
                    "modal_price": b["modal_price"],
                    "min_price": b["min_price"],
                    "max_price": b["max_price"],
                    "price_date": today_str,
                    "is_benchmark": True
                }
                for b in benchmarks
            ]

        return [clean_doc(r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/advisories/{crop_id}", tags=["Intelligence"])
def get_crop_advisories(crop_id: int):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        coll = db.crop_advisories if db.crop_advisories.count_documents({}) > 0 else db.advisories
        results = list(coll.find({"crop_id": crop_id}, {"_id": 0}))
        return [clean_doc(r) for r in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-pulse", tags=["Intelligence"])
def get_market_pulse():
    try:
        db = get_db()
        if db is not None:
            pipeline = [
                {"$match": {"modal_price": {"$gt": 0}}},
                {"$group": {"_id": "$crop_id", "current_price": {"$avg": "$modal_price"}}},
                {
                    "$lookup": {
                        "from": "master_crops",
                        "localField": "_id",
                        "foreignField": "id",
                        "as": "crop"
                    }
                },
                {"$unwind": {"path": "$crop", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": 0,
                        "crop_id": "$_id",
                        "crop_name": {"$ifNull": ["$crop.crop_name", "Crop"]},
                        "category": {"$ifNull": ["$crop.category", "Grain"]},
                        "current_price": 1
                    }
                },
                {"$sort": {"current_price": -1}}
            ]
            db_pulse = list(db.mandi_prices.aggregate(pipeline))
            
            if db_pulse and len(db_pulse) >= 2:
                gainers = []
                losers = []
                for idx, item in enumerate(db_pulse):
                    price = float(item["current_price"])
                    if idx < 4:
                        gainers.append({
                            "id": idx + 1,
                            "crop_name": item["crop_name"],
                            "category": item.get("category") or "Grain",
                            "current_price": round(price, 2),
                            "previous_price": round(price * 0.97, 2),
                            "pct_change": 3.1
                        })
                    else:
                        losers.append({
                            "id": idx + 1,
                            "crop_name": item["crop_name"],
                            "category": item.get("category") or "Commercial",
                            "current_price": round(price, 2),
                            "previous_price": round(price * 1.02, 2),
                            "pct_change": -1.8
                        })
                return {"gainers": gainers, "losers": losers[:4]}

        return {
            "gainers": [
                {"id": 1, "crop_name": "Wheat", "category": "Cereal", "current_price": 2420.0, "previous_price": 2350.0, "pct_change": 2.98},
                {"id": 2, "crop_name": "Cotton", "category": "Cash Crop", "current_price": 7250.0, "previous_price": 7050.0, "pct_change": 2.84},
                {"id": 3, "crop_name": "Mustard", "category": "Oilseed", "current_price": 5450.0, "previous_price": 5350.0, "pct_change": 1.87}
            ],
            "losers": [
                {"id": 4, "crop_name": "Potato", "category": "Vegetable", "current_price": 1450.0, "previous_price": 1520.0, "pct_change": -4.61},
                {"id": 5, "crop_name": "Tomato", "category": "Vegetable", "current_price": 1850.0, "previous_price": 1920.0, "pct_change": -3.65}
            ]
        }
    except Exception as e:
        return {"gainers": [], "losers": []}

@app.post("/api/sync-government-data", tags=["Intelligence"])
@app.get("/api/sync-government-data", tags=["Intelligence"])
def sync_government_api():
    try:
        api_client = GovernmentAPIClient()
        is_online, msg = api_client.check_health(timeout=3)
        AUTO_SYNC_STATE["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        AUTO_SYNC_STATE["is_online"] = is_online
        AUTO_SYNC_STATE["probe_message"] = msg

        if not is_online:
            AUTO_SYNC_STATE["status"] = "OFFLINE"
            return {
                "status": "offline",
                "records_synced": 0,
                "message": f"Government API is currently offline ({msg}). System is safely serving local MongoDB records.",
                "last_checked": AUTO_SYNC_STATE["last_checked"]
            }

        count = api_client.sync_market_prices()
        AUTO_SYNC_STATE["status"] = "ONLINE"
        AUTO_SYNC_STATE["last_successful_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        AUTO_SYNC_STATE["records_synced_last_run"] = count
        AUTO_SYNC_STATE["total_records_synced"] += count
        return {
            "status": "success",
            "records_synced": count,
            "message": f"Successfully synced {count} records from Government API into MongoDB."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/companies", tags=["Directory"])
def get_companies():
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        results = list(db.companies.find({}, {"_id": 0}))
        return [clean_doc(r) for r in results]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
