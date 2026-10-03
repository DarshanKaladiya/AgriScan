import os
import requests
from dotenv import load_dotenv
from db_utils import get_connection
import time
from datetime import datetime

load_dotenv()

class GovernmentAPIClient:
    def __init__(self):
        self.api_key = os.getenv("DATA_GOV_API_KEY")
        self.base_url = "https://api.data.gov.in/resource/"
        
        # AGMARKNET_RESOURCE_ID contains all commodity mandi prices
        # COMMODITY_RESOURCE_ID is specific commodity (e.g., Cotton)
        self.resources = {
            "market_price": os.getenv("AGMARKNET_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070"),
            "commodity_price": os.getenv("COMMODITY_RESOURCE_ID", "35985678-0d79-46b4-9ed6-6f13308a1d24")
        }

    def check_health(self, timeout=3):
        """
        Lightweight health check probe to test if api.data.gov.in is reachable.
        Returns tuple: (is_online: bool, message: str)
        """
        if not self.api_key:
            return False, "DATA_GOV_API_KEY not configured in .env"
        
        res_id = self.resources.get("market_price", "9ef84268-d588-465a-a308-a864a43d0070")
        url = f"{self.base_url}{res_id}?api-key={self.api_key}&format=json&limit=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgriIntelligence/1.0",
            "Accept": "application/json"
        }
        try:
            start_t = time.time()
            resp = requests.get(url, headers=headers, timeout=timeout)
            duration = round((time.time() - start_t) * 1000, 2)
            if resp.status_code == 200:
                return True, f"Online (latency {duration}ms)"
            elif resp.status_code in [502, 503, 504]:
                return False, f"Server Busy / Unavailable (HTTP {resp.status_code})"
            else:
                return False, f"HTTP Error {resp.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused / Government server offline"
        except requests.exceptions.Timeout:
            return False, f"Timeout after {timeout}s"
        except Exception as e:
            return False, str(e)

    def get_data(self, resource_type="market_price", limit=100, date_filter=None, commodity_filter=None, retries=1, delay=2, timeout=6):
        """
        Fetches records from data.gov.in with quick timeout to prevent server freeze
        when the government server is experiencing downtime.
        """
        if not self.api_key:
            print("[GovernmentAPIClient] DATA_GOV_API_KEY not configured in .env")
            return None
            
        res_id = self.resources.get(resource_type) or self.resources["market_price"]
        if not res_id:
            print(f"[GovernmentAPIClient] Resource ID for {resource_type} not found")
            return None

        url = f"{self.base_url}{res_id}?api-key={self.api_key}&format=json&limit={limit}"
        if date_filter:
            url += f"&filters[arrival_date]={date_filter}"
        if commodity_filter:
            url += f"&filters[commodity]={commodity_filter}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgriIntelligence/1.0",
            "Accept": "application/json"
        }

        print(f"[GovernmentAPIClient] Fetching {resource_type} (Resource: {res_id}, Commodity: {commodity_filter or 'All'}, Date: {date_filter or 'Latest'})...")
        
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [502, 503, 504]:
                    print(f"[GovernmentAPIClient] Server busy ({response.status_code}).")
                    if attempt < retries:
                        time.sleep(delay)
                else:
                    print(f"[GovernmentAPIClient] HTTP Error: {response.status_code} - {response.text[:200]}")
                    return None
            except requests.exceptions.ConnectionError:
                print("[GovernmentAPIClient] Connection to api.data.gov.in refused or server offline.")
                return None
            except requests.exceptions.Timeout:
                print(f"[GovernmentAPIClient] Request timed out ({timeout}s).")
                return None
            except Exception as e:
                print(f"[GovernmentAPIClient] Request failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    return None
        return None

    def sync_market_prices(self, date_filter=None):
        """
        Sync real-time market prices from data.gov.in into MongoDB mandi_prices collection.
        Falls back to local sync if external API is unreachable.
        """
        # Always prioritize market_price (Agmarknet all commodities)
        data = self.get_data("market_price", limit=500, date_filter=date_filter, timeout=8)
        
        db = get_connection()
        if db is None:
            print("[GovernmentAPIClient] Database connection unavailable for sync.")
            return 0
        
        # Fetch crop mappings from MongoDB master_crops collection
        crop_coll = db.master_crops if db.master_crops.count_documents({}) > 0 else db.crops
        crop_rows = list(crop_coll.find({}, {"id": 1, "crop_name": 1, "_id": 0}))
        crop_map = {c["crop_name"].lower(): c["id"] for c in crop_rows if "crop_name" in c and "id" in c}
        
        count = 0
        if data and "records" in data and len(data["records"]) > 0:
            records = data["records"]
            for r in records:
                try:
                    state = r.get("state") or r.get("State") or "National"
                    district = r.get("district") or r.get("District") or state
                    mandi = r.get("market") or r.get("Market") or "Agmarknet Mandi"
                    commodity = (r.get("commodity") or r.get("Commodity") or "").strip()
                    p_mod_raw = r.get("modal_price") or r.get("Modal_Price") or 0
                    p_min_raw = r.get("min_price") or r.get("Min_Price") or p_mod_raw
                    p_max_raw = r.get("max_price") or r.get("Max_Price") or p_mod_raw
                    p_date_raw = r.get("arrival_date") or r.get("Arrival_Date") or ""
                    
                    if not commodity:
                        continue
                    
                    commodity_lower = commodity.lower()
                    crop_id = None
                    for cname, cid in crop_map.items():
                        if cname in commodity_lower or commodity_lower in cname:
                            crop_id = cid
                            break
                    
                    if not crop_id:
                        continue

                    try:
                        p_date_str = datetime.strptime(p_date_raw.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                    except Exception:
                        p_date_str = datetime.now().strftime("%Y-%m-%d")
                    
                    db.mandi_prices.update_one(
                        {"crop_id": crop_id, "mandi_name": mandi, "price_date": p_date_str},
                        {
                            "$set": {
                                "crop_id": crop_id,
                                "state": state,
                                "district": district,
                                "mandi_name": mandi,
                                "min_price": float(p_min_raw),
                                "max_price": float(p_max_raw),
                                "modal_price": float(p_mod_raw),
                                "price_date": p_date_str
                            }
                        },
                        upsert=True
                    )
                    count += 1
                except Exception as e:
                    print(f"[GovernmentAPIClient] Sync record parse error: {e}")
            print(f"[GovernmentAPIClient] Successfully synced {count} market price records from Government API into MongoDB.")
        else:
            print("[GovernmentAPIClient] Government API returned no records or was offline.")
        
        return count

    def sync_commodity_prices(self):
        """Alias for sync_market_prices"""
        return self.sync_market_prices()
