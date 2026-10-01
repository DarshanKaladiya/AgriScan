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
        Sync real-time market prices from data.gov.in into MySQL mandi_prices table.
        Falls back to local sync if external API is unreachable.
        """
        # Always prioritize market_price (Agmarknet all commodities)
        data = self.get_data("market_price", limit=500, date_filter=date_filter, timeout=8)
        
        conn = get_connection()
        if not conn:
            print("[GovernmentAPIClient] Database connection unavailable for sync.")
            return 0
        cursor = conn.cursor()
        
        # Fetch crop mappings
        cursor.execute("SELECT id, crop_name FROM master_crops")
        crop_rows = cursor.fetchall()
        crop_map = {row[1].lower(): row[0] for row in crop_rows}
        
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
                        p_date = datetime.strptime(p_date_raw.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                    except Exception:
                        p_date = datetime.now().strftime("%Y-%m-%d")
                    
                    sql = """INSERT INTO mandi_prices (crop_id, state, district, mandi_name, min_price, max_price, modal_price, price_date) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                             ON DUPLICATE KEY UPDATE 
                                modal_price=VALUES(modal_price),
                                min_price=VALUES(min_price),
                                max_price=VALUES(max_price)"""
                    cursor.execute(sql, (crop_id, state, district, mandi, float(p_min_raw), float(p_max_raw), float(p_mod_raw), p_date))
                    count += 1
                except Exception as e:
                    print(f"[GovernmentAPIClient] Sync record parse error: {e}")
            conn.commit()
            print(f"[GovernmentAPIClient] Successfully synced {count} market price records from Government API.")
        else:
            print("[GovernmentAPIClient] Government API returned no records or was offline.")
        
        cursor.close()
        conn.close()
        return count

    def sync_commodity_prices(self):
        """Alias for sync_market_prices"""
        return self.sync_market_prices()
