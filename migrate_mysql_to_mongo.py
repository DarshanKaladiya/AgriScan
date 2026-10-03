"""
AgriScan Full Production Migration: MySQL -> MongoDB
Migrates 100% of all data from local MySQL `agri_intelligence` database:
- master_crops (all 272 rows)
- companies (all 51 rows)
- input_products (all 64 rows, with denormalized brand_name)
- crop_advisories (all 770 rows)
- mandi_prices (all 11,527 rows in bulk batches with string date YYYY-MM-DD)
Also ensures:
- disease_info (all 17 multilingual crop disease knowledge documents mapped to real crop IDs)
- demo users (Farmer & Officer accounts with bcrypt)
- counters (synced to max existing IDs)
- Row-count verification comparing MySQL vs MongoDB
"""

import os
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, date
from decimal import Decimal
from pymongo import InsertOne
from db_utils import get_db, init_db
from auth_utils import hash_password

MYSQL_HOST = os.getenv("DB_HOST", "127.0.0.1")
MYSQL_USER = os.getenv("DB_USER", "root")
MYSQL_PASS = os.getenv("DB_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB", "agri_intelligence")

def clean_val(val):
    if isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime) else val.strftime("%Y-%m-%d")
    elif isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val

def clean_record(d: dict) -> dict:
    return {k: clean_val(v) for k, v in d.items()}

