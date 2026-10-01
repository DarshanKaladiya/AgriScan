from django.shortcuts import render
import requests

API_URL = "http://localhost:8000/api"

def dashboard(request):
    try:
        # Fetch high-level stats for the dashboard with safety timeouts
        crops_res = requests.get(f"{API_URL}/crops", timeout=4)
        crops_count = len(crops_res.json()) if crops_res.status_code == 200 else 0
        
        mandi_res = requests.get(f"{API_URL}/mandi/1", timeout=4) # Use Wheat as reference
        mandi_count = len(mandi_res.json()) if mandi_res.status_code == 200 else 0
        
        comp_res = requests.get(f"{API_URL}/companies", timeout=4)
        comp_count = len(comp_res.json()) if comp_res.status_code == 200 else 0

        # Fetch Market Pulse (Top Gainers/Losers)
        pulse_res = requests.get(f"{API_URL}/market-pulse", timeout=4)
        pulse_data = pulse_res.json() if pulse_res.status_code == 200 else {"gainers": [], "losers": []}
        gainers = pulse_data.get("gainers", [])
        losers = pulse_data.get("losers", [])
    except Exception:
        crops_count = mandi_count = comp_count = 0
        gainers = losers = []

    return render(request, 'dashboard.html', {
        'crops_count': crops_count,
        'mandi_count': mandi_count,
        'comp_count': comp_count,
        'gainers': gainers,
        'losers': losers
    })

def crops_list(request):
    try:
        response = requests.get(f"{API_URL}/crops", timeout=4)
        crops = response.json() if response.status_code == 200 else []
    except Exception:
        crops = []
    # Add a fallback for empty list/error
    return render(request, 'crops_list.html', {'crops': crops})

def crop_detail(request, crop_id):
    try:
        # Fetch Crop Metadata
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
        'mandi_data': mandi_data[:10] # Top 10 latest
    })

def compare_products(request):
    tech_name = request.GET.get('technical', 'Generic')
    try:
        response = requests.get(f"{API_URL}/compare", params={'technical_name': tech_name}, timeout=4)
        products = response.json() if response.status_code == 200 else []
    except Exception:
        products = []
    return render(request, 'compare.html', {'products': products, 'tech_name': tech_name})

def mandi_rates(request):
    crop_id = request.GET.get('crop_id', 1)
    state = request.GET.get('state', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    try:
        # Fetch all crops for the filter dropdown
        crops_res = requests.get(f"{API_URL}/crops", timeout=4)
        crops = crops_res.json() if crops_res.status_code == 200 else []
        
        # Fetch mandi rates for the selected crop with filters
        params = {'state': state, 'start_date': start_date, 'end_date': end_date}
        response = requests.get(f"{API_URL}/mandi/{crop_id}", params=params, timeout=4)
        rates = response.json() if response.status_code == 200 else []
        
        # Find selected crop name for UI
        selected_crop = next((c for c in crops if str(c['id']) == str(crop_id)), None)
        
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
        'worst_mandi': worst_mandi
    })

def partners_list(request):
    try:
        response = requests.get(f"{API_URL}/companies", timeout=4)
        companies = response.json() if response.status_code == 200 else []
    except Exception:
        companies = []
    return render(request, 'companies_list.html', {'companies': companies})
