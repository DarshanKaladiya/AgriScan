"""
AgriScan Quick Single-Image Tester
Test any crop leaf photo against your trained model and see:
- Top-1 Predicted Disease & Confidence Score
- Top-3 Probability Distribution
- Multilingual Advisory (EN, HI, GU) & Spoken Audio Path

Usage:
    python ml/test_single_image.py --image path/to/leaf.jpg [--model ml/best_model.keras]
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
LABELS_PATH = BASE_DIR / "ml" / "labels.json"
ADVISORY_PATH = BASE_DIR / "ml" / "advisory.json"

def main():
    parser = argparse.ArgumentParser(description="AgriScan Quick Single-Image Tester")
    parser.add_argument("--image", type=str, required=True, help="Path to leaf image (.jpg, .jpeg, .png)")
    parser.add_argument("--model", type=str, default="ml/best_model.keras", help="Path to trained model (.keras or .h5)")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"[ERROR] Image file does not exist: {img_path}")
        return

    # Load Labels
    if not LABELS_PATH.exists():
        print(f"[ERROR] Labels file not found: {LABELS_PATH}")
        return
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)

    # Load Advisory
    advisory_map = {}
    if ADVISORY_PATH.exists():
        with open(ADVISORY_PATH, "r", encoding="utf-8") as f:
            advisory_map = json.load(f)

    print("=" * 68)
    print(">>> AGRISCAN: LEAF DIAGNOSIS TESTER <<<")
    print("=" * 68)
    print(f"Testing Leaf Image: {img_path.name}")
    print(f"Target Model:       {args.model}")
    print("-" * 68)

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"[NOTE] Model file '{model_path}' not found on local disk.")
        print("\nOnce you finish training in Google Colab:")
        print("  1. Download `best_model.keras` from Colab into `ml/`")
        print(f"  2. Re-run: python ml/test_single_image.py --image \"{args.image}\"\n")
        
        # Display simulated demonstration for verification
        print("--- [SIMULATED PREVIEW MODE (Sample Output Structure)] ---")
        detected_class = "Tomato___Early_blight"
        confidence = 0.942
        display_results(detected_class, confidence, labels, advisory_map)
        return

    # Real Model Inference
    try:
        import numpy as np
        from PIL import Image
        import tensorflow as tf

        img = Image.open(img_path).convert("RGB").resize((224, 224))
        # Raw 0 to 255 pixel values
        img_array = np.array(img, dtype=np.float32)
        batch = np.expand_dims(img_array, axis=0)

        model = tf.keras.models.load_model(str(model_path))
        preds = model.predict(batch, verbose=0)[0]

        top_indices = np.argsort(preds)[::-1][:3]
        top1_idx = top_indices[0]
        detected_class = labels[top1_idx]
        confidence = float(preds[top1_idx])

        display_results(detected_class, confidence, labels, advisory_map, preds=preds, top_indices=top_indices)

    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")

def display_results(detected_class, confidence, labels, advisory_map, preds=None, top_indices=None):
    info = advisory_map.get(detected_class, {})
    name_info = info.get("name", {})
    treatment_info = info.get("treatment", {})
    audio_info = info.get("audio", {})

    print(f"\nDIAGNOSIS:    {detected_class}")
    print(f"CONFIDENCE:   {confidence * 100:.2f}%\n")

    print("NAMES:")
    print(f"  - English:  {name_info.get('en', detected_class)}")
    print(f"  - Hindi:    {name_info.get('hi', 'N/A')}")
    print(f"  - Gujarati: {name_info.get('gu', 'N/A')}")

    print("\nRECOMMENDED TREATMENT:")
    print(f"  - English:  {treatment_info.get('en', 'N/A')}")
    print(f"  - Hindi:    {treatment_info.get('hi', 'N/A')}")
    print(f"  - Gujarati: {treatment_info.get('gu', 'N/A')}")

    print("\nAUDIO GUIDANCE CLIPS:")
    for lang, rel_path in audio_info.items():
        print(f"  - [{lang.upper()}]: scan-app/www/{rel_path}")

    if preds is not None and top_indices is not None:
        print("\nTOP-3 PROBABILITIES:")
        for idx in top_indices:
            print(f"  - {labels[idx]:<45} : {preds[idx] * 100:>5.2f}%")

    print("=" * 68)

if __name__ == "__main__":
    main()