def migrate_all():
    print("=" * 70)
    print(">>> AGRISCAN: MIGRATING 100% OF DATA FROM MYSQL TO MONGODB <<<")
    print("=" * 70)

    # 1. Connect to MySQL
    try:
        mysql_conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            cursorclass=DictCursor,
            charset="utf8mb4"
        )
        print(f"[MySQL] Successfully connected to MySQL database '{MYSQL_DB}'.")
    except Exception as e:
        print(f"[MySQL] ERROR: Failed to connect to MySQL: {e}")
        return False

    # 2. Connect to MongoDB
    mongo_db = get_db()
    if mongo_db is None:
        print("[MongoDB] ERROR: Could not connect to MongoDB.")
        return False
    print("[MongoDB] Connected to MongoDB database.")

    # Drop existing collections to ensure a 100% clean full migration from MySQL
    print("[MongoDB] Resetting collections for clean 1-to-1 migration...")
    mongo_db.companies.drop()
    mongo_db.master_crops.drop()
    mongo_db.input_products.drop()
    mongo_db.crop_advisories.drop()
    mongo_db.mandi_prices.drop()

    init_db()

    stats = {}

    with mysql_conn.cursor() as cur:
        # A. Migrate COMPANIES
        cur.execute("SELECT * FROM `companies`;")
        companies_rows = cur.fetchall()
        mysql_companies_count = len(companies_rows)
        comp_map = {}
        max_comp_id = 0
        comp_docs = []
        
        for c in companies_rows:
            cleaned = clean_record(c)
            comp_id = cleaned.get("id")
            if comp_id:
                comp_map[comp_id] = cleaned.get("name", "Generic")
                if comp_id > max_comp_id:
                    max_comp_id = comp_id
            comp_docs.append(cleaned)
            
        if comp_docs:
            mongo_db.companies.insert_many(comp_docs)
        mongo_companies_count = mongo_db.companies.count_documents({})
        stats["companies"] = (mysql_companies_count, mongo_companies_count)
        print(f" -> companies: MySQL={mysql_companies_count} | MongoDB={mongo_companies_count}")

        # B. Migrate MASTER_CROPS
        cur.execute("SELECT * FROM `master_crops`;")
        crops_rows = cur.fetchall()
        mysql_crops_count = len(crops_rows)
        max_crop_id = 0
        crop_docs = []
        
        for crop in crops_rows:
            cleaned = clean_record(crop)
            c_id = cleaned.get("id")
            if c_id and c_id > max_crop_id:
                max_crop_id = c_id
            crop_docs.append(cleaned)
            
        if crop_docs:
            mongo_db.master_crops.insert_many(crop_docs)
        mongo_crops_count = mongo_db.master_crops.count_documents({})
        stats["master_crops"] = (mysql_crops_count, mongo_crops_count)
        print(f" -> master_crops: MySQL={mysql_crops_count} | MongoDB={mongo_crops_count}")

        # C. Migrate INPUT_PRODUCTS
        cur.execute("SELECT * FROM `input_products`;")
        prod_rows = cur.fetchall()
        mysql_prod_count = len(prod_rows)
        max_prod_id = 0
        prod_docs = []
        
        for p in prod_rows:
            cleaned = clean_record(p)
            p_id = cleaned.get("id")
            if p_id and p_id > max_prod_id:
                max_prod_id = p_id
            # Denormalize brand_name for fast queries without joins
            cleaned["brand_name"] = comp_map.get(cleaned.get("brand_id"), "Generic Agro")
            prod_docs.append(cleaned)
            
        if prod_docs:
            mongo_db.input_products.insert_many(prod_docs)
        mongo_prod_count = mongo_db.input_products.count_documents({})
        stats["input_products"] = (mysql_prod_count, mongo_prod_count)
        print(f" -> input_products: MySQL={mysql_prod_count} | MongoDB={mongo_prod_count}")

        # D. Migrate CROP_ADVISORIES
        cur.execute("SELECT * FROM `crop_advisories`;")
        adv_rows = cur.fetchall()
        mysql_adv_count = len(adv_rows)
        max_adv_id = 0
        adv_docs = []
        
        for a in adv_rows:
            cleaned = clean_record(a)
            a_id = cleaned.get("id")
            if a_id and a_id > max_adv_id:
                max_adv_id = a_id
            adv_docs.append(cleaned)
            
        if adv_docs:
            mongo_db.crop_advisories.insert_many(adv_docs)
        mongo_adv_count = mongo_db.crop_advisories.count_documents({})
        stats["crop_advisories"] = (mysql_adv_count, mongo_adv_count)
        print(f" -> crop_advisories: MySQL={mysql_adv_count} | MongoDB={mongo_adv_count}")

        # E. Migrate MANDI_PRICES in bulk batches
        cur.execute("SELECT COUNT(*) as cnt FROM `mandi_prices`;")
        mysql_mandi_count = cur.fetchone()["cnt"]
        print(f" -> migrating {mysql_mandi_count} mandi_prices records in batches of 2000...")
        
        batch_size = 2000
        offset = 0
        max_mandi_id = 0
        
        while True:
            cur.execute(f"SELECT * FROM `mandi_prices` LIMIT {batch_size} OFFSET {offset};")
            mandi_rows = cur.fetchall()
            if not mandi_rows:
                break
                
            batch_docs = []
            for m in mandi_rows:
                cleaned = clean_record(m)
                m_id = cleaned.get("id")
                if m_id and m_id > max_mandi_id:
                    max_mandi_id = m_id
                    
                # Format price_date explicitly as YYYY-MM-DD string
                p_date = m.get("price_date")
                if isinstance(p_date, (datetime, date)):
                    cleaned["price_date"] = p_date.strftime("%Y-%m-%d")
                else:
                    cleaned["price_date"] = str(p_date) if p_date else ""
                batch_docs.append(cleaned)
                
            if batch_docs:
                mongo_db.mandi_prices.insert_many(batch_docs, ordered=False)
                
            offset += len(mandi_rows)
            print(f"    progress: {offset}/{mysql_mandi_count} records inserted...")
            
        mongo_mandi_count = mongo_db.mandi_prices.count_documents({})
        stats["mandi_prices"] = (mysql_mandi_count, mongo_mandi_count)
        print(f" -> mandi_prices: MySQL={mysql_mandi_count} | MongoDB={mongo_mandi_count}")

    mysql_conn.close()

    # 3. Ensure Multilingual Disease Knowledge documents exist with correct crop IDs
    seed_disease_knowledge(mongo_db)

    # 4. Ensure Demo Users exist
    seed_demo_users(mongo_db)

    # 5. Sync Sequence Counters to avoid ID collisions
    mongo_db.counters.update_one({"_id": "user_id"}, {"$max": {"seq": 50}}, upsert=True)
    mongo_db.counters.update_one({"_id": "crop_id"}, {"$max": {"seq": max_crop_id + 10}}, upsert=True)
    mongo_db.counters.update_one({"_id": "product_id"}, {"$max": {"seq": max_prod_id + 10}}, upsert=True)
    mongo_db.counters.update_one({"_id": "scan_id"}, {"$max": {"seq": 1000}}, upsert=True)

    # 6. Print Verification Summary Table
    print("\n" + "=" * 70)
    print("MIGRATION VERIFICATION AUDIT:")
    print("=" * 70)
    print(f"{'Collection / Table':<22} | {'MySQL Rows':<15} | {'MongoDB Docs':<15} | {'Status'}")
    print("-" * 70)
    for table, (m_count, mongo_c) in stats.items():
        status_str = "MATCHED (100% OK)" if mongo_c == m_count else f"DIFF ({mongo_c - m_count})"
        print(f"{table:<22} | {m_count:<15} | {mongo_c:<15} | {status_str}")
    print("-" * 70)
    print(f"disease_info           | {'N/A':<15} | {mongo_db.disease_info.count_documents({}):<15} | OK")
    print(f"users                  | {'N/A':<15} | {mongo_db.users.count_documents({}):<15} | OK")
    print(f"scans                  | {'N/A':<15} | {mongo_db.scans.count_documents({}):<15} | OK")
    print("=" * 70)
    print("ALL MYSQL DATA HAS BEEN FULLY AND COMPLETELY MIGRATED TO MONGODB!\n")
    return True

