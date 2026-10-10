import os
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
    scans = []
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{API_URL}/scans/mine", headers=headers, timeout=5)
        if res.status_code == 200:
            scans = res.json()
        elif res.status_code == 401:
            request.session.flush()
            messages.warning(request, "Your session has expired. Please log in again.")
            return redirect("login")
    except Exception as e:
        messages.error(request, "Unable to load scan history at this time.")

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
