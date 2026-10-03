# AgriScan: Project Change Plan

**Offline Crop Disease and Pest Detection and Advisory for Farmers**
Hackathon build plan: converting the current *AgriIntelligence* project into a problem-statement-ready product.

| | |
|---|---|
| **Project** | AgriScan (current codebase: `AgriScan/`, Django + FastAPI) |
| **Problem statement** | Offline-first mobile/web solution to identify crop diseases and pests from leaf images, with farmer-friendly advice, local-language support and low-end device support |
| **Target stack** | HTML, CSS, JS, Python (FastAPI + Django), MongoDB, bcrypt + JWT login, TensorFlow / TensorFlow.js, Capacitor (Android) |
| **Time available** | 10 days |
| **Document purpose** | Explain what the project is today, what the problem statement requires, and exactly what must change |

---

## 1. Executive summary

The current project is an **online agricultural market-intelligence platform**: crop guide, mandi prices, input-product comparison and a market dashboard. It works only when the server and internet are available, and it contains **no AI**.

The problem statement asks for something different: a **farmer-facing, offline-first app that diagnoses crop disease from a leaf photo**, explains prevention and treatment in simple local-language text, and runs on cheap phones.

**Strategy: keep the project as the online backbone, and add an offline scanning app on top of it.**

- The existing Django + FastAPI system becomes the **online side**: it stores knowledge, receives synced scans and shows field reports.
- **Login and signup** (backend, mobile app and website) give each farmer an account and a personal scan history, while a **guest mode** keeps the core scanning feature usable with no account at all.
- A new **mobile app** (Android, built with Capacitor) becomes the **offline side**: it contains the AI model, the advice text, and a local history, all stored on the phone.
- The database moves from **MySQL to MongoDB**, which suits flexible, multilingual disease documents and the hackathon's stated technology list.

The one-sentence pitch: **the intelligence travels with the phone, and only the reports travel over the network.**

---

## 2. Problem statement and what it requires

> Develop an offline-first mobile or web solution that helps farmers identify crop diseases and pest infestations using crop/leaf images, even in areas with limited or no internet connectivity. The system should provide quick disease/pest identification, preventive measures, and practical treatment recommendations in a simple, farmer-friendly format, with support for local languages and low-end devices.

| # | Requirement | What it means in practice |
|---|---|---|
| R1 | Offline-first | Core features work in airplane mode, from the very first launch |
| R2 | Image-based identification | A trained model classifies a leaf photo on the device |
| R3 | Disease **and pest** coverage | At least a credible disease set; pests as a bounded extension |
| R4 | Prevention and treatment advice | Short, practical, safe guidance for each result |
| R5 | Farmer-friendly format | Large text, icons, simple sentences, audio, few screens |
| R6 | Local languages | English plus Hindi and Gujarati (minimum), switchable offline |
| R7 | Low-end devices | Small model, light UI, no heavy dependencies, tested on a cheap phone |

---

## 3. Current project: what exists today

### 3.1 Architecture

```
Browser ──▶ Django (views, templates, port 8001) ──▶ FastAPI (api_main.py, port 8000) ──▶ MySQL
                                                              └──▶ data.gov.in (Agmarknet prices)
```

### 3.2 Features

| Area | Current state |
|---|---|
| Dashboard | Market stats, market pulse (gainers/losers), crop and company counts |
| Crop Guide | List and detail pages from `master_crops` and `crop_advisories` |
| Mandi Prices | Live government API with database cache and benchmark fallback |
| Product Insights | Seeds, fertilizers, pesticides, fungicides; compare by technical name and price per unit |
| Agri Networks | Company directory |
| UI | Dark glassmorphism theme, Lucide icons and Google Fonts loaded from CDNs |
| Database | MySQL (`schema.sql` with seed data), plus an unused Django `db.sqlite3` |

### 3.3 Gap analysis against the problem statement

