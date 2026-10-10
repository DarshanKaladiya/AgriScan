/**
 * AgriScan Offline Multilingual Translation Catalog
 * Languages: English (en), Hindi (hi), Gujarati (gu)
 * 100% Offline Accessible
 */

const I18N = {
  currentLang: localStorage.getItem('agriscan_lang') || 'en',

  translations: {
    en: {
      appName: "AgriScan",
      tagline: "Offline AI Crop Doctor",
      offlineMode: "Offline Mode",
      onlineMode: "Online Sync Ready",
      scanLeaf: "Scan a Crop Leaf",
      scanSub: "Snap or pick a leaf photo for instant offline diagnosis",
      takePhoto: "Open Live Camera",
      chooseGallery: "Choose from Gallery",
      recentScans: "Field Scan History",
      noScansYet: "No scans recorded yet. Diagnose your first leaf above!",
      waitingToSync: "Waiting to sync",
      syncedBadge: "Cloud Synced",
      diagnosticConfidence: "AI Confidence",
      symptoms: "Visual Symptoms",
      prevention: "Organic Prevention",
      treatment: "Recommended Treatment",
      activeChemicals: "Active Formulations",
      listenVoice: "Listen Spoken Advice",
      safetyNote: "Safety Advisory: Always wear protective gear when applying chemicals.",
      retakeScan: "Scan Another Leaf",
      inconclusiveTitle: "Inconclusive Scan / Unrecognized",
      inconclusiveDesc: "The photo does not match supported crop diseases (Corn, Potato, Tomato) or is not a clear plant leaf.",
      tip1: "Scan only supported crops: Corn (Maize), Potato, Tomato.",
      tip2: "Hold camera 10–20 cm away with good daylight.",
      tip3: "Avoid fingers, people, backgrounds, or blurry shots.",
      guestUser: "Guest Farmer",
      login: "Sign In",
      signup: "Create Account",
      guestModeBtn: "Continue as Guest",
      guestModeNotice: "Scanning works 100% offline without an account.",
      name: "Your Name",
      phoneOrEmail: "Mobile Number or Email",
      password: "Password",
      syncNow: "Sync Outbox Now",
      syncSuccess: "Outbox successfully synced with cloud!",
      syncNone: "All scans are already synced.",
      offlineNotice: "You are currently offline. Local features work normally.",
      logout: "Sign Out",
      settings: "Settings & Cloud Sync",
      selectLanguage: "Language / ભાષા / भाषा",
      helpline: "Kisan Call Center: 1800-180-1551"
    },
    hi: {
      appName: "AgriScan",
      tagline: "ऑफलाइन AI फसल डॉक्टर",
      offlineMode: "ऑफलाइन मोड",
      onlineMode: "ऑनलाइन सिंक तैयार",
      scanLeaf: "फसल की पत्ती स्कैन करें",
      scanSub: "तुरंत ऑफलाइन बीमारी जांच के लिए पत्ती का फोटो लें",
      takePhoto: "लाइव कैमरा खोलें",
      chooseGallery: "गैलरी से फोटो चुनें",
      recentScans: "खेत स्कैन इतिहास",
      noScansYet: "अभी तक कोई स्कैन नहीं। पहली पत्ती की जांच ऊपर से करें!",
      waitingToSync: "सिंक की प्रतीक्षा में",
      syncedBadge: "क्लाउड सिंक पूर्ण",
      diagnosticConfidence: "जांच सटीकता (AI)",
      symptoms: "लक्षण",
      prevention: "जैविक बचाव",
      treatment: "अनुशंसित रासायनिक उपचार",
      activeChemicals: "सक्रिय दवा घटक",
      listenVoice: "सलाह आवाज में सुनें",
      safetyNote: "सुरक्षा सलाह: दवा छिड़काव के समय हमेशा मास्क और दस्ताने पहनें।",
      retakeScan: "दूसरी पत्ती स्कैन करें",
      inconclusiveTitle: "अमान्य या अज्ञात फोटो / पत्ती नहीं मिली",
      inconclusiveDesc: "यह फोटो AgriScan डेटाबेस (मक्का, आलू, टमाटर) से मेल नहीं खाती या अस्पष्ट है।",
      tip1: "केवल समर्थित फसलें स्कैन करें: मक्का, आलू या टमाटर।",
      tip2: "अच्छी रोशनी में 10-20 सेमी दूरी से फोटो लें।",
      tip3: "उंगलियां, अन्य वस्तुएं या धुंधली फोटो से बचें।",
      guestUser: "अतिथि किसान (गेस्ट)",
      login: "लॉग इन करें",
      signup: "नया खाता बनाएं",
      guestModeBtn: "बिना खाते के आगे बढ़ें",
      guestModeNotice: "स्कैनिंग बिना खाते के 100% ऑफलाइन काम करती है।",
      name: "आपका नाम",
      phoneOrEmail: "मोबाइल नंबर या ईमेल",
      password: "पासवर्ड",
      syncNow: "अभी सिंक करें",
      syncSuccess: "सभी स्कैन सफलतापूर्वक क्लाउड पर सिंक हो गए!",
      syncNone: "सभी स्कैन पहले से सिंक हैं।",
      offlineNotice: "आप अभी ऑफलाइन हैं। सभी मुख्य कार्य सामान्य रूप से काम कर रहे हैं।",
      logout: "लॉग आउट करें",
      settings: "सेटिंग्स और क्लाउड सिंक",
      selectLanguage: "भाषा / Language",
      helpline: "किसान कॉल सेंटर: 1800-180-1551"
    },
    gu: {
      appName: "AgriScan",
      tagline: "ઑફલાઇન AI પાક ડૉક્ટર",
      offlineMode: "ઑફલાઇન મોડ",
      onlineMode: "ઑનલાઇન સિંક તૈયાર",
      scanLeaf: "પાકનું પાન સ્કેન કરો",
      scanSub: "તરત જ ઑફલાઇન રોગ નિદાન માટે પાનનો ફોટો લો",
      takePhoto: "લાઇવ કૅમેરો ખોલો",
      chooseGallery: "ગેલેરીમાંથી ફોટો પસંદ કરો",
      recentScans: "ખેતર સ્કેન હિસ્ટ્રી",
      noScansYet: "હજુ સુધી કોઈ સ્કેન નોંધાયેલ નથી. ઉપરથી પહેલું પાન તપાસો!",
      waitingToSync: "સિંકની રાહમાં",
      syncedBadge: "ક્લાઉડ સિંક સફળ",
      diagnosticConfidence: "નિદાન ચોકસાઈ (AI)",
      symptoms: "રોગના લક્ષણો",
      prevention: "કુદરતી/જૈવિક ઉપાય",
      treatment: "ભલામણ કરેલ દવા અને સારવાર",
      activeChemicals: "મુખ્ય દવા ઘટકો",
      listenVoice: "માર્ગદર્શન અવાજમાં સાંભળો",
      safetyNote: "સાવચેતી: દવા છાંટતી વખતે હંમેશા માસ્ક અને મોજા પહેરો.",
      retakeScan: "બીજું પાન સ્કેન કરો",
      inconclusiveTitle: "અમાન્ય અથવા અજાણ્યો ફોટો / પાન મળ્યું નથી",
      inconclusiveDesc: "આ ફોટો માન્ય પાક (મકાઈ, બટાકા, ટામેટા) સાથે મેળ ખાતો નથી અથવા અસ્પષ્ટ છે.",
      tip1: "ફક્ત માન્ય પાકના પાન સ્કેન કરો: મકાઈ, બટાકા અથવા ટામેટા.",
      tip2: "સારા અજવાળામાં 10-20 સેમી અંતરેથી ફોટો લો.",
      tip3: "આંગળીઓ, બીજી વસ્તુઓ કે ધૂંધળા ફોટા ટાળો.",
      guestUser: "અતિથિ ખેડૂત (ગેસ્ટ)",
      login: "લૉગ ઇન કરો",
      signup: "નવું ખાતું બનાવો",
      guestModeBtn: "ખાતા વગર આગળ વધો",
      guestModeNotice: "સ્કેનિંગ ખાતા વગર પણ 100% ઑફલાઇન કામ કરે છે.",
      name: "તમારું નામ",
      phoneOrEmail: "મોબાઇલ નંબર અથવા ઇમેઇલ",
      password: "પાસવર્ડ",
      syncNow: "હમણાં સિંક કરો",
      syncSuccess: "બધા સ્કેન સફળતાપૂર્વક ક્લાઉડ પર સિંક થઈ ગયા!",
      syncNone: "બધા સ્કેન પહેલેથી જ સિંક છે.",
      offlineNotice: "તમે અત્યારે ઑફલાઇન છો. મુખ્ય તમામ સુવિધાઓ સામાન્ય રીતે કામ કરે છે.",
      logout: "લૉગ આઉટ કરો",
      settings: "સેટિંગ્સ અને ક્લાઉડ સિંક",
      selectLanguage: "ભાષા / Language",
      helpline: "કિસાન કૉલ સેન્ટર: 1800-180-1551"
    }
  },

  t(key) {
    const lang = this.currentLang;
    if (this.translations[lang] && this.translations[lang][key]) {
      return this.translations[lang][key];
    }
    return this.translations['en'][key] || key;
  },

  setLanguage(lang) {
    if (['en', 'hi', 'gu'].includes(lang)) {
      this.currentLang = lang;
      localStorage.setItem('agriscan_lang', lang);
      this.applyTranslations();
    }
  },

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = this.t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      el.setAttribute('placeholder', this.t(key));
    });
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === this.currentLang);
    });
  }
};
