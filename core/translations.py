"""
AgriIntelligence & AgriScan Multilingual Translation Catalog
Languages: English (en), Hindi (hi), Gujarati (gu)
"""

TRANSLATIONS = {
    "en": {
        # Unrecognized / OOD Guard (en)
        "unrecognized_title": "Inconclusive Scan / Unrecognized Subject",
        "unrecognized_subtitle": "This photo does not match any recognized crop disease in the AgriScan dataset.",
        "unrecognized_reason": "The uploaded photo appears to be either a non-plant object, an unsupported plant species, or too blurry for reliable diagnosis. AgriScan currently supports Corn (Maize), Potato, and Tomato foliage.",
        "guidelines_title": "Tips for an Accurate Leaf Scan",
        "tip_supported_crops": "Scan only supported crops: Corn, Potato, or Tomato leaves",
        "tip_close_up": "Hold the camera steady 10–20 cm away with good natural lighting",
        "tip_no_clutter": "Avoid fingers, people, backgrounds, or non-plant objects",
        "btn_try_again": "Try Scanning Again",

        # Camera Scanner (en)
        "camera_scanner": "Live Camera Scanner",
        "open_camera": "Open Live Camera",
        "upload_file": "Upload Leaf Photo",
        "capture_leaf": "Capture Leaf",
        "flip_camera": "Flip Camera",
        "close_camera": "Close Camera",
        "camera_align_tip": "Position the infected crop leaf inside the brackets",
        "camera_error": "Camera access is unavailable or was denied. Please allow camera permission or choose an image file.",

        # Brand & Global
        "brand_name": "AgriIntelligence",
        "brand_tagline": "Autonomous Agro-Advisory",
        "language": "Language",
        "lang_en": "English",
        "lang_hi": "हिंदी (Hindi)",
        "lang_gu": "ગુજરાતી (Gujarati)",
        "system_online": "SYSTEM LIVE",
        "live_sync": "Live Government Sync",
        "search_placeholder": "Search crops, diseases, inputs, APMC markets...",
        "view_all": "View All",
        "details": "Details",
        "active": "Active",
        "status": "Status",
        "loading": "Loading...",
        "back": "Back",
        "submit": "Submit",
        "cancel": "Cancel",
        "close": "Close",
        
        # Navigation
        "nav_dashboard": "Dashboard",
        "nav_crops": "Crop Guide",
        "nav_mandi": "Mandi Rates",
        "nav_compare": "Compare Inputs",
        "nav_companies": "Agri Partners",
        "nav_scans": "My Field Scans",
        "nav_reports": "Field Reports",
        "nav_login": "Farmer Login",
        "nav_signup": "Register",
        "nav_logout": "Logout",
        
        # Dashboard
        "dash_title": "National Agri Intelligence Command",
        "dash_subtitle": "Real-time crop surveillance, APMC market arrivals, and AI-driven disease diagnosis.",
        "kpi_crops": "Tracked Crops",
        "kpi_crops_sub": "Major Indian staples & cash crops",
        "kpi_mandi": "Active APMC Mandis",
        "kpi_mandi_sub": "Live market trading nodes",
        "kpi_companies": "Verified Agri Inputs",
        "kpi_companies_sub": "Tested bio & chemical inputs",
        "kpi_accuracy": "AI Diagnostic Engine",
        "kpi_accuracy_sub": "Offline-first MobileNetV2 accuracy",
        "market_pulse": "Market Pulse (Price Trends)",
        "top_gainers": "Top Price Gainers",
        "top_losers": "Top Price Dips",
        "quick_actions": "Agricultural Action Center",
        "action_scan": "Scan Crop Leaf",
        "action_scan_desc": "Instant disease diagnosis with treatment recommendations.",
        "action_mandi": "Check APMC Mandi Rates",
        "action_mandi_desc": "Live modal and wholesale rates across Indian states.",
        "action_compare": "Compare Inputs",
        "action_compare_desc": "Evaluate cost-per-unit across verified manufacturers.",
        "action_crops": "Browse Crop Library",
        "action_crops_desc": "Agronomic advice, sowing schedules, and yield optimization.",
        
        # Mandi Rates
        "mandi_title": "APMC Mandi Real-Time Prices",
        "mandi_subtitle": "Daily wholesale commodity rates and mandi arrivals across India.",
        "filter_state": "Select State",
        "filter_district": "Select District",
        "filter_crop": "Select Crop",
        "all_states": "All States",
        "all_districts": "All Districts",
        "filter_btn": "Apply Filters",
        "reset_btn": "Reset",
        "col_market": "Market / Mandi",
        "col_district": "District / State",
        "col_modal_price": "Modal Price (₹/Qtl)",
        "col_price_range": "Price Range (Min - Max)",
        "col_date": "Report Date",
        "no_mandi_data": "No market arrivals found matching your query.",
        "benchmark_tag": "Govt Benchmark",
        
        # Crops Guide
        "crops_title": "Agricultural Crop Encyclopedia",
        "crops_subtitle": "Agronomic advisories, sowing cycles, and disease management guides.",
        "season": "Season",
        "soil": "Soil Type",
        "duration": "Duration (Days)",
        "water_req": "Water Requirement",
        "view_advisory": "View Advisory & Diseases",
        "crop_overview": "Crop Agronomic Profile",
        "sowing_period": "Sowing Period",
        "harvest_period": "Harvest Period",
        "expected_yield": "Expected Yield",
        "known_diseases": "Common Diseases & Pathogens",
        "symptoms": "Symptoms",
        "treatment": "Recommended Treatment",
        "prevention": "Organic Prevention",
        "chemical_dosage": "Chemical Dosage",
        
        # Compare Inputs
        "compare_title": "Agri Input Price Comparison",
        "compare_subtitle": "Transparent pricing, active ingredient matching, and cost-per-unit optimization.",
        "tech_name": "Active Molecule / Technical Name",
        "brand_name_label": "Brand Name",
        "company": "Manufacturer",
        "pack_size": "Pack Size",
        "unit_price": "Effective Unit Price",
        "select_tech": "Choose Technical Composition",
        "best_deal": "Best Value",
        
        # Companies
        "companies_title": "Verified Agricultural Partners",
        "companies_subtitle": "Authorized input manufacturers and agrochemical suppliers.",
        "company_name": "Company Name",
        "products_count": "Listed Formulations",
        "contact_info": "Contact & Support",
        
        # Scans & Reports (AgriScan)
        "my_scans_title": "My Crop Scans & Diagnosis History",
        "my_scans_subtitle": "Your personal field diagnostic logs and agronomic recommendations.",
        "scan_new_leaf": "Scan New Leaf",
        "confidence": "Diagnostic Confidence",
        "scan_date": "Date of Scan",
        "no_scans": "No scans recorded yet. Use the camera to diagnose your crops.",
        "field_reports_title": "Regional Disease Outbreak Surveillance",
        "field_reports_subtitle": "Real-time epidemiological monitoring for Extension Officers.",
        "total_scans_recorded": "Total Scans Recorded",
        "outbreak_hotspots": "Outbreak Hotspots",
        
        # Auth
        "login_title": "Farmer & Officer Portal",
        "login_subtitle": "Sign in to access your field diagnostics and market subscriptions.",
        "mobile_or_email": "Mobile Number or Email",
        "password": "Password",
        "btn_login": "Sign In",
        "btn_signup": "Create Farmer Account",
        "no_account": "Don't have an account?",
        "have_account": "Already have an account?",
        "demo_farmer": "1-Click Farmer Demo",
        "demo_officer": "1-Click Officer Demo",
        
        # Footer
        "footer_text": "AgriIntelligence System • Empowering Farmers with AI & Data",
        "footer_rights": "All rights reserved. Offline-first AI agricultural protection."
    },
    
    "hi": {
        # Unrecognized / OOD Guard (hi)

        # Camera Scanner (hi)

        # Brand & Global
        "brand_name": "एग्री-इंटेलिजेंस",
        "brand_tagline": "स्वायत्त कृषि परामर्श प्रणाली",
        "language": "भाषा",
        "lang_en": "English",
        "lang_hi": "हिंदी (Hindi)",
        "lang_gu": "ગુજરાતી (Gujarati)",
        "system_online": "प्रणाली सक्रिय",
        "live_sync": "सरकारी लाइव सिंक",
        "search_placeholder": "फसलें, रोग, कीटनाशक, एपीएमसी मंडियां खोजें...",
        "view_all": "सभी देखें",
        "details": "विवरण",
        "active": "सक्रिय",
        "status": "स्थिति",
        "loading": "लोड हो रहा है...",
        "back": "वापस जाएं",
        "submit": "जमा करें",
        "cancel": "रद्द करें",
        "close": "बंद करें",
        
        # Navigation
        "nav_dashboard": "डैशबोर्ड",
        "nav_crops": "फसल निर्देशिका",
        "nav_mandi": "मंडी भाव",
        "nav_compare": "उत्पाद तुलना",
        "nav_companies": "कृषि साझेदार",
        "nav_scans": "खेत के स्कैन",
        "nav_reports": "फील्ड रिपोर्ट",
        "nav_login": "किसान लॉगिन",
        "nav_signup": "पंजीकरण",
        "nav_logout": "लॉगआउट",
        
        # Dashboard
        "dash_title": "राष्ट्रीय कृषि आसूचना केंद्र",
        "dash_subtitle": "वास्तविक समय फसल निगरानी, एपीएमसी मंडी आवक और एआई रोग निदान प्रणाली।",
        "kpi_crops": "निगरानी में फसलें",
        "kpi_crops_sub": "प्रमुख भारतीय नकदी व खाद्यान्न फसलें",
        "kpi_mandi": "सक्रिय एपीएमसी मंडियां",
        "kpi_mandi_sub": "लाइव व्यापार केंद्र",
        "kpi_companies": "सत्यापित कृषि उत्पाद",
        "kpi_companies_sub": "परीक्षित जैविक व रासायनिक उत्पाद",
        "kpi_accuracy": "एआई निदान इंजन",
        "kpi_accuracy_sub": "ऑफलाइन MobileNetV2 सटीकता",
        "market_pulse": "मंडी नब्ज (कीमत रुझान)",
        "top_gainers": "शीर्ष मूल्य वृद्धि",
        "top_losers": "शीर्ष मूल्य गिरावट",
        "quick_actions": "त्वरित कृषि सेवा केंद्र",
        "action_scan": "फसल पत्ती स्कैन करें",
        "action_scan_desc": "रोग की तुरंत पहचान और उपचार सिफारिश प्राप्त करें।",
        "action_mandi": "आज का मंडी भाव देखें",
        "action_mandi_desc": "देशभर की मंडियों के मॉडल और थोक भाव की लाइव स्थिति।",
        "action_compare": "खाद व कीटनाशक तुलना",
        "action_compare_desc": "सर्वोत्तम प्रति-इकाई भाव और गुणवत्ता जांचें।",
        "action_crops": "फसल पुस्तकालय देखें",
        "action_crops_desc": "कृषि वैज्ञानिक सलाह, बुवाई चक्र और उत्पादन वृद्धि के उपाय।",
        
        # Mandi Rates
        "mandi_title": "एपीएमसी मंडी लाइव भाव",
        "mandi_subtitle": "भारत भर की मंडियों के दैनिक थोक जिंस भाव और आवक स्थिति।",
        "filter_state": "राज्य चुनें",
        "filter_district": "ज़िला चुनें",
        "filter_crop": "फसल चुनें",
        "all_states": "सभी राज्य",
        "all_districts": "सभी ज़िले",
        "filter_btn": "फ़िल्टर लागू करें",
        "reset_btn": "रीसेट करें",
        "col_market": "मंडी / बाज़ार",
        "col_district": "ज़िला / राज्य",
        "col_modal_price": "मॉडल भाव (₹/क्विंटल)",
        "col_price_range": "भाव दायरा (न्यूनतम - अधिकतम)",
        "col_date": "रिपोर्ट दिनांक",
        "no_mandi_data": "आपके चयन के अनुसार कोई मंडी रिकॉर्ड नहीं मिला।",
        "benchmark_tag": "सरकारी बेंचमार्क",
        
        # Crops Guide
        "crops_title": "कृषि फसल विश्वकोश",
        "crops_subtitle": "सस्य वैज्ञानिक परामर्श, बुवाई चक्र और पादप रोग प्रबंधन।",
        "season": "मौसम",
        "soil": "मिट्टी का प्रकार",
        "duration": "अवधि (दिन)",
        "water_req": "जल आवश्यकता",
        "view_advisory": "परामर्श व रोग देखें",
        "crop_overview": "फसल सस्य प्रोफ़ाइल",
        "sowing_period": "बुवाई का समय",
        "harvest_period": "कटाई का समय",
        "expected_yield": "अनुमानित पैदावार",
        "known_diseases": "प्रमुख रोग और रोगज़नक़",
        "symptoms": "लक्षण",
        "treatment": "अनुशंसित उपचार",
        "prevention": "जैविक रोकथाम",
        "chemical_dosage": "रासायनिक मात्रा",
        
        # Compare Inputs
        "compare_title": "कृषि उत्पाद मूल्य तुलना",
        "compare_subtitle": "पारदर्शी मूल्य निर्धारण, सक्रिय अणु मिलान और प्रति-इकाई बचत।",
        "tech_name": "सक्रिय अणु / तकनीकी नाम",
        "brand_name_label": "ब्रांड नाम",
        "company": "निर्माता कंपनी",
        "pack_size": "पैकिंग साइज़",
        "unit_price": "प्रभावी प्रति यूनिट भाव",
        "select_tech": "तकनीकी संरचना चुनें",
        "best_deal": "सर्वोत्तम मूल्य",
        
        # Companies
        "companies_title": "सत्यापित कृषि साझेदार",
        "companies_subtitle": "अधिकृत उत्पाद निर्माता और कृषि रसायन आपूर्तिकर्ता।",
        "company_name": "कंपनी का नाम",
        "products_count": "सूचीबद्ध उत्पाद",
        "contact_info": "संपर्क व सहायता",
        
        # Scans & Reports (AgriScan)
        "my_scans_title": "मेरे खेत के स्कैन और स्वास्थ्य इतिहास",
        "my_scans_subtitle": "आपके व्यक्तिगत पादप निदान लॉग और कृषि वैज्ञानिक सिफारिशें।",
        "scan_new_leaf": "नई पत्ती स्कैन करें",
        "confidence": "निदान सटीकता",
        "scan_date": "स्कैन दिनांक",
        "no_scans": "अभी तक कोई स्कैन नहीं है। अपनी फसल जांचने के लिए कैमरे का उपयोग करें।",
        "field_reports_title": "क्षेत्रीय रोग प्रकोप निगरानी",
        "field_reports_subtitle": "कृषि विस्तार अधिकारियों के लिए वास्तविक समय महामारी निगरानी।",
        "total_scans_recorded": "कुल दर्ज स्कैन",
        "outbreak_hotspots": "प्रकोप प्रभावित क्षेत्र",
        
        # Auth
        "login_title": "किसान व अधिकारी पोर्टल",
        "login_subtitle": "अपने फसल स्वास्थ्य रिकॉर्ड और मंडी अलर्ट तक पहुंचने के लिए लॉगिन करें।",
        "mobile_or_email": "मोबाइल नंबर या ईमेल",
        "password": "पासवर्ड",
        "btn_login": "लॉगिन करें",
        "btn_signup": "नया किसान खाता बनाएं",
        "no_account": "खाता नहीं है?",
        "have_account": "पहले से खाता है?",
        "demo_farmer": "1-क्लिक किसान डेमो",
        "demo_officer": "1-क्लिक अधिकारी डेमो",
        
        # Footer
        "footer_text": "एग्री-इंटेलिजेंस प्रणाली • एआई और डेटा से किसानों का सशक्तिकरण",
        "footer_rights": "सर्वाधिकार सुरक्षित। ऑफलाइन एआई फसल सुरक्षा।"
    },
    
    "gu": {
        # Unrecognized / OOD Guard (gu)

        # Camera Scanner (gu)

        # Brand & Global
        "brand_name": "એગ્રી-ઇન્ટેલિજન્સ",
        "brand_tagline": "સ્વાયત્ત કૃષિ સલાહકાર પ્રણાલી",
        "language": "ભાષા",
        "lang_en": "English",
        "lang_hi": "हिंदी (Hindi)",
        "lang_gu": "ગુજરાતી (Gujarati)",
        "system_online": "સિસ્ટમ ચાલુ છે",
        "live_sync": "સરકારી લાઈવ સિંક",
        "search_placeholder": "પાક, રોગો, દવાઓ, APMC બજારો શોધો...",
        "view_all": "બધા જુઓ",
        "details": "વિગતો",
        "active": "સક્રિય",
        "status": "સ્થિતિ",
        "loading": "લોડ થઈ રહ્યું છે...",
        "back": "પાછા જાઓ",
        "submit": "સબમિટ કરો",
        "cancel": "રદ કરો",
        "close": "બંધ કરો",
        
        # Navigation
        "nav_dashboard": "ડેશબોર્ડ",
        "nav_crops": "પાક માર્ગદર્શિકા",
        "nav_mandi": "બજાર ભાવ",
        "nav_compare": "ખાતર/દવા સરખામણી",
        "nav_companies": "કૃષિ ભાગીદારો",
        "nav_scans": "ખેતર સ્કેન",
        "nav_reports": "ફીલ્ડ રિપોર્ટ્સ",
        "nav_login": "ખેડૂત લૉગિન",
        "nav_signup": "નોંધણી",
        "nav_logout": "લૉગ આઉટ",
        
        # Dashboard
        "dash_title": "રાષ્ટ્રીય કૃષિ ઇન્ટેલિજન્સ સેન્ટર",
        "dash_subtitle": "રીયલ-ટાઇમ પાક સર્વેલન્સ, APMC બજાર આવક અને AI રોગ નિદાન પ્રણાલી.",
        "kpi_crops": "ટ્રેક કરેલા પાક",
        "kpi_crops_sub": "મુખ્ય રોકડિયા અને ખાદ્યાન્ન પાકો",
        "kpi_mandi": "સક્રિય APMC બજારો",
        "kpi_mandi_sub": "લાઇવ ટ્રેડિંગ માર્કેટ યાર્ડ",
        "kpi_companies": "પ્રમાણિત કૃષિ ઇનપુટ્સ",
        "kpi_companies_sub": "ચકાસાયેલ જૈવિક અને રાસાયણિક ઉત્પાદનો",
        "kpi_accuracy": "AI ડાયગ્નોસ્ટિક એન્જિન",
        "kpi_accuracy_sub": "ઑફલાઇન MobileNetV2 ચોકસાઈ",
        "market_pulse": "બજાર પલ્સ (ભાવ વલણો)",
        "top_gainers": "સૌથી વધુ વધારો",
        "top_losers": "સૌથી વધુ ઘટાડો",
        "quick_actions": "ઝડપી કૃષિ સેવા કેન્દ્ર",
        "action_scan": "પાકના પાનનું સ્કેન કરો",
        "action_scan_desc": "તરત જ રોગ ઓળખો અને નિવારણ ભલામણ મેળવો.",
        "action_mandi": "આજના બજાર ભાવ જુઓ",
        "action_mandi_desc": "રાજ્યભરના માર્કેટિંગ યાર્ડના સરેરાશ અને જથ્થાબંધ ભાવ.",
        "action_compare": "ખાતર અને જંતુનાશક સરખામણી",
        "action_compare_desc": "શ્રેષ્ઠ પ્રતિ-યુનિટ ભાવ અને ગુણવત્તા શોધો.",
        "action_crops": "પાક માહિતી જુઓ",
        "action_crops_desc": "વાવણી ચક્ર, આબોહવા અને ઉત્પાદન વધારવાની કૃષિ સલાહ.",
        
        # Mandi Rates
        "mandi_title": "APMC બજાર લાઈવ ભાવ",
        "mandi_subtitle": "સમગ્ર ભારતના માર્કેટ યાર્ડના દૈનિક જથ્થાબંધ ભાવ અને આવક સ્થિતિ.",
        "filter_state": "રાજ્ય પસંદ કરો",
        "filter_district": "જિલ્લો પસંદ કરો",
        "filter_crop": "પાક પસંદ કરો",
        "all_states": "બધા રાજ્યો",
        "all_districts": "બધા જિલ્લા",
        "filter_btn": "ફિલ્ટર લાગુ કરો",
        "reset_btn": "રીસેટ કરો",
        "col_market": "બજાર / યાર્ડ",
        "col_district": "જિલ્લો / રાજ્ય",
        "col_modal_price": "સરેરાશ ભાવ (₹/ક્વિન્ટલ)",
        "col_price_range": "ભાવ મર્યાદા (ઓછામાં ઓછો - વધુમાં વધુ)",
        "col_date": "તારીખ",
        "no_mandi_data": "તમારી પસંદગી મુજબ કોઈ બજાર રેકોર્ડ મળ્યો નથી.",
        "benchmark_tag": "સરકારી બેંચમાર્ક",
        
        # Crops Guide
        "crops_title": "કૃષિ પાક માર્ગદર્શિકા",
        "crops_subtitle": "વાવણી ચક્ર, આબોહવા, સિંચાઈ અને રોગ નિયંત્રણ માર્ગદર્શન.",
        "season": "ઋતુ / મોસમ",
        "soil": "જમીનનો પ્રકાર",
        "duration": "સમયગાળો (દિવસ)",
        "water_req": "પાણીની જરૂરિયાત",
        "view_advisory": "સલાહ અને રોગો જુઓ",
        "crop_overview": "પાક રૂપરેખા",
        "sowing_period": "વાવણીનો સમય",
        "harvest_period": "કાપણીનો સમય",
        "expected_yield": "અંદાજિત ઉત્પાદન",
        "known_diseases": "મુખ્ય રોગો અને જીવાત",
        "symptoms": "લક્ષણો",
        "treatment": "ભલામણ કરેલ સારવાર",
        "prevention": "જૈવિક અટકાયત",
        "chemical_dosage": "દવાનો છંટકાવ / માત્રા",
        
        # Compare Inputs
        "compare_title": "કૃષિ ઇનપુટ ભાવ સરખામણી",
        "compare_subtitle": "પારદર્શક ભાવો, સક્રિય ઘટક સરખામણી અને પ્રતિ-યુનિટ બચત.",
        "tech_name": "ટેકનિકલ નામ / સક્રિય ઘટક",
        "brand_name_label": "બ્રાન્ડ નામ",
        "company": "ઉત્પાદક કંપની",
        "pack_size": "પેકિંગ સાઈઝ",
        "unit_price": "અસરકારક પ્રતિ યુનિટ ભાવ",
        "select_tech": "ટેકનિકલ ફોર્મ્યુલેશન પસંદ કરો",
        "best_deal": "શ્રેષ્ઠ ડીલ",
        
        # Companies
        "companies_title": "પ્રમાણિત કૃષિ ભાગીદારો",
        "companies_subtitle": "અધિકૃત ઇનપુટ ઉત્પાદકો અને કૃષિ રસાયણ સપ્લાયર્સ.",
        "company_name": "કંપનીનું નામ",
        "products_count": "નોંધાયેલ પ્રોડક્ટ્સ",
        "contact_info": "સંપર્ક અને સહાય",
        
        # Scans & Reports (AgriScan)
        "my_scans_title": "મારા ખેતરના સ્કેન અને આરોગ્ય હિસ્ટ્રી",
        "my_scans_subtitle": "તમારા ખેતરના રોગ નિદાન લૉગ્સ અને કૃષિ વૈજ્ઞાનિક ભલામણો.",
        "scan_new_leaf": "નવા પાનનું સ્કેન કરો",
        "confidence": "નિદાન સચોટતા",
        "scan_date": "સ્કેન તારીખ",
        "no_scans": "હજી સુધી કોઈ સ્કેન નોંધાયેલ નથી. પાક તપાસવા કેમેરાનો ઉપયોગ કરો.",
        "field_reports_title": "પ્રાદેશિક રોગચાળો સર્વેલન્સ",
        "field_reports_subtitle": "કૃષિ અધિકારીઓ માટે રીયલ-ટાઇમ રોગચાળો ટ્રેકિંગ.",
        "total_scans_recorded": "કુલ નોંધાયેલ સ્કેન",
        "outbreak_hotspots": "સૌથી વધુ અસરગ્રસ્ત વિસ્તારો",
        
        # Auth
        "login_title": "ખેડૂત અને અધિકારી પોર્ટલ",
        "login_subtitle": "તમારા પાક આરોગ્ય રેકોર્ડ અને બજાર એલર્ટ મેળવવા લૉગિન કરો.",
        "mobile_or_email": "મોબાઇલ નંબર અથવા ઇમેઇલ",
        "password": "પાસવર્ડ",
        "btn_login": "લૉગિન કરો",
        "btn_signup": "નવું ખેડૂત ખાતું બનાવો",
        "no_account": "ખાતું નથી?",
        "have_account": "પહેલેથી ખાતું છે?",
        "demo_farmer": "1-ક્લિક ખેડૂત ડેમો",
        "demo_officer": "1-ક્લિક અધિકારી ડેમો",
        
        # Footer
        "footer_text": "એગ્રી-ઇન્ટેલિજન્સ સિસ્ટમ • AI અને ડેટા દ્વારા ખેડૂતોનું સશક્તિકરણ",
        "footer_rights": "સર્વાધિકાર સુરક્ષિત. ઑફલાઇન AI પાક સુરક્ષા."
    }
}

AVAILABLE_LANGUAGES = [
    {"code": "en", "label": "English", "flag": "🇬🇧"},
    {"code": "hi", "label": "हिंदी", "flag": "🇮🇳"},
    {"code": "gu", "label": "ગુજરાતી", "flag": "🇮🇳"},
]

def get_translation(lang_code: str = "en") -> dict:
    """Returns the translation dictionary for the given language code, falling back to English."""
    lang = lang_code if lang_code in TRANSLATIONS else "en"
    return TRANSLATIONS[lang]