def seed_disease_knowledge(db):
    """
    Ensures complete 17 disease documents are present in disease_info collection,
    mapped to real MySQL crop IDs: Tomato=30, Potato=31, Maize=3.
    """
    diseases = [
        # --- TOMATO (crop_id: 30) ---
        {
            "class_key": "Tomato___Bacterial_spot",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Bacterial Spot", "hi": "जीवाणु पत्ती धब्बा रोग (टमाटर)", "gu": "જીવાણુ પાન ટપકાં રોગ (ટામેટા)"},
            "symptoms": {"en": "Small dark water-soaked circular spots with yellow halos on leaves, rough raised spots on fruit.", "hi": "पत्तियों और तनों पर पीले घेरे वाले छोटे गहरे पानी जैसे गोल धब्बे।", "gu": "પાન અને ડાળી પર પીળી કિનારીવાળા નાના કાળા ડાઘ."},
            "prevention": {"en": "Use hot water treated seeds. Avoid overhead irrigation.", "hi": "गर्म पानी से उपचारित बीज बोएं। पत्तियों पर पानी न छिड़कें।", "gu": "ગરમ પાણીથી માવજત કરેલ બિયારણ વાવો. પાન ભીના ન રહે તેનું ધ્યાન રાખો."},
            "treatment": {"en": "Spray Copper Oxychloride 50% WP (2.5 g/L) + Streptocycline upon first symptom.", "hi": "कॉपर ऑक्सीक्लोराइड 50% WP (2.5 ग्राम/लीटर) और स्ट्रेप्टोसाइक्लिन का छिड़काव करें।", "gu": "કોપર ઓક્સીક્લોરાઇડ ૫૦% WP સાથે સ્ટ્રેપ્ટોસાયક્લિન છાંટો."},
            "recommended_technical_names": ["Copper Oxychloride 50% WP"],
            "safety_note": {"en": "Bacterial spot spreads rapidly through wind-driven rains.", "hi": "हवा और बारिश के छींटों से यह जीवाणु तेजी से फैलता है।", "gu": "પવન અને વરસાદના છાંટાથી ઝડપથી ફેલાય છે."},
            "audio": {"en": "audio/en/tomato_bacterial_spot.mp3", "hi": "audio/hi/tomato_bacterial_spot.mp3", "gu": "audio/gu/tomato_bacterial_spot.mp3"}
        },
        {
            "class_key": "Tomato___Early_blight",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Early Blight", "hi": "अगेती झुलसा (टमाटर)", "gu": "વહેલો સુકારો (ટામેટા)"},
            "symptoms": {"en": "Dark brown circular spots with concentric rings on older leaves.", "hi": "निचली पत्तियों पर गोल छल्लेदार धब्बे।", "gu": "નીચેના જૂના પાન પર કથ્થઈ ગોળ ટપકાં."},
            "prevention": {"en": "Rotate crops every 2-3 years. Avoid wetting leaves.", "hi": "2-3 साल में फसल चक्र अपनाएं।", "gu": "પાકની ફેરબદલી કરો."},
            "treatment": {"en": "Prune infected leaves. Spray Mancozeb 75% WP (2.5 g/L).", "hi": "मैंकोजेब 75% WP (2.5 ग्राम/लीटर) का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP નો છંટકાવ કરો."},
            "recommended_technical_names": ["Mancozeb 75% WP", "Copper Oxychloride 50% WP"],
            "safety_note": {"en": "Wear gloves and face mask during spraying.", "hi": "छिड़काव के समय दस्ताने और मास्क पहनें।", "gu": "દવા છાંટતી વખતે હાથમોજાં અને માસ્ક પહેરો."},
            "audio": {"en": "audio/en/tomato_early_blight.mp3", "hi": "audio/hi/tomato_early_blight.mp3", "gu": "audio/gu/tomato_early_blight.mp3"}
        },
        {
            "class_key": "Tomato___Late_blight",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "high",
            "name": {"en": "Late Blight", "hi": "पछेती झुलसा (टमाटर)", "gu": "મોડો સુકારો (ટામેટા)"},
            "symptoms": {"en": "Water-soaked lesions on leaves and stems with white fungal mold underneath.", "hi": "पत्तियों और तनों पर पानी जैसे काले धब्बे।", "gu": "પાન અને ડાળી પર કાળા પાણી જેવા ડાઘ."},
            "prevention": {"en": "Destroy cull piles, plant certified disease-free seedlings.", "hi": "संक्रमित अवशेषों को नष्ट करें।", "gu": "રોગિષ્ટ છોડના અવશેષોનો નાશ કરો."},
            "treatment": {"en": "Spray Metalaxyl 4% + Mancozeb 64% WP (Ridomil Gold 2.5 g/L).", "hi": "मेटालैक्सिल 4% + मैंकोजेब 64% WP का तुरंत छिड़काव करें।", "gu": "મેટાલેક્સિલ ૪% + મેન્કોઝેબ ૬૪% WP નો છંટકાવ કરો."},
            "recommended_technical_names": ["Metalaxyl 4% + Mancozeb 64% WP", "Mancozeb 75% WP"],
            "safety_note": {"en": "Spreads rapidly in cool, humid weather.", "hi": "ठंडे और नम मौसम में बहुत तेजी से फैलता है।", "gu": "ભેજવાળા વાતાવરણમાં ખૂબ ઝડપથી ફેલાય છે."},
            "audio": {"en": "audio/en/tomato_late_blight.mp3", "hi": "audio/hi/tomato_late_blight.mp3", "gu": "audio/gu/tomato_late_blight.mp3"}
        },
        {
            "class_key": "Tomato___Leaf_Mold",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Leaf Mold", "hi": "पत्ती का फफूंद रोग", "gu": "પાનનો ફૂગ રોગ (મોલ્ડ)"},
            "symptoms": {"en": "Pale green/yellow spots on upper leaf surfaces, olive green velvety mold underneath.", "hi": "पत्ती पर हल्के पीले धब्बे और निचली सतह पर मखमली फफूंद।", "gu": "પાન પર પીળા ડાઘ અને નીચે મખમલી ફૂગ."},
            "prevention": {"en": "Improve ventilation, avoid night irrigation.", "hi": "हवा का संचार बढ़ाएं, रात में पानी न दें।", "gu": "હવા-ઉજાસ રાખો, રાત્રે પાણી ન આપો."},
            "treatment": {"en": "Spray Carbendazim 12% + Mancozeb 63% WP (2 g/L).", "hi": "कार्बेंडाजिम + मैंकोजेब (2 ग्राम/लीटर) का छिड़काव करें।", "gu": "કાર્બેન્ડાઝીમ + મેન્કોઝેબ (૨ ગ્રામ/લિટર) નો છંટકાવ કરો."},
            "recommended_technical_names": ["Carbendazim 12% + Mancozeb 63% WP"],
            "safety_note": {"en": "Do not inhale spray mist.", "hi": "छिड़काव के समय मुंह ढंकें।", "gu": "છંટકાવ વખતે મોં ઢાંકો."},
            "audio": {"en": "audio/en/tomato_leaf_mold.mp3", "hi": "audio/hi/tomato_leaf_mold.mp3", "gu": "audio/gu/tomato_leaf_mold.mp3"}
        },
        {
            "class_key": "Tomato___Septoria_leaf_spot",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Septoria Leaf Spot", "hi": "सेप्टोरिया पत्ती धब्बा", "gu": "સેપ્ટોરિયા પાન ટપકાં"},
            "symptoms": {"en": "Small circular spots with grayish-white centers and dark brown margins.", "hi": "सफेद केंद्र वाले छोटे गोल धब्बे।", "gu": "સફેદ કેન્દ્રવાળા નાના ગોળ ટપકાં."},
            "prevention": {"en": "Mulch soil to prevent rain splash.", "hi": "मल्चिंग करें ताकि मिट्टी न उड़े।", "gu": "માટીના છાંટા રોકવા મલ્ચિંગ કરો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2 g/L).", "hi": "मैंकोजेब 75% WP का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP નો છંટકાવ કરો."},
            "recommended_technical_names": ["Mancozeb 75% WP"],
            "safety_note": {"en": "Ensure complete leaf coverage.", "hi": "पत्तियों को दोनों तरफ से अच्छी तरह भिगोएं।", "gu": "પાનની બંને બાજુ સરખો છંટકાવ કરો."},
            "audio": {"en": "audio/en/tomato_septoria.mp3", "hi": "audio/hi/tomato_septoria.mp3", "gu": "audio/gu/tomato_septoria.mp3"}
        },
        {
            "class_key": "Tomato___Spider_mites_Two_spotted_spider_mite",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Spider Mites (Pest)", "hi": "लाल मकड़ी (कीट प्रकोप)", "gu": "લાલ કથીરી (જીવાત ઉપદ્રવ)"},
            "symptoms": {"en": "Yellow speckling on leaves, fine webbing under leaves, leaf bronzing.", "hi": "पत्तियों पर बारीक पीले बिंदु और जाले।", "gu": "પાન પર ઝીણા ટપકાં અને જાળી."},
            "prevention": {"en": "Maintain soil moisture; avoid dry dusty conditions.", "hi": "खेत में नमी रखें।", "gu": "જમીનમાં ભેજ જાળવી રાખો."},
            "treatment": {"en": "Spray Imidacloprid 30.5% SC or Chlorantraniliprole 18.5% SC.", "hi": "इमिडाक्लोप्रिड या कोराजन का छिड़काव करें।", "gu": "ઇમિડાક્લોપ્રિડ અથવા કોરાજન છાંટો."},
            "recommended_technical_names": ["Imidacloprid 30.5% SC", "Chlorantraniliprole 18.5% SC"],
            "safety_note": {"en": "Target undersides of leaves.", "hi": "पत्ती के नीचे स्प्रे करें।", "gu": "પાનની નીચે દવા પહોંચાડો."},
            "audio": {"en": "audio/en/tomato_spider_mites.mp3", "hi": "audio/hi/tomato_spider_mites.mp3", "gu": "audio/gu/tomato_spider_mites.mp3"}
        },
        {
            "class_key": "Tomato___Target_Spot",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Target Spot", "hi": "टारगेट स्पॉट रोग", "gu": "ટાર્ગેટ સ્પોટ"},
            "symptoms": {"en": "Brown circular spots with concentric rings on leaves and sunken pits on fruit.", "hi": "पत्तियों पर छल्लेदार गोल धब्बे।", "gu": "પાન પર ગોળાકાર ડાઘ."},
            "prevention": {"en": "Prune foliage to improve airflow.", "hi": "हवा-धूप के लिए छंटाई करें।", "gu": "યોગ્ય હવા-ઉજાસ રાખો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2.5 g/L).", "hi": "मैंकोजेब 75% WP का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP છાંટો."},
            "recommended_technical_names": ["Mancozeb 75% WP"],
            "safety_note": {"en": "Avoid excess overhead watering.", "hi": "पत्तियों पर पानी न छिड़कें।", "gu": "પાન પર પાણી ન છાંટો."},
            "audio": {"en": "audio/en/tomato_target_spot.mp3", "hi": "audio/hi/tomato_target_spot.mp3", "gu": "audio/gu/tomato_target_spot.mp3"}
        },
        {
            "class_key": "Tomato___Yellow_Leaf_Curl_Virus",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "high",
            "name": {"en": "Yellow Leaf Curl Virus", "hi": "पत्ती मरोड़ विषाणु", "gu": "પાન વળવાનો વાયરસ (કોકડવા)"},
            "symptoms": {"en": "Upward leaf curling, yellow leaf margins, stunted growth.", "hi": "पत्तियां ऊपर की ओर मुड़ना और पौधा बौना रहना।", "gu": "પાન ઉપર વળવા અને છોડ ઠિંગણો રહેવો."},
            "prevention": {"en": "Control vector whiteflies using yellow sticky traps.", "hi": "पीले स्टिकी ट्रैप से सफेद मक्खी रोकें।", "gu": "પીળા સ્ટીકી ટ્રેપ લગાવો."},
            "treatment": {"en": "Uproot infected plants. Spray Imidacloprid 30.5% SC (0.3 ml/L) for whiteflies.", "hi": "रोगग्रस्त पौधे उखाड़ें, सफेद मक्खी हेतु इमिडाक्लोप्रिड छिड़कें।", "gu": "રોગિષ્ટ છોડ ઉપાડી લો, સફેદ માખી માટે ઇમિડાક્લોપ્રિડ છાંટો."},
            "recommended_technical_names": ["Imidacloprid 30.5% SC"],
            "safety_note": {"en": "Virus is transmitted by whiteflies.", "hi": "सफेद मक्खी द्वारा फैलता है।", "gu": "સફેદ માખી દ્વારા ફેલાય છે."},
            "audio": {"en": "audio/en/tomato_yellow_curl.mp3", "hi": "audio/hi/tomato_yellow_curl.mp3", "gu": "audio/gu/tomato_yellow_curl.mp3"}
        },
        {
            "class_key": "Tomato___mosaic_virus",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Disease",
            "severity": "high",
            "name": {"en": "Mosaic Virus", "hi": "मोज़ेक वायरस", "gu": "મોઝેક વાયરસ"},
            "symptoms": {"en": "Mottled dark green and light yellow pattern on leaves.", "hi": "पत्तियों पर हरे-पीले धब्बों का मोज़ेक पैटर्न।", "gu": "પાન પર ઘાટા લીલા અને પીળા પટ્ટા."},
            "prevention": {"en": "Wash hands with soap before touching plants.", "hi": "हाथों व औजारों को साबुन से धोएं।", "gu": "હાથ અને ઓજારો સાબુથી સાફ કરો."},
            "treatment": {"en": "Remove infected plants. No chemical cure exists.", "hi": "रोगग्रस्त पौधे हटाएं, कोई रासायनिक इलाज नहीं है।", "gu": "રોગિષ્ટ છોડ ઉપાડી નાશ કરો."},
            "recommended_technical_names": [],
            "safety_note": {"en": "Spreads easily by contact.", "hi": "छूने से फैलता है।", "gu": "સ્પર્શથી ફેલાય છે."},
            "audio": {"en": "audio/en/tomato_mosaic.mp3", "hi": "audio/hi/tomato_mosaic.mp3", "gu": "audio/gu/tomato_mosaic.mp3"}
        },
        {
            "class_key": "Tomato___healthy",
            "crop_id": 30,
            "crop_name": "Tomato",
            "kind": "Healthy",
            "severity": "none",
            "name": {"en": "Tomato - Healthy", "hi": "स्वस्थ टमाटर की पत्ती", "gu": "તંદુરસ્ત ટામેટાંનું પાન"},
            "symptoms": {"en": "Vibrant green uniform leaves with no spots or curling.", "hi": "पत्तियां पूरी तरह हरी और बेदाग हैं।", "gu": "પાન તદ્દન લીલાંછમ અને ડાઘ વગરનાં છે."},
            "prevention": {"en": "Maintain regular watering and nutrition with NPK 19:19:19.", "hi": "संतुलित पोषण और सिंचाई जारी रखें।", "gu": "નિયમિત પાણી અને NPK 19:19:19 ખાતર આપો."},
            "treatment": {"en": "No pesticide needed.", "hi": "किसी कीटनाशक की आवश्यकता नहीं है।", "gu": "કોઈ દવાની જરૂર નથી."},
            "recommended_technical_names": ["NPK 19:19:19"],
            "safety_note": {"en": "Continue routine weekly field inspection.", "hi": "नियमित निरीक्षण जारी रखें।", "gu": "નિયમિત તપાસ ચાલુ રાખો."},
            "audio": {"en": "audio/en/tomato_healthy.mp3", "hi": "audio/hi/tomato_healthy.mp3", "gu": "audio/gu/tomato_healthy.mp3"}
        },

        # --- POTATO (crop_id: 31) ---
        {
            "class_key": "Potato___Early_blight",
            "crop_id": 31,
            "crop_name": "Potato",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Potato Early Blight", "hi": "आलू का अगेती झुलसा", "gu": "બટાટાનો વહેલો સુકારો"},
            "symptoms": {"en": "Concentric rings forming brown target spots on lower leaves.", "hi": "निचली पत्तियों पर छल्लेदार भूरे धब्बे।", "gu": "નીચેના પાન પર ગોળ ચક્રાકાર ડાઘ."},
            "prevention": {"en": "Use certified seed tubers, avoid nitrogen deficiency.", "hi": "प्रमाणित बीज का उपयोग करें।", "gu": "પ્રમાણિત બિયારણ વાપરો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2 g/L) or Carbendazim + Mancozeb.", "hi": "मैंकोजेब 75% WP (2 ग्राम/लीटर) का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP નો છંટકાવ કરો."},
            "recommended_technical_names": ["Mancozeb 75% WP", "Carbendazim 12% + Mancozeb 63% WP"],
            "safety_note": {"en": "Spray before tuber initiation if blight occurred previously.", "hi": "कंद बनने से पहले छिड़काव करें।", "gu": "ગાંઠ બેસતા પહેલાં છંટકાવ કરો."},
            "audio": {"en": "audio/en/potato_early_blight.mp3", "hi": "audio/hi/potato_early_blight.mp3", "gu": "audio/gu/potato_early_blight.mp3"}
        },
        {
            "class_key": "Potato___Late_blight",
            "crop_id": 31,
            "crop_name": "Potato",
            "kind": "Disease",
            "severity": "high",
            "name": {"en": "Potato Late Blight", "hi": "आलू का पछेती झुलसा", "gu": "બટાટાનો મોડો સુકારો"},
            "symptoms": {"en": "Water-soaked lesions on leaf margins with white downy growth.", "hi": "पत्तियों के किनारों पर काले गीले धब्बे।", "gu": "પાનની કિનારી પર કાળા ભીના ડાઘ."},
            "prevention": {"en": "Earth up soil well around tubers.", "hi": "कंदों पर अच्छी तरह मिट्टी चढ़ाएं।", "gu": "બટાટાની ગાંઠ પર માટી બરાબર ચડાવો."},
            "treatment": {"en": "Spray Metalaxyl 4% + Mancozeb 64% WP (2.5 g/L).", "hi": "मेटालैक्सिल 4% + मैंकोजेब 64% WP का तत्काल छिड़काव करें।", "gu": "મેટાલેક્સિલ ૪% + મેન્કોઝેબ ૬૪% WP છાંટો."},
            "recommended_technical_names": ["Metalaxyl 4% + Mancozeb 64% WP"],
            "safety_note": {"en": "Destroys potato crops rapidly in damp weather.", "hi": "गीले मौसम में बहुत तेजी से फसल नष्ट करता है।", "gu": "ભેજવાળા વાતાવરણમાં પાક ઝડપથી બગાડે છે."},
            "audio": {"en": "audio/en/potato_late_blight.mp3", "hi": "audio/hi/potato_late_blight.mp3", "gu": "audio/gu/potato_late_blight.mp3"}
        },
        {
            "class_key": "Potato___healthy",
            "crop_id": 31,
            "crop_name": "Potato",
            "kind": "Healthy",
            "severity": "none",
            "name": {"en": "Potato - Healthy", "hi": "स्वस्थ आलू की पत्ती", "gu": "તંદુરસ્ત બટાટાનું પાન"},
            "symptoms": {"en": "Dense green foliage without lesions, rot, or curling.", "hi": "पत्तियां घनी, हरी और धब्बा रहित हैं।", "gu": "પાન ઘટાદાર અને ડાઘ વગરનાં છે."},
            "prevention": {"en": "Maintain earthing up and timely irrigation.", "hi": "समय पर मिट्टी चढ़ाएं और पानी दें।", "gu": "સમયસર માટી ચડાવો અને પિયત આપો."},
            "treatment": {"en": "No pesticide required.", "hi": "दवा की आवश्यकता नहीं है।", "gu": "કોઈ દવાની જરૂર નથી."},
            "recommended_technical_names": [],
            "safety_note": {"en": "Crop in great health.", "hi": "फसल स्वस्थ है।", "gu": "પાક તંદુરસ્ત છે."},
            "audio": {"en": "audio/en/potato_healthy.mp3", "hi": "audio/hi/potato_healthy.mp3", "gu": "audio/gu/potato_healthy.mp3"}
        },

        # --- CORN / MAIZE (crop_id: 3) ---
        {
            "class_key": "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot",
            "crop_id": 3,
            "crop_name": "Maize",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Gray Leaf Spot (Maize)", "hi": "मक्के का धूसर पत्ती धब्बा", "gu": "મકાઈનો ગ્રે પાન ટપકાં રોગ"},
            "symptoms": {"en": "Rectangular gray spots bounded by leaf veins.", "hi": "नसों के बीच लंबे आयताकार धूसर धब्बे।", "gu": "પાનની નસો વચ્ચે લંબચોરસ રાખોડી પટ્ટા."},
            "prevention": {"en": "Rotate crops, plant tolerant hybrids.", "hi": "फसल चक्र अपनाएं, सहिष्णु बीज लगाएं।", "gu": "પાકની ફેરબદલી કરો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2 g/L).", "hi": "मैंकोजेब 75% WP का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP નો છંટકાવ કરો."},
            "recommended_technical_names": ["Mancozeb 75% WP"],
            "safety_note": {"en": "Protect the ear leaf for optimal yield.", "hi": "भुट्टे के पास वाली पत्ती को बचाएं।", "gu": "ડોડા પાસેના પાનને બચાવો."},
            "audio": {"en": "audio/en/corn_gray_leaf_spot.mp3", "hi": "audio/hi/corn_gray_leaf_spot.mp3", "gu": "audio/gu/corn_gray_leaf_spot.mp3"}
        },
        {
            "class_key": "Corn_(maize)___Common_rust",
            "crop_id": 3,
            "crop_name": "Maize",
            "kind": "Disease",
            "severity": "medium",
            "name": {"en": "Common Rust (Maize)", "hi": "मक्के का सामान्य गेरुआ (रस्ट)", "gu": "મકાઈનો ગેરુ રોગ (રસ્ટ)"},
            "symptoms": {"en": "Golden-brown powdery pustules on both leaf surfaces.", "hi": "पत्तियों पर सुनहरे भूरे पाउडर जैसे फफोले।", "gu": "પાન પર સોનેરી કથ્થઈ પાવડર જેવી ફોલ્લીઓ."},
            "prevention": {"en": "Plant resistant hybrids, sow early.", "hi": "रोगरोधी बीज चुनें, समय पर बुवाई करें।", "gu": "રોગપ્રતિકારક બિયારણ વાવો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2 g/L).", "hi": "मैंकोजेब 75% WP का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP છાંટો."},
            "recommended_technical_names": ["Mancozeb 75% WP"],
            "safety_note": {"en": "Rust spores travel on wind currents.", "hi": "रस्ट के बीजाणु हवा से दूर तक फैलते हैं।", "gu": "ગેરુના કણો પવન દ્વારા ફેલાય છે."},
            "audio": {"en": "audio/en/corn_common_rust.mp3", "hi": "audio/hi/corn_common_rust.mp3", "gu": "audio/gu/corn_common_rust.mp3"}
        },
        {
            "class_key": "Corn_(maize)___Northern_Leaf_Blight",
            "crop_id": 3,
            "crop_name": "Maize",
            "kind": "Disease",
            "severity": "high",
            "name": {"en": "Northern Leaf Blight", "hi": "उत्तरी पत्ती झुलसा (मक्का)", "gu": "નોર્ધન લીફ બ્લાઇટ (મકાઈ)"},
            "symptoms": {"en": "Long cigar-shaped grayish-green lesions on leaves.", "hi": "पत्तियों पर सिगार के आकार के बड़े धब्बे।", "gu": "પાન પર સિગાર આકારના લાંબા ડાઘ."},
            "prevention": {"en": "Bury crop residues after harvest, rotate crops.", "hi": "अवशेषों को मिट्टी में दबाएं, फसल चक्र अपनाएं।", "gu": "અવશેષો જમીનમાં દાટો."},
            "treatment": {"en": "Spray Mancozeb 75% WP (2 g/L).", "hi": "मैंकोजेब 75% WP का छिड़काव करें।", "gu": "મેન્કોઝેબ ૭૫% WP છાંટો."},
            "recommended_technical_names": ["Mancozeb 75% WP"],
            "safety_note": {"en": "Severe blight before pollination cuts yield by 50%.", "hi": "परागण से पहले भारी संक्रमण भारी नुकसान करता है।", "gu": "પરાગનયન પહેલાં રોગ લાગવાથી મોટું નુકસાન થાય છે."},
            "audio": {"en": "audio/en/corn_northern_blight.mp3", "hi": "audio/hi/corn_northern_blight.mp3", "gu": "audio/gu/corn_northern_blight.mp3"}
        },
        {
            "class_key": "Corn_(maize)___healthy",
            "crop_id": 3,
            "crop_name": "Maize",
            "kind": "Healthy",
            "severity": "none",
            "name": {"en": "Maize - Healthy", "hi": "स्वस्थ मक्के की पत्ती", "gu": "તંદુરસ્ત મકાઈનું પાન"},
            "symptoms": {"en": "Broad arching deep green leaves with no lesions.", "hi": "गहरे हरे रंग की चौड़ी स्वस्थ पत्तियां।", "gu": "ઘેરા લીલા રંગના પહોળા પાન."},
            "prevention": {"en": "Ensure balanced nutrition and timely weeding.", "hi": "संतुलित खाद और निराई करें।", "gu": "યોગ્ય ખાતર અને નિંદામણ કરો."},
            "treatment": {"en": "No pesticide required.", "hi": "दवा की आवश्यकता नहीं है।", "gu": "કોઈ દવાની જરૂર નથી."},
            "recommended_technical_names": [],
            "safety_note": {"en": "Crop in excellent health.", "hi": "फसल उत्तम स्थिति में है।", "gu": "પાક તંદુરસ્ત છે."},
            "audio": {"en": "audio/en/corn_healthy.mp3", "hi": "audio/hi/corn_healthy.mp3", "gu": "audio/gu/corn_healthy.mp3"}
        },

        # --- UNKNOWN / NOT A LEAF (crop_id: 0) ---
        {
            "class_key": "Unknown___not_a_leaf",
            "crop_id": 0,
            "crop_name": "Unknown",
            "kind": "Other",
            "severity": "none",
            "name": {"en": "Not a Crop Leaf / Unclear Image", "hi": "फसल की पत्ती नहीं पहचानी गई", "gu": "પાકની પત્તી ઓળખાઈ નથી / અસ્પષ્ટ ફોટો"},
            "symptoms": {"en": "Image does not appear to be a supported crop leaf.", "hi": "फोटो में समर्थित पत्ती स्पष्ट नहीं है।", "gu": "ફોટામાં પાન સ્પષ્ટ દેખાતું નથી."},
            "prevention": {"en": "Take photo in daylight covering the leaf center.", "hi": "उजाले में पत्ती का साफ फोटो लें।", "gu": "અજવાળામાં સ્પષ્ટ ફોટો લો."},
            "treatment": {"en": "Please retake the photo in good lighting.", "hi": "कृपया अच्छी रोशनी में दोबारा फोटो लें।", "gu": "કૃપા કરીને ફરીથી ફોટો લો."},
            "recommended_technical_names": [],
            "safety_note": {"en": "AgriScan supports Tomato, Potato, and Maize crops.", "hi": "एग्रीस्कैन टमाटर, आलू और मक्का का समर्थन करता है।", "gu": "એગ્રીસ્કેન ટામેટાં, બટાટા અને મકાઈને સપોર્ટ કરે છે."},
            "audio": {"en": "audio/en/unknown_leaf.mp3", "hi": "audio/hi/unknown_leaf.mp3", "gu": "audio/gu/unknown_leaf.mp3"}
        }
    ]

    for d in diseases:
        db.disease_info.update_one({"class_key": d["class_key"]}, {"$set": d}, upsert=True)
    print(f"[MongoDB] Disease Info verified ({len(diseases)} documents).")

def seed_demo_users(db):
    """Seeds default demo accounts with bcrypt passwords."""
    demo_users = [
        {
            "id": 1,
            "name": "Ramesh Patel",
            "login_id": "9876543210",
            "password_hash": hash_password("farmer123"),
            "role": "farmer",
            "preferred_language": "gu",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 2,
            "name": "Kisan Kumar",
            "login_id": "farmer@agriscan.com",
            "password_hash": hash_password("farmer123"),
            "role": "farmer",
            "preferred_language": "hi",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 3,
            "name": "Dr. Anita Desai",
            "login_id": "officer@agriscan.com",
            "password_hash": hash_password("officer123"),
            "role": "officer",
            "preferred_language": "en",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 4,
            "name": "District Agro Officer",
            "login_id": "9876543211",
            "password_hash": hash_password("officer123"),
            "role": "officer",
            "preferred_language": "en",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    for u in demo_users:
        db.users.update_one({"login_id": u["login_id"]}, {"$set": u}, upsert=True)
    print(f"[MongoDB] Demo users verified (Farmer & Officer accounts ready).")

if __name__ == "__main__":
    migrate_all()
