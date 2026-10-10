import os
import json
import uuid
from datetime import datetime
from functools import wraps
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/api")

# -------------------------------------------------------------
# AUTHENTICATION DECORATORS
# -------------------------------------------------------------

def login_required(view_func):
    """Ensures user has an active session token before opening the view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("token") or not request.session.get("user"):
            messages.info(request, "Please log in to access your personal AgriScan dashboard.")
            return redirect(f"/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper

def officer_required(view_func):
    """Restricts access to Agricultural Officers and Researchers."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.session.get("user")
        if not user:
            messages.info(request, "Officer login required to access Field Reports.")
            return redirect(f"/login/?next={request.path}")
        if user.get("role") != "officer":
            return render(request, "403.html", {
                "message": "Access Denied: Field Outbreak Reports are restricted to Agricultural Officers and Researchers."
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

# -------------------------------------------------------------
# CORE PAGES
# -------------------------------------------------------------

def dashboard(request):
    """
    AgriScan Main Landing & Intelligence Hub:
    Highlights offline AI disease detection, crop guide, live mandi pulse, and field alerts.
    """
    crops_count = 0
    mandi_count = 0
    products_count = 0
    gainers = []
    losers = []
    total_scans = 0
    recent_detections = []

    try:
        # High-level stats
        crops_res = requests.get(f"{API_URL}/crops", timeout=4)
        if crops_res.status_code == 200:
            crops_data = crops_res.json()
            crops_count = len(crops_data)

        prod_res = requests.get(f"{API_URL}/products", timeout=4)
        if prod_res.status_code == 200:
            products_count = len(prod_res.json())

        mandi_res = requests.get(f"{API_URL}/mandi/1", timeout=4)
        if mandi_res.status_code == 200:
            mandi_count = len(mandi_res.json())

        pulse_res = requests.get(f"{API_URL}/market-pulse", timeout=4)
        if pulse_res.status_code == 200:
            pulse_data = pulse_res.json()
            gainers = pulse_data.get("gainers", [])
            losers = pulse_data.get("losers", [])

        # Public summary from advisory
        adv_res = requests.get(f"{API_URL}/advisory", timeout=4)
        disease_count = len(adv_res.json()) if adv_res.status_code == 200 else 17
    except Exception:
        disease_count = 17

    return render(request, 'dashboard.html', {
        'crops_count': crops_count or 272,
        'products_count': products_count or 64,
        'mandi_count': mandi_count or 11527,
        'disease_count': disease_count,
        'gainers': gainers,
        'losers': losers,
        'user': request.session.get("user")
    })

def crops_list(request):
    try:
        response = requests.get(f"{API_URL}/crops", timeout=4)
        crops = response.json() if response.status_code == 200 else []
    except Exception:
        crops = []
    return render(request, 'crops_list.html', {
        'crops': crops,
        'user': request.session.get("user")
    })

def crop_detail(request, crop_id):
    try:
        # Fetch Crop Metadata and Common Diseases from upgraded API
        crop_res = requests.get(f"{API_URL}/crops/{crop_id}", timeout=4)
        crop = crop_res.json() if crop_res.status_code == 200 else None

        # Fetch Advisories
        adv_res = requests.get(f"{API_URL}/advisories/{crop_id}", timeout=4)
        advisories = adv_res.json() if adv_res.status_code == 200 else []

        # Fetch Mandi Stats for context
        mandi_res = requests.get(f"{API_URL}/mandi/{crop_id}", timeout=4)
        mandi_data = mandi_res.json() if mandi_res.status_code == 200 else []
    except Exception:
        crop = None
        advisories = []
        mandi_data = []

    if not crop:
        return render(request, '404.html', status=404)

    return render(request, 'crop_detail.html', {
        'crop': crop,
        'advisories': advisories,
        'mandi_data': mandi_data[:10],
        'diseases': crop.get("diseases", []),
        'user': request.session.get("user")
    })

def compare_products(request):
    tech_name = request.GET.get('technical', 'Mancozeb 75% WP')
    try:
        response = requests.get(f"{API_URL}/compare", params={'technical_name': tech_name}, timeout=4)
        products = response.json() if response.status_code == 200 else []
    except Exception:
        products = []
    return render(request, 'compare.html', {
        'products': products,
        'tech_name': tech_name,
        'user': request.session.get("user")
    })

def mandi_rates(request):
    crop_id = request.GET.get('crop_id', 1)
    state = request.GET.get('state', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    try:
        crops_res = requests.get(f"{API_URL}/crops", timeout=4)
        crops = crops_res.json() if crops_res.status_code == 200 else []

        params = {'state': state, 'start_date': start_date, 'end_date': end_date}
        response = requests.get(f"{API_URL}/mandi/{crop_id}", params=params, timeout=4)
        rates = response.json() if response.status_code == 200 else []

        selected_crop = next((c for c in crops if str(c.get('id')) == str(crop_id)), None)

        best_mandi = None
        worst_mandi = None
        if rates:
            valid_rates = [r for r in rates if r.get("modal_price", 0) > 0]
            if valid_rates:
                best_mandi = max(valid_rates, key=lambda x: x["modal_price"])
                worst_mandi = min(valid_rates, key=lambda x: x["modal_price"])
    except Exception:
        crops = []
        rates = []
        selected_crop = None
        best_mandi = None
        worst_mandi = None

    return render(request, 'mandi_rates.html', {
        'rates': rates,
        'crops': crops,
        'selected_crop': selected_crop,
        'start_date': start_date,
        'end_date': end_date,
        'best_mandi': best_mandi,
        'worst_mandi': worst_mandi,
        'user': request.session.get("user")
    })

def partners_list(request):
    try:
        response = requests.get(f"{API_URL}/companies", timeout=4)
        companies = response.json() if response.status_code == 200 else []
    except Exception:
        companies = []
    return render(request, 'companies_list.html', {
        'companies': companies,
        'user': request.session.get("user")
    })

# -------------------------------------------------------------
# AUTHENTICATION VIEWS (Section 5.6 & 5.7)
# -------------------------------------------------------------

def login_view(request):
    """Farmer and Officer web login."""
    if request.session.get("token") and request.session.get("user"):
        return redirect("dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        login_id = request.POST.get("login_id", "").strip()
        password = request.POST.get("password", "")

        try:
            res = requests.post(f"{API_URL}/auth/login", json={
                "login_id": login_id,
                "password": password
            }, timeout=5)

            if res.status_code == 200:
                data = res.json()
                request.session["token"] = data["token"]
                request.session["user"] = data["user"]
                messages.success(request, f"Welcome back, {data['user']['name']}!")

                if next_url and next_url.startswith("/"):
                    return redirect(next_url)
                if data["user"].get("role") == "officer":
                    return redirect("field_reports")
                return redirect("my_scans")
            else:
                err_msg = res.json().get("detail", "Invalid mobile number/email or password.")
                messages.error(request, err_msg)
        except requests.exceptions.RequestException:
            messages.error(request, "Authentication service is temporarily unavailable. Please try again.")

    return render(request, 'login.html', {
        'next': next_url,
        'user': None
    })

def signup_view(request):
    """Farmer account registration."""
    if request.session.get("token") and request.session.get("user"):
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        login_id = request.POST.get("login_id", "").strip()
        password = request.POST.get("password", "")
        preferred_language = request.POST.get("preferred_language", "en")

        try:
            res = requests.post(f"{API_URL}/auth/register", json={
                "name": name,
                "login_id": login_id,
                "password": password,
                "preferred_language": preferred_language
            }, timeout=5)

            if res.status_code == 200:
                data = res.json()
                request.session["token"] = data["token"]
                request.session["user"] = data["user"]
                messages.success(request, "Account created successfully! Welcome to AgriScan.")
                return redirect("my_scans")
            else:
                err_msg = res.json().get("detail", "Registration failed. Please check your information.")
                messages.error(request, err_msg)
        except requests.exceptions.RequestException:
            messages.error(request, "Registration service is temporarily unavailable. Please try again.")

    return render(request, 'signup.html', {
        'user': None
    })

def logout_view(request):
    """Clears Django session and logs user out."""
    request.session.flush()
    messages.info(request, "You have been safely logged out.")
    return redirect("dashboard")

# -------------------------------------------------------------
# PROTECTED USER & OFFICER VIEWS
# -------------------------------------------------------------

@login_required
def my_scans(request):
    """Personal scan history for the signed-in farmer."""
    token = request.session.get("token")
    user = request.session.get("user") or {}
    user_id = user.get("id")
    scans = []
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        res = requests.get(f"{API_URL}/scans/mine", headers=headers, timeout=5)
        if res.status_code == 200:
            scans = res.json()
        elif res.status_code == 401:
            request.session.flush()
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect("login")
    except Exception as e:
        pass

    # Reliable MongoDB fallback if scans is empty or API call had issues
    if not scans and user_id:
        try:
            db = get_db()
            if db is not None:
                db_scans = list(db.scans.find({"user_id": user_id}, {"_id": 0}).sort("scanned_at", -1))
                disease_cache = {d["class_key"]: d for d in db.disease_info.find({}, {"_id": 0})}
                for s in db_scans:
                    cleaned = clean_doc(s)
                    ck = cleaned.get("class_key")
                    if ck in disease_cache:
                        d_info = disease_cache[ck]
                        cleaned["disease_name"] = d_info.get("name", {}).get("en", ck)
                        cleaned["severity"] = d_info.get("severity", "moderate")
                        cleaned["treatment_summary"] = d_info.get("treatment", {}).get("en", "")
                    else:
                        parts = (ck or "Crop___Disease").split("___")
                        cleaned["disease_name"] = parts[1].replace("_", " ") if len(parts) > 1 else ck
                        cleaned["severity"] = "healthy" if "healthy" in (ck or "").lower() else "high" if cleaned.get("confidence", 0) > 85 else "moderate"
                    scans.append(cleaned)
        except Exception as err:
            print("MongoDB fallback error:", err)

    return render(request, 'my_scans.html', {
        'scans': scans,
        'user': request.session.get("user")
    })

@officer_required
def field_reports(request):
    """Outbreak analytics and regional surveillance dashboard for Agricultural Officers."""
    token = request.session.get("token")
    stats = {
        "total_scans": 0,
        "by_disease": [],
        "by_crop": [],
        "recent_scans": []
    }
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{API_URL}/scans/stats", headers=headers, timeout=5)
        if res.status_code == 200:
            stats = res.json()
    except Exception:
        messages.error(request, "Unable to load real-time field outbreak statistics.")

    return render(request, 'field_reports.html', {
        'stats': stats,
        'user': request.session.get("user")
    })

def scanner_view(request):
    """Redirects to personal scanner hub with login protection."""
    return redirect("my_scans")


def set_language(request):
    """
    Switches active interface language ('en', 'hi', 'gu').
    Saves in session and cookie, then redirects back to previous page.
    """
    lang = request.GET.get('lang') or request.POST.get('lang') or 'en'
    if lang not in ['en', 'hi', 'gu']:
        lang = 'en'
    
    request.session['lang'] = lang
    next_url = request.GET.get('next') or request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    
    if not next_url.startswith('/') and not next_url.startswith('http://127.0.0.1') and not next_url.startswith('http://localhost'):
        next_url = '/'
        
    response = redirect(next_url)
    response.set_cookie('agri_lang', lang, max_age=30*24*3600)
    return response


import uuid
from django.http import JsonResponse
from db_utils import get_db, clean_doc

@login_required
def save_scan_view(request):
    """
    Persists client-side AI diagnosis results directly into MongoDB and
    synchronizes with the backend so they appear immediately in Past Scans.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        class_key = data.get("class_key", "")
        confidence = float(data.get("confidence", 0.0))
        client_uuid = data.get("client_uuid") or f"scan_{uuid.uuid4().hex[:12]}"
        user = request.session.get("user") or {}
        user_id = user.get("id")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        crop_id = 1
        crop_name = "Crop"
        if "potato" in class_key.lower():
            crop_id = 10
            crop_name = "Potato"
        elif "tomato" in class_key.lower():
            crop_id = 11
            crop_name = "Tomato"
        elif "corn" in class_key.lower() or "maize" in class_key.lower():
            crop_id = 12
            crop_name = "Corn (Maize)"

        severity = "healthy" if "healthy" in class_key.lower() else ("high" if confidence > 85 else "medium")

        # 1. Direct MongoDB upsert via db_utils
        db = get_db()
        if db is not None:
            scan_doc = {
                "client_uuid": client_uuid,
                "user_id": user_id,
                "class_key": class_key,
                "crop_id": crop_id,
                "confidence": confidence,
                "severity": severity,
                "language": request.session.get("lang") or "en",
                "scanned_at": now_str,
                "synced_at": now_str,
                "location": {
                    "region": "Gujarat, India"
                }
            }
            db.scans.update_one(
                {"client_uuid": client_uuid},
                {"$set": scan_doc, "$setOnInsert": {"created_in_db": now_str}},
                upsert=True
            )

        # 2. Sync to FastAPI backend if active
        token = request.session.get("token")
        if token:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                requests.post(
                    f"{API_URL}/scans/sync",
                    json={
                        "scans": [{
                            "client_uuid": client_uuid,
                            "class_key": class_key,
                            "crop_id": crop_id,
                            "confidence": confidence,
                            "scanned_at": now_str,
                            "user_id": user_id
                        }]
                    },
                    headers=headers,
                    timeout=3
                )
            except Exception:
                pass

        return JsonResponse({
            "status": "success",
            "client_uuid": client_uuid,
            "class_key": class_key,
            "crop_name": crop_name,
            "confidence": confidence,
            "severity": severity,
            "scanned_at": now_str
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings

def scan_app_view(request):
    """
    Serves the standalone 100% offline AgriScan PWA Single-Page Application.
    Works seamlessly in browser, mobile viewport, and airplane mode via Service Worker.
    """
    index_file = settings.BASE_DIR / 'scan-app' / 'www' / 'index.html'
    if not index_file.exists():
        raise Http404("Offline scan-app not found")
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/html')

def scan_app_static(request, path):
    """
    Serves static assets (WASM binaries, ONNX model weights, JSON catalogues, CSS/JS)
    for the offline scan-app PWA with correct MIME types and Service Worker scoping.
    """
    file_path = settings.BASE_DIR / 'scan-app' / 'www' / path
    if not file_path.exists() or not file_path.is_file():
        raise Http404(f"Asset {path} not found")

    content_type, _ = mimetypes.guess_type(str(file_path))
    if path.endswith('.wasm'):
        content_type = 'application/wasm'
    elif path.endswith('.json'):
        content_type = 'application/json'
    elif path.endswith('.js'):
        content_type = 'application/javascript'
    elif path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.onnx') or path.endswith('.tflite'):
        content_type = 'application/octet-stream'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')
    if path == 'sw.js':
        response['Service-Worker-Allowed'] = '/scan-app/'
    response['Cache-Control'] = 'public, max-age=86400'
    return response

