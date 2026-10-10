/**
 * AgriScan Main Application Controller
 * Handles view switching, camera viewfinder, image capture,
 * diagnosis orchestration, voice guidance, and history rendering.
 */

const App = {
  activeView: 'view-home',
  currentStream: null,
  currentFacingMode: 'environment',
  currentDiagnosis: null,

  async init() {
    // 1. Register Service Worker for offline PWA
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js').catch(err => {
        console.warn('SW registration skipped:', err);
      });
    }

    // 2. Initialize subsystems
    await AppDB.init();
    I18N.applyTranslations();
    SyncService.init();

    // 3. Setup UI bindings
    this.setupEventListeners();

    // 4. Check initial view
    const user = Auth.getUser();
    if (!user || (!user.id && user.role !== 'guest')) {
      this.showView('view-welcome');
    } else {
      this.showView('view-home');
      this.updateUserProfileUI();
    }

    // Pre-warm model in background
    setTimeout(() => {
      ModelService.init();
    }, 1000);

    this.renderHistory();
  },

  setupEventListeners() {
    // Bottom Nav
    document.querySelectorAll('.nav-tab').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetView = btn.getAttribute('data-view');
        if (targetView) this.showView(targetView);
      });
    });

    // Language pills
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const lang = btn.getAttribute('data-lang');
        I18N.setLanguage(lang);
        if (this.currentDiagnosis) {
          this.renderResultScreen(this.currentDiagnosis);
        }
        this.renderHistory();
      });
    });
  },

  showView(viewId) {
    this.activeView = viewId;
    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const target = document.getElementById(viewId);
    if (target) {
      target.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update bottom nav active state
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.getAttribute('data-view') === viewId);
    });

    // Clean up camera stream if leaving viewfinder
    if (viewId !== 'view-capture') {
      this.stopCameraStream();
    }

    // Refresh history if entering history
    if (viewId === 'view-history') {
      this.renderHistory();
    }
  },

  updateUserProfileUI() {
    const user = Auth.getUser();
    const isGuest = !user || user.role === 'guest' || !user.id;

    // Home greeting
    const nameEl = document.getElementById('userNameDisplay');
    const badgeEl = document.getElementById('userRoleBadge');
    if (nameEl) nameEl.textContent = user.name || I18N.t('guestUser');
    if (badgeEl) badgeEl.textContent = user.role === 'officer' ? 'Officer' : (isGuest ? 'Guest' : 'Farmer');

    // Settings account card
    const setBadge = document.getElementById('settingsRoleBadge');
    const setDesc = document.getElementById('settingsUserDesc');
    const setBtn = document.getElementById('settingsAuthActionBtn');

    if (setBadge) {
      setBadge.textContent = isGuest ? 'Guest' : (user.role === 'officer' ? 'Officer' : 'Farmer');
      setBadge.style.color = isGuest ? 'var(--primary)' : '#60a5fa';
    }

    if (setDesc) {
      if (isGuest) {
        setDesc.innerHTML = `Browsing in <strong>Guest Mode</strong>. All scans are saved locally on this phone. Sign in to sync your scans across all devices.`;
      } else {
        setDesc.innerHTML = `<strong style="color: #fff; font-size: 1rem;">${user.name}</strong><br><span style="color: var(--text-dim); font-size: 0.82rem;">${user.login_id || ''} • Cloud Sync Active</span>`;
      }
    }

    if (setBtn) {
      if (isGuest) {
        setBtn.innerHTML = `
          <button class="btn-primary" onclick="App.openAuthView('login')">
            🔑 Log In / Create Account
          </button>
        `;
      } else {
        setBtn.innerHTML = `
          <button class="btn-secondary" onclick="App.handleLogout()" style="color: var(--danger); border-color: rgba(248,113,113,0.3);">
            🚪 Sign Out (${user.name})
          </button>
        `;
      }
    }
  },

  // ========================================================
  // Authentication & Guest Mode
  // ========================================================
  continueAsGuest() {
    Auth.continueAsGuest();
    this.updateUserProfileUI();
    this.showView('view-home');
  },

  openAuthView(tab = 'login') {
    this.showView('view-auth');
    this.switchAuthTab(tab);
    const offlineNotice = document.getElementById('authOfflineNotice');
    if (offlineNotice) {
      offlineNotice.style.display = navigator.onLine ? 'none' : 'block';
    }
  },

  switchAuthTab(tab) {
    const isLogin = tab === 'login';
    const tabLogin = document.getElementById('authTabLogin');
    const tabSignup = document.getElementById('authTabSignup');
    const formLogin = document.getElementById('authLoginForm');
    const formSignup = document.getElementById('authSignupForm');

    if (tabLogin && tabSignup) {
      tabLogin.style.background = isLogin ? 'var(--primary)' : 'transparent';
      tabLogin.style.color = isLogin ? '#000' : 'var(--text-dim)';
      tabSignup.style.background = !isLogin ? 'var(--primary)' : 'transparent';
      tabSignup.style.color = !isLogin ? '#000' : 'var(--text-dim)';
    }

    if (formLogin) formLogin.style.display = isLogin ? 'block' : 'none';
    if (formSignup) formSignup.style.display = !isLogin ? 'block' : 'none';
  },

  async handleLogin() {
    const loginId = document.getElementById('loginIdInput')?.value?.trim();
    const password = document.getElementById('loginPasswordInput')?.value?.trim();

    if (!loginId || !password) {
      alert("Please enter both mobile/email and password.");
      return;
    }

    if (!navigator.onLine) {
      alert("Internet required to authenticate. You can continue scanning offline as Guest.");
      return;
    }

    try {
      const user = await Auth.login(loginId, password);
      alert(`Welcome back, ${user.name}!`);
      this.updateUserProfileUI();
      this.showView('view-home');
      this.renderHistory();
    } catch(err) {
      alert(err.message || "Failed to log in.");
    }
  },

  async handleSignup() {
    const name = document.getElementById('signupNameInput')?.value?.trim();
    const loginId = document.getElementById('signupLoginIdInput')?.value?.trim();
    const password = document.getElementById('signupPasswordInput')?.value?.trim();
    const lang = document.getElementById('signupLangSelect')?.value || 'en';

    if (!name || !loginId || !password) {
      alert("Please fill in all signup fields.");
      return;
    }

    if (!navigator.onLine) {
      alert("Internet connection required to create an account. You can continue scanning as Guest.");
      return;
    }

    try {
      const user = await Auth.register(name, loginId, password, lang);
      alert(`Account created successfully! Welcome, ${user.name}.`);
      this.updateUserProfileUI();
      this.showView('view-home');
      this.renderHistory();
    } catch(err) {
      alert(err.message || "Registration failed.");
    }
  },

  handleLogout() {
    if (confirm("Sign out of your account? Local offline scans will remain saved.")) {
      Auth.logout();
      this.updateUserProfileUI();
      this.showView('view-home');
      this.renderHistory();
    }
  },

  // ========================================================
  // Camera & Capture Workflow
  // ========================================================
  async openCameraView() {
    this.showView('view-capture');
    await this.startCameraStream();
  },

  async startCameraStream() {
    this.stopCameraStream();
    const video = document.getElementById('cameraVideo');
    if (!video) return;

    try {
      const constraints = {
        video: {
          facingMode: { ideal: this.currentFacingMode },
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 }
        },
        audio: false
      };

      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch(e) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      this.currentStream = stream;
      video.srcObject = stream;
      await video.play();
    } catch(err) {
      console.warn("Camera access failed, falling back to file picker:", err);
      alert(I18N.t('offlineNotice'));
      document.getElementById('hiddenFileInput').click();
    }
  },

  stopCameraStream() {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(t => {
        try { t.stop(); } catch(e){}
      });
      this.currentStream = null;
    }
    const video = document.getElementById('cameraVideo');
    if (video) video.srcObject = null;
  },

  async flipCamera() {
    this.currentFacingMode = (this.currentFacingMode === 'environment') ? 'user' : 'environment';
    await this.startCameraStream();
  },

  captureShutter() {
    const video = document.getElementById('cameraVideo');
    if (!video || !this.currentStream) return;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    this.stopCameraStream();

    const img = new Image();
    img.onload = () => {
      this.processImage(img);
    };
    img.src = canvas.toDataURL('image/jpeg', 0.95);
  },

  handleFileSelect(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        this.processImage(img);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  },

  // ========================================================
  // On-Device AI Diagnosis Execution
  // ========================================================
  async processImage(imgElement) {
    // Show spinner
    const spinner = document.getElementById('scanSpinner');
    if (spinner) spinner.style.display = 'flex';

    try {
      const result = await ModelService.predict(imgElement);
      if (spinner) spinner.style.display = 'none';

      if (!result.isRecognized) {
        // Show Inconclusive Screen
        document.getElementById('inconclusiveReason').textContent = result.reason;
        this.showView('view-inconclusive');
        return;
      }

      this.currentDiagnosis = result;

      // 1. Save scan record locally in IndexedDB & queue in outbox
      const savedRecord = await AppDB.saveScan({
        class_key: result.class_key,
        confidence: result.confidence,
        severity: result.severity,
        crop_id: 1,
        language: I18N.currentLang,
        user_id: Auth.getUser()?.id || null
      });

      // 2. Render Result Screen
      this.renderResultScreen(result);
      this.showView('view-result');

      // 3. Trigger background sync if online
      if (navigator.onLine) {
        SyncService.syncOutboxNow();
      }

    } catch(err) {
      if (spinner) spinner.style.display = 'none';
      console.error("Diagnosis error:", err);
      alert("Error during diagnosis: " + err.message);
    }
  },

  renderResultScreen(diag) {
    const lang = I18N.currentLang;
    const adv = diag.advisory || {};

    const diseaseTitle = (adv.name && adv.name[lang]) ? adv.name[lang] : diag.class_key.replace("___", " - ").replace(/_/g, " ");
    const symptoms = (adv.symptoms && adv.symptoms[lang]) ? adv.symptoms[lang] : "Visual leaf lesions observed.";
    const prevention = (adv.prevention && adv.prevention[lang]) ? adv.prevention[lang] : "Practice crop rotation and use certified healthy seeds.";
    const treatment = (adv.treatment && adv.treatment[lang]) ? adv.treatment[lang] : "Apply approved protective fungicide if required.";

    document.getElementById('resCropName').textContent = diag.crop_name || "Crop";
    document.getElementById('resDiseaseTitle').textContent = diseaseTitle;
    document.getElementById('resConfidenceBadge').textContent = `${diag.confidence}% Match`;
    document.getElementById('resSymptoms').textContent = symptoms;
    document.getElementById('resPrevention').textContent = prevention;
    document.getElementById('resTreatment').textContent = treatment;

    // Severity pill
    const sevPill = document.getElementById('resSeverityPill');
    if (sevPill) {
      sevPill.textContent = diag.severity.toUpperCase();
      sevPill.style.background = diag.severity === 'healthy' ? 'rgba(0,255,136,0.15)' : (diag.severity === 'high' ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.15)');
      sevPill.style.color = diag.severity === 'healthy' ? '#00ff88' : (diag.severity === 'high' ? '#f87171' : '#fbbf24');
    }

    // Recommended Chemicals
    const chemBox = document.getElementById('resChemicalsBox');
    if (chemBox) {
      chemBox.innerHTML = '';
      const chemicals = adv.recommended_technical_names || ["Mancozeb 75% WP"];
      chemicals.forEach(c => {
        const badge = document.createElement('span');
        badge.style = "background: rgba(96, 165, 250, 0.15); color: #60a5fa; font-size: 0.78rem; font-weight: 700; padding: 0.25rem 0.65rem; border-radius: 8px; border: 1px solid rgba(96, 165, 250, 0.3);";
        badge.textContent = c;
        chemBox.appendChild(badge);
      });
    }
  },

  playVoiceGuidance() {
    if (!this.currentDiagnosis) return;
    const diag = this.currentDiagnosis;
    const lang = I18N.currentLang;
    const adv = diag.advisory || {};

    const diseaseTitle = (adv.name && adv.name[lang]) ? adv.name[lang] : diag.class_key;
    const treatment = (adv.treatment && adv.treatment[lang]) ? adv.treatment[lang] : "";
    const speechText = `${diseaseTitle}. ${treatment}`;

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(speechText);
      utter.lang = lang === 'hi' ? 'hi-IN' : (lang === 'gu' ? 'gu-IN' : 'en-IN');
      window.speechSynthesis.speak(utter);
    }
  },

  // ========================================================
  // History List Rendering
  // ========================================================
  async renderHistory() {
    const listContainer = document.getElementById('historyListContainer');
    if (!listContainer) return;

    const scans = await AppDB.getAllScans();
    if (!scans || scans.length === 0) {
      listContainer.innerHTML = `
        <div class="card" style="text-align: center; padding: 2.5rem 1rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🌱</div>
          <h4 style="color: #fff; margin-bottom: 0.3rem;" data-i18n="noScansYet">${I18N.t('noScansYet')}</h4>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = '';
    scans.forEach(scan => {
      const syncStatusBadge = scan.synced
        ? `<span style="color: #10b981; font-size: 0.72rem; font-weight: 800;">✅ ${I18N.t('syncedBadge')}</span>`
        : `<span style="color: #fbbf24; font-size: 0.72rem; font-weight: 800;">⏳ ${I18N.t('waitingToSync')}</span>`;

      const card = document.createElement('div');
      card.className = 'card';
      card.style = "padding: 1rem 1.2rem; margin-bottom: 0.8rem;";

      const crop = scan.class_key.split("___")[0].replace("_", " ");
      const parts = scan.class_key.split("___");
      const disease = parts.length > 1 ? parts[1].replace(/_/g, " ") : scan.class_key;

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <span style="font-size: 0.75rem; font-weight: 800; color: #cbd5e1; text-transform: uppercase;">🌿 ${crop}</span>
          ${syncStatusBadge}
        </div>
        <h4 style="color: #fff; font-size: 1.05rem; font-weight: 800; margin-bottom: 0.4rem;">${disease}</h4>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: var(--text-dim);">
          <span>Confidence: <strong style="color: var(--primary);">${scan.confidence}%</strong></span>
          <span>${scan.scanned_at}</span>
        </div>
      `;
      listContainer.appendChild(card);
    });
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();
});
