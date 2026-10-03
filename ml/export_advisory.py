"""
AgriScan Advisory Knowledge Exporter
Extracts all multilingual disease documents from MongoDB `disease_info`
and exports them into a clean, standalone `advisory.json` file for
the offline mobile application.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from db_utils import get_db, clean_doc

load_dotenv()

OUTPUT_PATH_ML = os.path.join(os.path.dirname(__file__), "advisory.json")
OUTPUT_PATH_APP = os.path.join(os.path.dirname(__file__), "..", "scan-app", "www", "data", "advisory.json")

def export_advisory():
    print("=" * 60)
    print(">>> AGRISCAN: EXPORTING ADVISORY KNOWLEDGE BUNDLE <<<")
    print("=" * 60)

    db = get_db()
    if db is None:
        print("[ERROR] Cannot connect to MongoDB. Ensure MongoDB is running on port 27017.")
        return False

    # Fetch all disease knowledge documents
    docs = list(db.disease_info.find({}, {"_id": 0}))
    if not docs:
        print("[ERROR] No documents found in `disease_info` collection. Run migrate_mysql_to_mongo.py first.")
        return False

    cleaned_docs = [clean_doc(d) for d in docs]
    
    # Create key-value lookup indexed by class_key for O(1) offline lookup
    advisory_dict = {
        d["class_key"]: d for d in cleaned_docs
    }

    # Also extract class_keys in consistent order
    class_keys = sorted(list(advisory_dict.keys()))

    # Write to ml/advisory.json
    os.makedirs(os.path.dirname(OUTPUT_PATH_ML), exist_ok=True)
    with open(OUTPUT_PATH_ML, "w", encoding="utf-8") as f:
        json.dump(advisory_dict, f, ensure_ascii=False, indent=2)
    print(f"[OK] Exported {len(cleaned_docs)} disease entries to: {OUTPUT_PATH_ML}")

    # Write labels.json to ml/labels.json
    labels_path = os.path.join(os.path.dirname(__file__), "labels.json")
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(class_keys, f, ensure_ascii=False, indent=2)
    print(f"[OK] Exported {len(class_keys)} labels to: {labels_path}")

    # If scan-app exists, copy advisory and labels there as well
    try:
        os.makedirs(os.path.dirname(OUTPUT_PATH_APP), exist_ok=True)
        with open(OUTPUT_PATH_APP, "w", encoding="utf-8") as f:
            json.dump(advisory_dict, f, ensure_ascii=False, indent=2)
        
        app_labels_path = os.path.join(os.path.dirname(OUTPUT_PATH_APP), "labels.json")
        with open(app_labels_path, "w", encoding="utf-8") as f:
            json.dump(class_keys, f, ensure_ascii=False, indent=2)

        model_dir = os.path.join(os.path.dirname(__file__), "..", "scan-app", "www", "model")
        os.makedirs(model_dir, exist_ok=True)
        with open(os.path.join(model_dir, "labels.json"), "w", encoding="utf-8") as f:
            json.dump(class_keys, f, ensure_ascii=False, indent=2)

        print(f"[OK] Synced advisory & labels into mobile app data & model dirs")
    except Exception as e:
        print(f"[Notice] Mobile app data dir not yet initialized ({e})")

    print("\nSummary of Exported Classes:")
    for idx, ck in enumerate(class_keys):
        info = advisory_dict[ck]
        name_en = info.get("name", {}).get("en", ck)
        name_gu = info.get("name", {}).get("gu", "")
        print(f" {idx+1:02d}. {ck:<45} -> {name_en} ({name_gu})")
    print("=" * 60)
    return True

if __name__ == "__main__":
    export_advisory()
