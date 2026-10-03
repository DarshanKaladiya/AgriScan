"""
AgriScan Real-World Evaluation Benchmark (PlantDoc Test Suite)
Validates model robustness on unbiased in-field photos from the PlantDoc dataset.

Usage:
    python ml/evaluate_realworld.py [--model ml/best_model.keras] [--dataset PlantDoc/test]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
LABELS_PATH = BASE_DIR / "ml" / "labels.json"
PLANTDOC_TEST_DIR = BASE_DIR / "PlantDoc" / "test"
PLANTDOC_TRAIN_DIR = BASE_DIR / "PlantDoc" / "train"

# Cross-dataset alignment mapping: PlantDoc folder name -> AgriScan class_key
PLANTDOC_MAPPING = {
    # Tomato classes
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf mosaic virus": "Tomato___mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Yellow_Leaf_Curl_Virus",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato leaf": "Tomato___healthy",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites_Two_spotted_spider_mite",
    # Corn classes
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot",
    "Corn rust leaf": "Corn_(maize)___Common_rust",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    # Potato classes
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
}

def load_labels():
    if not LABELS_PATH.exists():
        print(f"[ERROR] Labels file not found at {LABELS_PATH}. Run ml/export_advisory.py first.")
        sys.exit(1)
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def audit_dataset_alignment(test_dir, labels):
    """Audits available test images and maps them to model classes."""
    print("=" * 68)
    print(">>> AGRISCAN: AUDITING REAL-WORLD TEST BENCHMARK (PlantDoc) <<<")
    print("=" * 68)

    label_set = set(labels)
    dataset_summary = {}
    total_images = 0
    matched_images = 0

    if not test_dir.exists():
        print(f"[ERROR] Test directory {test_dir} does not exist.")
        return None

    folders = sorted([f for f in test_dir.iterdir() if f.is_dir()])
    print(f"\nFound {len(folders)} total class folders in {test_dir.name}/.\n")
    print(f"{'PlantDoc Folder':<38} | {'AgriScan Class Key':<35} | {'Images':<6}")
    print("-" * 85)

    for folder in folders:
        img_files = [p for p in folder.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]]
        count = len(img_files)
        total_images += count
        target_class = PLANTDOC_MAPPING.get(folder.name)

        if target_class and target_class in label_set:
            status = target_class
            matched_images += count
            dataset_summary[folder.name] = {
                "folder": str(folder),
                "target_class": target_class,
                "count": count,
                "files": [str(p) for p in img_files]
            }
        else:
            status = f"[Ignored / Not in Model: {target_class or 'Out of Scope'}]"

        print(f"{folder.name:<38} | {status:<35} | {count:<6}")

    print("-" * 85)
    print(f"Total Images in Benchmark Directory: {total_images}")
    print(f"Aligned Target Disease Images:        {matched_images} across {len(dataset_summary)} classes")
    print("=" * 68)
    return dataset_summary

def evaluate_model(model_path, dataset_summary, labels):
    """Evaluates a trained Keras/TFLite/SavedModel on aligned PlantDoc test images."""
    print(f"\n[INFO] Loading model from: {model_path} ...")

    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("[ERROR] Required packages numpy or pillow not installed. Install with `pip install numpy pillow`.")
        return

    # Try loading TensorFlow / Keras
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path)
        print(f"[OK] Successfully loaded Keras model: {model.name if hasattr(model, 'name') else 'Trained Model'}")
    except Exception as e:
        print(f"[WARN] Failed loading as standard Keras model: {e}")
        return

    label_to_idx = {l: i for i, l in enumerate(labels)}
    idx_to_label = {i: l for i, l in enumerate(labels)}

    correct_top1 = 0
    correct_top3 = 0
    total_evaluated = 0
    per_class_results = defaultdict(lambda: {"total": 0, "top1": 0, "conf_sum": 0.0})

    for folder_name, info in dataset_summary.items():
        true_label = info["target_class"]
        true_idx = label_to_idx.get(true_label)
        if true_idx is None:
            continue

        for img_path in info["files"]:
            try:
                # Load and preprocess image (224x224, raw 0-255 for MobileNetV2 with internal preprocess)
                img = Image.open(img_path).convert("RGB").resize((224, 224))
                img_array = np.array(img, dtype=np.float32)
                batch = np.expand_dims(img_array, axis=0)

                # Inference
                preds = model.predict(batch, verbose=0)[0]
                top1_idx = int(np.argmax(preds))
                top3_indices = [int(i) for i in np.argsort(preds)[-3:][::-1]]

                confidence = float(preds[top1_idx])
                is_top1 = (top1_idx == true_idx)
                is_top3 = (true_idx in top3_indices)

                if is_top1:
                    correct_top1 += 1
                if is_top3:
                    correct_top3 += 1
                total_evaluated += 1

                per_class_results[true_label]["total"] += 1
                if is_top1:
                    per_class_results[true_label]["top1"] += 1
                per_class_results[true_label]["conf_sum"] += confidence

            except Exception as ex:
                print(f"[WARN] Error reading image {img_path}: {ex}")

    if total_evaluated == 0:
        print("[ERROR] No images evaluated.")
        return

    top1_acc = (correct_top1 / total_evaluated) * 100
    top3_acc = (correct_top3 / total_evaluated) * 100

    print("\n" + "=" * 68)
    print(f">>> REAL-WORLD FIELD TEST RESULTS (PlantDoc) <<<")
    print("=" * 68)
    print(f"Overall Top-1 Accuracy: {top1_acc:.2f}% ({correct_top1}/{total_evaluated})")
    print(f"Overall Top-3 Accuracy: {top3_acc:.2f}% ({correct_top3}/{total_evaluated})")
    print("-" * 68)
    print(f"{'Class Key':<42} | {'Tested':<6} | {'Top-1 Acc':<9} | {'Avg Conf':<8}")
    print("-" * 68)

    results_export = {
        "overall_top1_accuracy": round(top1_acc, 2),
        "overall_top3_accuracy": round(top3_acc, 2),
        "total_evaluated": total_evaluated,
        "classes": {}
    }

    for label, stat in sorted(per_class_results.items()):
        cnt = stat["total"]
        t1 = stat["top1"]
        acc = (t1 / cnt) * 100 if cnt > 0 else 0
        avg_conf = (stat["conf_sum"] / cnt) if cnt > 0 else 0
        print(f"{label:<42} | {cnt:<6} | {acc:>8.1f}% | {avg_conf * 100:>7.1f}%")
        results_export["classes"][label] = {
            "count": cnt,
            "top1_correct": t1,
            "accuracy_percent": round(acc, 2),
            "avg_confidence": round(avg_conf, 4)
        }

    print("=" * 68)

    benchmark_json = BASE_DIR / "ml" / "benchmark_results.json"
    with open(benchmark_json, "w", encoding="utf-8") as f:
        json.dump(results_export, f, indent=2)
    print(f"[OK] Detailed benchmark report saved to: {benchmark_json}\n")

def main():
    parser = argparse.ArgumentParser(description="AgriScan Real-World Evaluation Benchmark")
    parser.add_argument("--model", type=str, default="", help="Path to trained Keras model or weights file")
    parser.add_argument("--dataset", type=str, default=str(PLANTDOC_TEST_DIR), help="Path to PlantDoc test directory")
    args = parser.parse_args()

    labels = load_labels()
    test_dir = Path(args.dataset)
    dataset_summary = audit_dataset_alignment(test_dir, labels)

    if args.model and os.path.exists(args.model):
        evaluate_model(args.model, dataset_summary, labels)
    else:
        print("\n[NOTE] No --model path provided or model not found on local disk.")
        print("To benchmark your trained model after Google Colab training:")
        print("    1. Download `best_model.keras` or `model.h5` from Google Colab into `ml/`")
        print("    2. Run: python ml/evaluate_realworld.py --model ml/best_model.keras")
        print("=" * 68)

if __name__ == "__main__":
    main()
