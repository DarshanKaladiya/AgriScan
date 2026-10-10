/**
 * AgriScan Background Outbox Sync Service
 * Implements the Outbox Pattern: local changes queue up when offline,
 * and automatically upload when connectivity returns.
 */

const SyncService = {
  isSyncing: false,
  get apiBase() {
    if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== '127.0.0.1' && window.location.hostname !== 'localhost') {
      return `${window.location.protocol}//${window.location.hostname}:8001/api`;
    }
    return 'http://127.0.0.1:8001/api';
  },

  init() {
    window.addEventListener('online', () => {
      console.log("🌐 Network online detected! Triggering auto-sync...");
      this.updateNetworkBadge(true);
      this.syncOutboxNow();
    });

    window.addEventListener('offline', () => {
      console.log("📡 Network offline detected.");
      this.updateNetworkBadge(false);
    });

    this.updateNetworkBadge(navigator.onLine);

    // Initial check on launch
    setTimeout(() => {
      if (navigator.onLine) this.syncOutboxNow();
    }, 2000);
  },

  updateNetworkBadge(isOnline) {
    const badge = document.getElementById('networkStatusPill');
    if (!badge) return;
    if (isOnline) {
      badge.className = 'status-pill pill-online';
      badge.innerHTML = `<span class="dot-live"></span> <span data-i18n="onlineMode">${I18N.t('onlineMode')}</span>`;
    } else {
      badge.className = 'status-pill pill-offline';
      badge.innerHTML = `<span class="dot-offline"></span> <span data-i18n="offlineMode">${I18N.t('offlineMode')}</span>`;
    }
  },

  async syncOutboxNow() {
    if (this.isSyncing) return;
    if (!navigator.onLine) {
      this.updateOutboxCounter();
      return;
    }

    try {
      this.isSyncing = true;
      const pending = await AppDB.getPendingOutbox();
      if (!pending || pending.length === 0) {
        console.log("Outbox empty. Nothing to sync.");
        this.updateOutboxCounter();
        return;
      }

      console.log(`🚀 Uploading ${pending.length} pending scans to server...`);
      const token = Auth.getToken();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const payload = {
        scans: pending.map(item => ({
          client_uuid: item.client_uuid,
          class_key: item.payload.class_key,
          crop_id: item.payload.crop_id || 1,
          confidence: parseFloat(item.payload.confidence),
          language: item.payload.language || 'en',
          scanned_at: item.payload.scanned_at,
          user_id: Auth.getUser()?.id || null,
          device_id: Auth.getDeviceId(),
          location: { region: "Gujarat, India" }
        }))
      };

      const res = await fetch(`${this.apiBase}/scans/sync`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const result = await res.json();
        console.log("✅ Sync confirmed by backend:", result);
        for (const item of pending) {
          await AppDB.markScanSynced(item.client_uuid);
        }
        if (window.App && App.renderHistory) {
          App.renderHistory();
        }
      } else {
        console.warn("Backend rejected sync payload:", res.status);
      }
    } catch(err) {
      console.warn("Outbox sync attempt failed (will retry):", err);
    } finally {
      this.isSyncing = false;
      this.updateOutboxCounter();
    }
  },

  async updateOutboxCounter() {
    try {
      const pending = await AppDB.getPendingOutbox();
      const countEl = document.getElementById('pendingSyncCount');
      const banner = document.getElementById('outboxBanner');
      if (countEl) countEl.innerText = pending.length;
      if (banner) {
        banner.style.display = pending.length > 0 ? 'flex' : 'none';
      }
    } catch(e){}
  }
};
