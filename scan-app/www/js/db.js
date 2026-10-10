/**
 * AgriScan Offline IndexedDB Storage Engine
 * Manages local scan history and the pending sync outbox.
 * 100% Offline Resilience (No server needed to store or retrieve)
 */

const AppDB = {
  dbName: 'agriscan_offline_db',
  dbVersion: 1,
  dbInstance: null,

  async init() {
    if (this.dbInstance) return this.dbInstance;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        // Store 1: scans (full history on phone)
        if (!db.objectStoreNames.contains('scans')) {
          const scanStore = db.createObjectStore('scans', { keyPath: 'client_uuid' });
          scanStore.createIndex('scanned_at', 'scanned_at', { unique: false });
          scanStore.createIndex('synced', 'synced', { unique: false });
          scanStore.createIndex('user_id', 'user_id', { unique: false });
        }
        // Store 2: outbox (pending upload queue)
        if (!db.objectStoreNames.contains('outbox')) {
          const outboxStore = db.createObjectStore('outbox', { keyPath: 'client_uuid' });
          outboxStore.createIndex('created_at', 'created_at', { unique: false });
        }
      };

      request.onsuccess = (event) => {
        this.dbInstance = event.target.result;
        console.log("🗄️ IndexedDB initialized successfully!");
        resolve(this.dbInstance);
      };

      request.onerror = (event) => {
        console.error("IndexedDB error:", event.target.error);
        reject(event.target.error);
      };
    });
  },

  async saveScan(scan) {
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(['scans', 'outbox'], 'readwrite');
      const scanStore = tx.objectStore('scans');
      const outboxStore = tx.objectStore('outbox');

      // Default fields
      const record = {
        client_uuid: scan.client_uuid || ('scan_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6)),
        class_key: scan.class_key,
        crop_id: scan.crop_id || 1,
        confidence: parseFloat(scan.confidence || 0),
        severity: scan.severity || (scan.confidence > 85 ? 'high' : 'medium'),
        language: scan.language || I18N.currentLang,
        scanned_at: scan.scanned_at || new Date().toISOString().replace('T', ' ').substr(0, 19),
        user_id: scan.user_id || null,
        device_id: scan.device_id || Auth.getDeviceId(),
        synced: false
      };

      scanStore.put(record);
      outboxStore.put({
        client_uuid: record.client_uuid,
        payload: record,
        created_at: Date.now()
      });

      tx.oncomplete = () => {
        console.log("✅ Scan saved locally in IndexedDB & queued in outbox:", record.client_uuid);
        resolve(record);
      };
      tx.onerror = () => reject(tx.error);
    });
  },

  async getAllScans() {
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('scans', 'readonly');
      const store = tx.objectStore('scans');
      const request = store.getAll();

      request.onsuccess = () => {
        const scans = request.result || [];
        // Sort descending by scanned_at
        scans.sort((a, b) => new Date(b.scanned_at) - new Date(a.scanned_at));
        resolve(scans);
      };
      request.onerror = () => reject(request.error);
    });
  },

  async getPendingOutbox() {
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('outbox', 'readonly');
      const store = tx.objectStore('outbox');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  },

  async markScanSynced(client_uuid) {
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(['scans', 'outbox'], 'readwrite');
      const scanStore = tx.objectStore('scans');
      const outboxStore = tx.objectStore('outbox');

      const getReq = scanStore.get(client_uuid);
      getReq.onsuccess = () => {
        if (getReq.result) {
          const updated = getReq.result;
          updated.synced = true;
          scanStore.put(updated);
        }
      };

      outboxStore.delete(client_uuid);

      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error);
    });
  },

  async clearAll() {
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(['scans', 'outbox'], 'readwrite');
      tx.objectStore('scans').clear();
      tx.objectStore('outbox').clear();
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error);
    });
  }
};
