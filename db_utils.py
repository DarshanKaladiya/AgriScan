import os
from pymongo import MongoClient, ReturnDocument
from dotenv import load_dotenv
from datetime import date, datetime
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agri_intelligence")

_client = None

def get_mongo_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client

def db_is_up() -> bool:
    """Quick boolean check if MongoDB is alive and responsive."""
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return True
    except Exception:
        return False

def get_db(db_name=None):
    """Returns the MongoDB database instance if connected, else None."""
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return client[db_name or MONGO_DB_NAME]
    except Exception as err:
        print(f"[db_utils] MongoDB Connection Error: {err}")
        return None

def get_connection(db_name=None):
    """Backwards-compatible alias for get_db."""
    return get_db(db_name)

def next_id(sequence_name: str) -> int:
    """
    Atomic counter generator for collections requiring numeric IDs 
    (e.g., users, master_crops, input_products) for clean URLs and compatibility.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database connection unavailable for next_id generation.")
    result = db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result["seq"]

def clean_doc(doc: dict, keep_mongo_id: bool = False) -> dict:
    """Format MongoDB document: stringify ObjectId, format datetime objects."""
    if not doc:
        return doc
    cleaned = {}
    for k, v in doc.items():
        if k == "_id":
            if keep_mongo_id:
                cleaned["_id"] = str(v)
            continue
        elif isinstance(v, ObjectId):
            cleaned[k] = str(v)
        elif isinstance(v, (datetime, date)):
            cleaned[k] = v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v.strftime("%Y-%m-%d")
        elif isinstance(v, dict):
            cleaned[k] = clean_doc(v, keep_mongo_id)
        elif isinstance(v, list):
            cleaned[k] = [clean_doc(item, keep_mongo_id) if isinstance(item, dict) else item for item in v]
        else:
            cleaned[k] = v
    return cleaned

def init_db():
    """Initializes MongoDB database and creates all required indexes for AgriScan."""
    db = get_db()
    if db is None:
        print("[db_utils] Could not connect to MongoDB server.")
        print("[db_utils] Please ensure MongoDB is running on port 27017.")
        return False

    print("[db_utils] Initializing MongoDB indexes for AgriScan collections...")
    try:
        # Master Crops
        db.master_crops.create_index("id", unique=True)
        db.master_crops.create_index("crop_name", unique=True)

        # Companies
        db.companies.create_index("id", unique=True)
        db.companies.create_index("name", unique=True)

        # Input Products
        db.input_products.create_index("id", unique=True)
        db.input_products.create_index([("category", 1), ("brand_id", 1)])
        db.input_products.create_index("technical_name")

        # Crop Advisories
        db.crop_advisories.create_index("id", unique=True)
        db.crop_advisories.create_index("crop_id")

        # Mandi Prices
        db.mandi_prices.create_index([("mandi_name", 1), ("crop_id", 1), ("price_date", 1)], unique=True)
        db.mandi_prices.create_index([("crop_id", 1), ("price_date", -1)])

        # Users
        db.users.create_index("login_id", unique=True)
        db.users.create_index("id", unique=True)
        db.users.create_index("role")

        # Scans (Uploaded leaf diagnoses)
        db.scans.create_index("client_uuid", unique=True)
        db.scans.create_index("user_id")
        db.scans.create_index("device_id")
        db.scans.create_index("class_key")
        db.scans.create_index("scanned_at")

        # Disease Knowledge Info
        db.disease_info.create_index("class_key", unique=True)
        db.disease_info.create_index("crop_id")
        db.disease_info.create_index("kind")

        print("[db_utils] AgriScan MongoDB indexes verified successfully!")
        return True
    except Exception as err:
        print(f"[db_utils] Error creating indexes: {err}")
        return False

if __name__ == "__main__":
    init_db()