| Requirement | Status | Gap |
|---|---|---|
| R1 Offline-first | **Missing** | Every page needs the server and the database on each load |
| R2 Image identification | **Missing** | No upload, no model, no inference |
| R3 Disease/pest coverage | **Missing** | No disease or pest data at all |
| R4 Prevention and treatment | **Partial** | `crop_advisories` covers crop-stage advice, not disease treatment. `input_products` has fungicides and pesticides that can be linked to diseases |
| R5 Farmer-friendly | **Partial** | Polished but dense, English-only, effects-heavy |
| R6 Local languages | **Missing** | English only |
| R7 Low-end devices | **Missing** | Blur effects, CDN assets, no mobile app |
| Mobile access | **Missing** | Website only |
| Authentication | **Missing** | No signup, login or user accounts, so scans cannot belong to a person and no page can be protected |

### 3.4 What is reusable

- The **FastAPI + Django split**: it becomes the sync, authentication and reporting backend.
- The **crop master data** (10 crops, icons) and the **fungicide/pesticide product data**.
- The **visual identity** (green and dark palette), simplified for the mobile app.
- The **resilience patterns** already added: request timeouts, benchmark fallback when the database is down.

---

## 4. Target solution

### 4.1 Architecture

```
┌────────────────────────── FARMER'S PHONE (OFFLINE) ──────────────────────────┐
│  AgriScan Android app (Capacitor, HTML/CSS/JS)                                │
│   ├─ Camera / gallery picker                                                  │
│   ├─ TensorFlow.js model  (bundled in the app)  ──▶ disease prediction        │
│   ├─ advisory.json  (multilingual advice, bundled)                            │
│   ├─ audio clips  (bundled)                                                   │
│   ├─ IndexedDB: scan history + outbox (pending uploads) + cached API data     │
│   └─ Auth token (saved after the first online login)                          │
└──────────────────────────────────┬────────────────────────────────────────────┘
                                   │ only when internet is available
                                   ▼  (sync scans, refresh cached data, login)
┌────────────────────────── ONLINE BACKEND ─────────────────────────────────────┐
│  FastAPI  ──▶  MongoDB   (users, crops, diseases, scans, prices, products)    │
│  Django website: Crop Guide, Mandi, Products, and NEW Field Reports dashboard │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Design principles

1. **The server is never required for the core job.** Scanning, advice, language switching and history all work with no network.
2. **Read from local storage first; sync in the background.** Screens never wait on the server.
3. **Writes go through an outbox.** Save locally, show success instantly, upload later, mark synced only after the server confirms.
4. **Be honest about uncertainty.** Low-confidence results say "not sure, retake the photo" instead of guessing.
5. **Scope small, finish completely.** A narrow, well-tested model beats a broad, unreliable one.

### 4.3 Scope decisions

| Decision | Choice | Reason |
|---|---|---|
| Crops for the model | Tomato, Potato, Maize (about 15 to 17 classes with "healthy") | All have strong public datasets; the project already has their icons |
| Extra class | `Unknown / not a leaf` | Prevents confident nonsense on non-leaf photos |
| Pests | **Stretch goal** (3 to 5 pests, one crop) | Different dataset and image style; do only after diseases work end to end |
| Languages | English, Hindi, Gujarati | Gujarati suits the local context; translations must be checked by a native speaker |
| Platform | Android first (APK) | iOS needs a Mac; web/PWA remains a fallback |
| Mobile approach | Capacitor wrapping the web app | One codebase, reuses HTML/CSS/JS skills, model ships inside the APK |
| Accounts | Login with **mobile number or email** plus password, and a guest mode | Many farmers use a phone number more than email; password login needs no paid SMS service; guest mode means the core feature never depends on an account |

---

## 5. Required changes, by area

### 5.1 Database: MySQL to MongoDB

**Why:** disease advice is naturally nested and multilingual (one document holds English, Hindi and Gujarati text together), and MongoDB is on the hackathon's allowed technology list.

**Status:** conversion of `api_main.py` and `government_api.py` is drafted. `db_utils.py` (with the `get_db()` and `db_is_up()` helpers), the migration script and the updated `requirements.txt` still need to be completed and tested. See Section 8.

**Collections**

| Collection | Source | Notes |
|---|---|---|
| `master_crops` | migrated | Keep the numeric `id` so Django URLs like `/crop/5/` keep working |
| `companies` | migrated | |
| `input_products` | migrated | `brand_name` stored inside each product, so no join is needed |
| `crop_advisories` | migrated | |
| `mandi_prices` | migrated | Unique on (`mandi_name`, `crop_id`, `price_date`); dates stored as `YYYY-MM-DD` text |
| `counters` | new | Replaces MySQL `AUTO_INCREMENT` for new records |
| `disease_info` | **new** | Disease and pest knowledge, multilingual |
| `scans` | **new** | Scan history uploaded from phones |
| `users` | **new** | Accounts for signup and login (Section 5.7) |

**Example `disease_info` document**

```json
{
  "class_key": "Tomato___Early_blight",
  "crop_id": 6,
  "kind": "Disease",
  "name":       { "en": "Early Blight", "hi": "अगेती झुलसा", "gu": "વહેલો સુકારો" },
  "symptoms":   { "en": "Brown spots with rings on older leaves.", "hi": "...", "gu": "..." },
  "prevention": { "en": "Rotate crops. Avoid wetting leaves.", "hi": "...", "gu": "..." },
  "treatment":  { "en": "Remove infected leaves. Spray a copper-based fungicide.", "hi": "...", "gu": "..." },
  "recommended_technical_names": ["Mancozeb 75% WP"],
  "severity": "medium",
  "audio": { "en": "audio/en/tomato_early_blight.mp3", "hi": "...", "gu": "..." }
}
```

> **Critical rule:** `class_key` must match the model's class names **exactly** (the same text as the training folder names). A mismatch breaks the result lookup.

**Example `scans` document**

```json
{
  "client_uuid": "b1f3...e9",
  "user_id": null,
  "device_id": "7c2a...41",
  "class_key": "Tomato___Early_blight",
  "confidence": 91.4,
  "language": "hi",
  "location": { "lat": 23.25, "lng": 69.66 },
  "scanned_at": "2026-10-10T08:15:00Z",
  "synced_at": "2026-10-10T18:02:11Z"
}
```

The phone creates `client_uuid`. A unique index on it means a retried upload can never create duplicates. `user_id` is `null` for guest scans; `device_id` is a random ID the app creates on first launch, so guest scans can later be attached to an account.

**Example `users` document**

```json
{
  "name": "Ramesh Patel",
  "login_id": "9876543210",
  "password_hash": "$2b$12$...",
  "role": "farmer",
  "preferred_language": "gu",
  "created_at": "2026-10-10T07:40:00Z",
  "last_login": "2026-10-10T07:40:00Z"
}
```

`login_id` holds either a mobile number or an email, stored normalised (emails lower-cased), with a **unique index**. `role` is `farmer` by default; `officer` accounts are created only by seeding, never by public signup.

### 5.2 Backend (FastAPI)

**Keep:** crops, advisories, mandi, market pulse, companies, compare, government-data sync.

**Add:**

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Confirms the database is reachable |
| `POST /api/auth/register` | Signup: validates input, hashes the password, creates the account, returns a token and profile |
| `POST /api/auth/login` | Login: checks credentials, returns a token and profile |
| `GET /api/auth/me` | Returns the current user from the token; used to confirm a saved token is still valid |
| `GET /api/advisory` | Full disease/advice export, used to build the app bundle and to refresh when online |
| `POST /api/scans/sync` | Accepts a batch of scans (with the token if logged in, anonymous guest scans allowed), inserts them idempotently by `client_uuid` |
| `GET /api/scans/mine` | The logged-in user's own scan history (for the My Scans page and for restoring history on a new phone) |
| `GET /api/scans/stats` | Counts by disease, crop and date for the Field Reports dashboard (officer role only) |

**Improve:**

- Authentication follows Section 5.7: bcrypt password hashing, signed tokens, no plain-text passwords. Put the helpers in a separate `auth_utils.py`.
- Restrict CORS to known origins before any real deployment (currently `*`).
- Use parameterised or validated inputs only; validate the sync payload with Pydantic models.

### 5.3 AI / machine learning (new)

| Step | Detail |
|---|---|
| Data | PlantVillage (clean, large) for the main training set; PlantDoc and your own phone photos for real-world robustness; an `Unknown` class of non-leaf images |
| Model | MobileNetV2 transfer learning, two phases (train the new top layer, then fine-tune gently) |
| Training aids | Strong augmentation, label smoothing, class weights, early stopping |
| Evaluation | Per-class report and confusion matrix, plus a **separate real-world test set** that the model never trains on. That number is the honest accuracy to quote |
| Export | Save `labels.json` in training order, convert to TensorFlow.js |
| Size and speed | Quantize (float16) and measure seconds per scan on a low-end phone |
| Freeze date | **End of Day 4.** No further retraining after that unless something is seriously wrong |

Notes that avoid common failures:

- A model converted from a SavedModel is a **graph model**: load it with `tf.loadGraphModel(...)`, not `loadLayersModel`.
- The model rescales pixels internally, so the app must pass **raw 0 to 255 pixel values** and must not divide by 255 again.
- Verify that Python and the phone give nearly the same probabilities for the same image.
- Validation accuracy on lab-style datasets overstates field performance. State this limitation openly.
- Tool versions in Colab (TensorFlow, Keras, tensorflowjs) can clash; test the export on Day 1 with a tiny model.

### 5.4 Mobile app (new): `scan-app/`

Built as plain HTML/CSS/JS (lightest for low-end phones) and wrapped with Capacitor.

**Screens (keep the flow shallow)**

1. **Welcome (first launch only):** "Continue as guest", "Log in", "Sign up".
2. **Login / Signup:** simple forms (name, mobile number or email, password, preferred language), in the user's language.
3. **Home:** big "Scan a leaf" button, language selector, online/offline indicator.
4. **Capture:** camera or gallery, with a tip ("one leaf, fill the frame, daylight").
5. **Result:** disease name, confidence, symptoms, prevention, treatment, recommended products, audio play button, safety note.
6. **History:** past scans with a "waiting to sync" mark.
7. **Account / Settings:** profile, language, manual sync, log out (guests see "Create an account" instead).

**Plugins:** `@capacitor/camera`, `@capacitor/network`, `@capacitor/preferences` (token storage).

**Farmer-friendly rules**

- Large touch targets, high contrast, short sentences, icon plus text for every action.
- Audio for each result, bundled in the app, because literacy varies.
- Drop heavy effects (blur, glow) that slow cheap phones.
- A visible safety note: wear gloves and follow the pesticide label.
- Low confidence shows "Not sure. Retake the photo," with an option to contact an expert. Verify any helpline number before printing it.

### 5.5 Offline architecture (how it works)

| Need | Where it lives on the phone |
|---|---|
| App screens and logic | Inside the APK (`www/`) |
| AI model and `labels.json` | Inside the APK |
| Advice text and audio | Inside the APK |
| Scan history | IndexedDB |
| Login token | Capacitor Preferences |
| Last-fetched server data | IndexedDB cache with a timestamp |

**Four types of API call, four strategies**

| Type | Example | Strategy |
|---|---|---|
| Stable reference data | Disease advice, crop list | Bundle in the app; refresh when online |
| Changing data | Mandi prices, reports | Cache the last response; show "last updated" |
| User-created data | Scans | **Outbox pattern:** save locally, queue, sync later |
| Needs the server | Register, first login | Requires internet; offer **guest mode** so the core feature never needs an account |

**Sync rules:** the phone generates unique IDs; items are sent one by one; an item is marked synced only after the server confirms; failed syncs are silent and retried when the network returns; requests use a timeout so a weak connection does not freeze the app.

**Hard rules**

- No CDN links anywhere in the app (icons, fonts, libraries are all bundled).
- Prediction runs **on the device**. Sending the image to a server would make it an online app that only looks offline.
- Always test in **airplane mode on a real phone**.

### 5.6 Web (Django): changes

| File | Change |
|---|---|
| `core/views.py` | Read `API_URL` from the environment instead of hard-coding `localhost`. Add views for signup, login, logout, My Scans and Field Reports |
| `agri_dashboard/urls.py` | Add `login/`, `signup/`, `logout/`, `my-scans/` and `field-reports/` |
| `core/templates/base.html` | New branding (AgriScan). Navigation: **Crop Guide, My Scans, Field Reports, More** (mandi, products, networks under "More"). Show **Log in / Sign up** for visitors, and the user's name with **Log out** when signed in. Add a "Get the app" button |
| `core/templates/dashboard.html` | New hero focused on disease detection, "Get the app" call to action, scan and disease statistics |
| `core/templates/login.html`, `signup.html` | **New:** simple forms that match the dark theme |
| `core/templates/my_scans.html` | **New:** the signed-in user's own scan history |
| `core/templates/field_reports.html` | **New:** table and charts of synced scans by disease, crop and date (officer role) |
| `crop_detail.html` | Add a "Common diseases" section linked to `disease_info` |
| `compare.html` | Reuse it for "Recommended products" after a diagnosis |
| `db.sqlite3` | Keep it. Django uses it for **sessions**, which now hold the signed-in user (see 5.7) |

Run the API on port **8000** and Django on **8001** (`python manage.py runserver 8001`), because both default to 8000.

### 5.7 Authentication: login and signup

#### Goals

- Every farmer can have **one account that works in the mobile app and on the website**, with their own scan history.
- The core feature (scan a leaf, get advice) **never requires an account**. Guest mode is always available.
- Login works in low-connectivity conditions: the network is needed **once** to sign up or log in, never to reopen the app.

#### User journeys

| Journey | What happens |
|---|---|
| **Sign up (online)** | The farmer enters name, mobile number or email, password and language. The server validates, hashes the password, creates the account and returns a token. The app saves the token and profile on the phone |
| **Log in (online)** | The farmer enters mobile number or email and password. On success, the token and profile are saved on the phone |
| **Reopen the app (offline)** | The app finds the saved token and opens straight away. **No network call is needed.** When online later, it quietly checks the token with `GET /api/auth/me` |
| **Continue as guest** | All core features work. Scans are saved on the phone with `user_id = null` and the app's `device_id` |
| **Guest becomes a user** | After signup or login, the app offers to attach earlier guest scans to the account, then syncs them |
| **Try to sign up offline** | A clear message: "You need internet to create an account. You can continue as a guest." |
| **Token expires or is rejected** | The app asks the user to log in again **without deleting local scans** |
| **Log out** | The token is removed from the phone. The app offers to keep or clear local history (useful on shared phones) |

#### Backend design

- **Passwords:** hash with `bcrypt`. Never store, log or return plain passwords or hashes.
- **Tokens:** signed JWTs created with `PyJWT`, using a long random `JWT_SECRET` from `.env`. Claims: user id, role and expiry. Use a long expiry for the mobile app (for example 30 days, configurable with `JWT_EXPIRE_DAYS`) so farmers are not forced to log in while offline.
- **Protected routes:** a reusable `get_current_user` dependency in `auth_utils.py` that reads the `Authorization: Bearer <token>` header. Role checks (`officer`) sit on top of it.
- **Validation (Pydantic):** name is required; `login_id` must be a valid email or a 10-digit mobile number; password has a minimum length (for example 8 characters).
- **Error handling:** a duplicate `login_id` returns 409 with a friendly message. A failed login returns the **same generic message** for an unknown account and a wrong password, so attackers cannot discover which accounts exist.
- **Roles:** `farmer` for everyone who signs up; `officer` accounts are seeded manually. Only officers can open Field Reports and `GET /api/scans/stats`.
- **Sync rules:** `POST /api/scans/sync` accepts guest scans (no token) and account scans (with token). A logged-in sync sets `user_id` from the token, never from the request body.

#### Mobile app implementation notes

- Store the token and basic profile with `@capacitor/preferences`. This is **not encrypted storage**. It is acceptable for a hackathon demo; for production, move the token to a secure-storage plugin backed by the Android Keystore (check which plugin is currently maintained).
- Generate `device_id` once on first launch and keep it on the phone.
- Filter History by the current user, so one person's scans do not show under another account on a shared phone.
- Show every login and signup message in English, Hindi or Gujarati, matching the chosen language.

#### Website implementation notes (Django)

- The Django login and signup views send the form data to the FastAPI auth endpoints (using `requests`, with a timeout) and store the returned token and profile in the **Django session**. Django's session cookie then keeps the user signed in. Confirm that `django.contrib.sessions` is enabled in `settings.py` (it is by default in new projects).
- Add a small decorator for protected views. It redirects visitors to the login page, and returns a "not allowed" page when a farmer opens an officer-only page.
- Public pages: Home, Crop Guide, Mandi Prices, Product Insights, Agri Networks. Protected pages: My Scans (any signed-in user) and Field Reports (officers).
- Include `{% csrf_token %}` in every Django form.
- Log out clears the session.

#### Demo accounts

Seed two accounts and list them in the README: a demo **farmer** and a demo **officer**, so judges can see both views without signing up. These are for the demo only and must be removed or changed before any real use.

#### Deliberately out of scope (be honest in the pitch)

- Password reset and "forgot password" (needs an email or SMS service).
- Verifying that the mobile number or email belongs to the user. OTP verification needs a paid SMS gateway.
- Social login and multi-factor authentication.
- Production-grade rate limiting. A simple attempt counter on login is enough for the demo.

These belong on the roadmap slide, not in the 10-day build.

---

## 6. File-by-file change matrix

| File / folder | Action | What changes |
|---|---|---|
| `db_utils.py` | **Rewrite** | MongoDB client, `get_db()`, `db_is_up()`, `next_id()`, index creation |
| `api_main.py` | **Modify** | Replace SQL with MongoDB queries; add auth, advisory, scan-sync, stats, health |
| `core/services/government_api.py` | **Modify** | MongoDB upserts instead of `ON DUPLICATE KEY UPDATE` |
| `schema.sql` | **Retire** | Keep as migration reference; the data now lives in MongoDB |
| `migrate_mysql_to_mongo.py` | **New** | One-time data copy with row-count verification |
| `requirements.txt` | **Modify** | Replace `mysql-connector-python` with `pymongo`; add `bcrypt` and `PyJWT` for authentication (and `email-validator` if you use Pydantic's email type) |
| `.env` / `.env.example` | **Modify / New** | Add `MONGO_URI`, `MONGO_DB`, `API_URL`, `JWT_SECRET` (long random value) and `JWT_EXPIRE_DAYS`. **Never commit `.env`** |
| `auth_utils.py` | **New** | Password hashing, token creation and checking, `get_current_user` and role checks |
| `core/views.py`, `urls.py` | **Modify** | See 5.6 (adds signup, login, logout, My Scans, Field Reports) |
| `core/templates/*` | **Modify / New** | See 5.6 (adds `login.html`, `signup.html`, `my_scans.html`, `field_reports.html`) |
| `scan-app/` | **New** | Capacitor mobile app (Section 5.4) |
| `ml/` | **New** | Training notebook, `export_advisory.py`, label and conversion scripts |
| `README.md` | **Rewrite** | New problem statement, setup, architecture, demo steps |

### Target folder structure

```
AgriScan/
├── api_main.py
├── auth_utils.py                  # NEW: hashing, tokens, current-user checks
├── db_utils.py
├── migrate_mysql_to_mongo.py
├── requirements.txt
├── .env.example
├── manage.py
├── agri_dashboard/
├── core/
│   ├── views.py
│   ├── services/government_api.py
│   ├── templates/                 # base, dashboard, crops, compare, mandi,
│   │                              # + login, signup, my_scans, field_reports
│   └── static/
├── scan-app/                      # NEW: offline mobile app
│   ├── package.json
│   ├── capacitor.config.json
│   ├── www/
│   │   ├── index.html
│   │   ├── app.js   db.js   i18n.js   auth.js   style.css
│   │   ├── vendor/tf.min.js
│   │   ├── model/   (model.json, *.bin, labels.json)
│   │   ├── data/advisory.json
│   │   └── audio/{en,hi,gu}/
│   └── android/                   # generated by Capacitor
└── ml/                            # training only, not deployed
    ├── train_model.ipynb
    └── export_advisory.py
```

---

## 7. Security and quality requirements

- Do **not** share or commit `.env` or `.venv`. The earlier project zips contained both. If any secret was shared, rotate it.
- Hash passwords with bcrypt; never log tokens, passwords or hashes.
- Keep `JWT_SECRET` long, random and only in `.env`. Changing it signs everyone out.
- Return the same generic error for an unknown account and a wrong password.
- Signup always creates the `farmer` role. Create `officer` accounts only by seeding, and take the user id for synced scans from the token, never from the request body.
- Tighten CORS and require HTTPS for any deployment. Plain `http://` is acceptable only for a local demo, and Android needs an explicit cleartext setting for it.
- Validate all API input; handle expired tokens by asking for a new login **without deleting local data**.
- Keep scan photos on the device. Upload only the diagnosis, confidence, language and optional location. Ask for location permission explicitly.
- Treatment advice must be reviewed. Wrong pesticide guidance can cause real harm, so have a knowledgeable person check every disease entry and translation.

---

## 8. Execution plan (10 days)

| Day | Goal | Output |
|---|---|---|
| **1** | Environment and risk removal | Colab set up and dataset downloaded; **test the TF.js export with a tiny model**; Node and Android Studio installed; an empty Capacitor app running on a real phone; MongoDB installed |
| **2** | Data and first full training | Real-world photos and `Unknown` class collected; two-phase training run; confusion matrix reviewed |
| **3** | Improve and evaluate | Fix weak classes; evaluate on the real-world test set; choose the model version |
| **4** | **Model freeze** and database | Export, convert and verify the model; `labels.json`; finish `db_utils.py` and the migration; run it and verify counts |
| **5** | App core | App: camera, model inference, result screen, language switching. Backend: `users` collection, `auth_utils.py`, register, login and me endpoints |
| **6** | Content | `disease_info` entries in three languages, `advisory.json` export, audio clips, IndexedDB history. Login and signup screens in the app and on the Django website, guest mode |
| **7** | Backend and sync | Token-protected scan sync, stats and `scans/mine`; network listener and outbox; Field Reports and My Scans pages in Django; seed demo accounts |
| **8** | Offline hardening | Airplane-mode tests (including reopening the app offline while logged in), fresh-install tests, low-end phone test, bug fixes |
| **9** | Polish | Clean APK build, app and website UI cleanup, README (with demo accounts), screenshots |
| **10** | Presentation | Slides, demo video (airplane mode visible), full rehearsal. **No new features** |

**Suggested roles (team of 4)**

| Role | Responsibility |
|---|---|
| ML engineer | Dataset, training, evaluation, export, label files |
| Backend engineer | MongoDB migration, FastAPI endpoints, auth, sync |
| Mobile/frontend engineer | Capacitor app, offline storage, UI, languages |
| Web and content lead | Django website changes (including login and signup pages), disease content and translations, slides |

The frontend can start on Day 1 with a **fake prediction**, then plug in the real model on Day 5.

**Minimum viable submission (if time runs short):** offline scan working on a phone, advice in two languages, signup and login with guest mode, and sync into a Field Reports dashboard. Pests, audio and extra crops are bonuses.

---

## 9. Testing and acceptance checklist

**Functional**

- [ ] The app installs from an APK on a clean phone.
- [ ] In **airplane mode**, a leaf photo gives a diagnosis, treatment and audio.
- [ ] Switching language works offline for every screen.
- [ ] A non-leaf image returns "not a leaf / not sure."
- [ ] Low-confidence results show the retake message.
- [ ] Scans made offline appear in History marked "waiting to sync."
- [ ] After reconnecting, scans reach MongoDB with **no duplicates**, and the mark clears.
- [ ] Closing and reopening the app offline loses nothing and keeps the user signed in.
- [ ] A fresh install with no network shows guest mode and clear empty states, not a crash.

**Accounts and login**

- [ ] Signup creates an account; a duplicate mobile number or email is rejected with a clear message.
- [ ] An invalid email or mobile number, and a too-short password, are rejected with helpful messages.
- [ ] A wrong password and an unknown account show the **same** generic error.
- [ ] In MongoDB, the `users` collection contains only password hashes, never plain text.
- [ ] After logging in, closing the app and reopening it in airplane mode keeps the user signed in.
- [ ] An expired or rejected token asks for login again **without deleting local scans**.
- [ ] Signup or login attempted offline shows a clear message and offers guest mode.
- [ ] Guest scans can be attached to the account after login, and then appear in My Scans on the website.
- [ ] A farmer cannot open Field Reports; an officer can.
- [ ] Logging out removes the token, and protected website pages redirect to the login page.

**Model**

- [ ] Real-world test-set accuracy recorded and reported honestly.
- [ ] Per-class weak spots identified and noted.
- [ ] Python and phone predictions match for the same test images.

**Performance**

- [ ] Scan time measured on the cheapest available phone.
- [ ] APK size and model size recorded.

**Backend/web**

- [ ] `/api/health` is OK; `/docs` lists all endpoints.
- [ ] Existing pages (Crop Guide, Mandi, Products) still work on MongoDB.
- [ ] Field Reports shows live synced data.

---

## 10. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Model accuracy drops on real field photos | Demo misfires | Add PlantDoc and own photos; confidence threshold; `Unknown` class; demo with good photos and state limits honestly |
| TF.js conversion or version errors | Lost days | Test the export on Day 1; keep a fallback pretrained model |
| Android toolchain problems | No APK | Install and run an empty app on Day 1; PWA as fallback |
| Slow inference on low-end phones | Poor UX | Quantized MobileNetV2, resize to 224×224, measure early |
| MongoDB migration issues | Data loss | Keep MySQL untouched until counts are verified; the migration is re-runnable |
| Hardware/network failure during demo | Embarrassment | Pre-recorded demo video; APK on a charged phone; tested offline flow |
| Wrong translations or advice | Credibility and safety | Native-speaker review; expert check of treatments |
| Authentication bugs or weak security | Locked-out users, exposed accounts, failed demo | Use bcrypt and signed tokens, keep guest mode so scanning never depends on login, seed demo accounts, test offline reopen early |
| Scope creep | Unfinished product | Model freeze Day 4; feature freeze Day 9 |

---

## 11. Demo script and pitch

**Demo (about 3 minutes)**

1. Show the installed AgriScan app. Sign up (or log in with the demo farmer account) while online.
2. Turn on **airplane mode** on camera. Close and reopen the app to show the farmer stays logged in.
3. Photograph a diseased tomato leaf: show disease, confidence, treatment.
4. Switch to Gujarati or Hindi and play the audio advice.
5. Scan a non-leaf object to show the "not sure" handling.
6. Reconnect: the scans sync. Open **My Scans** on the website as the farmer, then log in as the officer to show the **Field Reports** dashboard.

**Key messages for judges**

- **Problem:** farmers in low-connectivity areas cannot get timely expert help, and delay costs crops.
- **Solution:** an installable app with an on-device AI model, advice in local languages with audio, and offline history that syncs later.
- **Why it works offline:** the model, advice and audio ship inside the app. Only reports need a network.
- **Impact and scale:** synced scans create a regional view that supports early outbreak detection.
- **Honest limits:** trained on selected crops; best with clear single-leaf photos; accuracy reported on a separate real-world test set.
- **Roadmap:** more crops and pests, expert-verified labels, outbreak maps, more languages, iOS.

---

## 12. Definition of done

The project is complete when a farmer can install the app, sign up or log in (or continue as a guest), switch to airplane mode, photograph a leaf, and receive a clear, safe, translated diagnosis with prevention and treatment steps, and when that scan later appears under the farmer's My Scans page and on the officer's Field Reports dashboard without any manual work.

---

## Appendix A: Glossary

| Term | Meaning |
|---|---|
| Offline-first | The app's main features work with no internet; the network is used only to sync |
| Transfer learning | Reusing a model pretrained on millions of images and teaching it only the new task |
| MobileNetV2 | A small, fast image model suited to phones |
| TensorFlow.js | A library that runs the model in a browser or WebView on the phone |
| Capacitor | A tool that wraps a web app into an installable Android app |
| IndexedDB | A database built into browsers/WebViews that keeps data on the device |
| Outbox pattern | Saving changes locally and uploading them later, marking them done only after confirmation |
| Idempotent sync | Sending the same record twice has no extra effect, thanks to a unique ID |
| PWA | A web app that can be installed and cached for offline use |
| JWT | A signed token that proves who the user is. The phone saves it, so the app can stay logged in offline |
| bcrypt | A password-hashing method. Passwords are stored as hashes, never as plain text |
| Guest mode | Using the core scan feature without an account |

## Appendix B: Items to verify before relying on them

- Exact Kaggle dataset names and class-folder spelling (check with a directory listing after download).
- Compatibility of your Python version with `pymongo` and any TensorFlow tooling (create a Python 3.11 or 3.12 environment if installs fail).
- Current Capacitor settings for cleartext HTTP on Android (they change between versions).
- Any helpline phone numbers shown in the app.
- Which secure-storage option you will use for the login token on Android (Capacitor Preferences is not encrypted).
- That `bcrypt` and `PyJWT` install cleanly on your Python version.
