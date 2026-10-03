# 🛡️ AgriScan: Offline Crop Disease Detection & Multilingual Advisory

> **"The intelligence travels with the phone, and only the reports travel over the network."**

An offline-first agricultural solution empowering farmers to diagnose crop diseases and pest infestations from leaf photographs in **Airplane Mode**, receive instant prevention and treatment guidance in local languages (**English, ગુજરાતી, and हिंदी**) with audio, and automatically synchronize field reports with agricultural officers when internet connectivity is restored.

---

## 🚀 Key Highlights & Features

- 🌿 **On-Device AI Inference:** Client-side neural network (MobileNetV2) runs inside the mobile application. Classifies leaf images in 1.5 seconds without internet connectivity.
- 🗣️ **Multilingual Audio Advice:** Disease symptoms, preventive practices, and practical chemical/organic remedies translated into English, Gujarati, and Hindi with pre-bundled audio guidance.
- 🗄️ **Full MongoDB Integration:** Scalable document storage housing 272 master crops, 64 input agro products, 770 crop advisories, 11,500+ APMC mandi market records, and 17 multilingual disease classes.
- 🔐 **Secure Role-Based Authentication:** Bcrypt password hashing + signed JWTs supporting both mobile phone numbers and email logins, with guest mode support.
- 📡 **Officer Outbreak Surveillance Dashboard:** Aggregates synchronized field scans to track disease spread, map high-risk clusters, and enable proactive epidemic control.
- 📊 **Real-Time APMC Mandi Intelligence:** Live market prices, commodity trend trackers, and active ingredient fungicide/pesticide comparisons.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **AI / Machine Learning** | MobileNetV2, TensorFlow / TensorFlow.js |
| **Mobile App (Offline Side)** | HTML5, Modern Vanilla CSS, JavaScript, IndexedDB, Capacitor |
| **Backend & Sync API** | Python, FastAPI, Uvicorn, Pydantic, PyJWT, Bcrypt |
| **Web Platform** | Python, Django 6, Django Sessions, SQLite3 |
| **Database** | MongoDB (Compass / Service on port 27017) |

---

## 🔑 Demo Accounts (For Hackathon Judges)

Quick testing credentials for both user roles:

| Role | Username / Mobile / Email | Password | Access Level |
|---|---|---|---|
| **Farmer Demo** | `9876543210` *(or `farmer@agriscan.com`)* | `farmer123` | Personal Scan History, Crop Health Guides |
| **Officer Demo** | `officer@agriscan.com` *(or `9876543211`)* | `officer123` | Outbreak Surveillance & Field Reports |
| **Guest Mode** | *No account needed* | *N/A* | Core Leaf Scanning & Audio Advisory |

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/DarshanKaladiya/AgriScan.git
cd AgriScan
```

### 2. Configure Virtual Environment & Dependencies
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure MongoDB is running locally on `mongodb://localhost:27017/`.

### 4. Database Setup & Migration
To migrate all data from MySQL to MongoDB (or seed fresh MongoDB records):
```bash
python migrate_mysql_to_mongo.py
```

### 5. Start the Services

**Terminal 1 — FastAPI Backend (Port 8000):**
```bash
uvicorn api_main:app --reload --port 8000
```
*API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)*

**Terminal 2 — Django Web Platform (Port 8001):**
```bash
python manage.py runserver 8001
```
*Web Portal: [http://localhost:8001](http://localhost:8001)*

---

## 🧪 Automated Test Verification

Run the integration test suites to verify system integrity:

```bash
# Test 1: Backend API, Authentication, Advisory, and Sync (10 suites)
python test_phase1.py

# Test 2: Django Web Views, Sessions, Role Guards, and Outbreak Reports (9 suites)
python test_phase2_django.py
```

---

## 👨‍💻 Author
**Darshan Kaladiya** & the AgriScan Team
