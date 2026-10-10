/**
 * AgriScan Offline Authentication & Guest Mode Controller
 * Core diagnostic scanning works 100% without an account (Guest Mode).
 * Offline-first: login token and profile cached on phone.
 */

const Auth = {
  get apiBase() {
    if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
      return `${window.location.protocol}//${window.location.hostname}:8001/api`;
    }
    return 'http://127.0.0.1:8001/api';
  },

  getDeviceId() {
    let devId = localStorage.getItem('agriscan_device_id');
    if (!devId) {
      devId = 'dev_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 8);
      localStorage.setItem('agriscan_device_id', devId);
    }
    return devId;
  },

  getUser() {
    try {
      const u = localStorage.getItem('agriscan_user');
      if (u) return JSON.parse(u);
    } catch(e){}
    return { name: I18N.t('guestUser'), role: 'guest', id: null };
  },

  getToken() {
    return localStorage.getItem('agriscan_token') || null;
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  continueAsGuest() {
    localStorage.removeItem('agriscan_token');
    localStorage.setItem('agriscan_user', JSON.stringify({ name: I18N.t('guestUser'), role: 'guest', id: null }));
    return this.getUser();
  },

  async login(login_id, password) {
    if (!navigator.onLine) {
      throw new Error(I18N.t('offlineNotice'));
    }

    const res = await fetch(`${this.apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id, password })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Invalid mobile number or password.");
    }

    const data = await res.json();
    localStorage.setItem('agriscan_token', data.token);
    localStorage.setItem('agriscan_user', JSON.stringify(data.user));
    if (data.user.preferred_language) {
      I18N.setLanguage(data.user.preferred_language);
    }
    console.log("Logged in:", data.user);
    // Trigger sync
    if (window.SyncService) SyncService.syncOutboxNow();
    return data.user;
  },

  async register(name, login_id, password, preferred_language = 'en') {
    if (!navigator.onLine) {
      throw new Error(I18N.t('offlineNotice'));
    }

    const res = await fetch(`${this.apiBase}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, login_id, password, preferred_language })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Could not register account.");
    }

    const data = await res.json();
    localStorage.setItem('agriscan_token', data.token);
    localStorage.setItem('agriscan_user', JSON.stringify(data.user));
    I18N.setLanguage(preferred_language);
    return data.user;
  },

  logout() {
    localStorage.removeItem('agriscan_token');
    this.continueAsGuest();
  }
};
