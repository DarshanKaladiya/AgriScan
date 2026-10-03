"""
Generates the Google Colab Notebook: ml/train_model.ipynb
with complete MobileNetV2 transfer learning, PlantDoc real-world evaluation,
and quantized TensorFlow.js GraphModel export.
"""

import json
import os

notebook = {
    "nbformat": 4,
    "nbformat_minor": 2,
    "metadata": {
        "colab": {
            "name": "AgriScan_Model_Training_and_Export.ipynb",
            "provenance": [],
            "toc_visible": True,
            "gpuType": "T4"
        },
        "kernelspec": {
            "name": "python3",
            "display_name": "Python 3"
        },
        "language_info": {
            "name": "python"
        },
        "accelerator": "GPU"
    },
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🌿 AgriScan: MobileNetV2 Training & Offline TF.js Export\n",
                "\n",
                "This notebook trains an optimized **MobileNetV2** deep learning model for crop disease classification, benchmarks it against real-world in-the-field photos from **PlantDoc**, and exports a quantized **TensorFlow.js GraphModel** ready for offline execution in the **AgriScan mobile app**.\n",
                "\n",
                "### 🎯 Key Engineering Highlights:\n",
                "1. **In-Graph Preprocessing**: Model takes **raw 0–255 pixel values** directly (no manual division by 255 in the mobile app).\n",
                "2. **2-Phase Transfer Learning**: Frozen ImageNet feature extraction followed by gentle fine-tuning of the top 35 layers.\n",
                "3. **Real-World PlantDoc Benchmark**: Tests on unbiased field photos to measure true agricultural accuracy.\n",
                "4. **Quantized TF.js GraphModel**: Converted with float16/uint8 quantization for rapid inference on low-end smartphones (<10MB bundle).\n",
                "\n",
                "⚡ **Recommended Runtime**: Go to *Runtime > Change runtime type* and select **T4 GPU**."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Install Dependencies & Check GPU"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Install tensorflowjs and evaluation tools\n",
                "!pip install -q tensorflowjs matplotlib seaborn pillow\n",
                "\n",
                "import os\n",
                "import json\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import tensorflow as tf\n",
                "from tensorflow import keras\n",
                "from tensorflow.keras import layers\n",
                "from pathlib import Path\n",
                "from google.colab import files\n",
                "\n",
                "print(f\"TensorFlow Version: {tf.__version__}\")\n",
                "gpus = tf.config.list_physical_devices('GPU')\n",
                "if gpus:\n",
                "    print(f\"[OK] GPU Detected: {gpus[0].name}\")\n",
                "else:\n",
                "    print(\"[WARN] No GPU detected. Switch to GPU runtime for 10x faster training!\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Ingest Dataset\n",
                "\n",
                "Upload `tomato_dataset.zip` and optionally `PlantDoc.zip` (for real-world field evaluation).\n",
                "You can upload them using the Colab file browser on the left, or run the cell below to prompt an upload."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Option A: Upload tomato_dataset.zip and PlantDoc.zip directly\n",
                "if not os.path.exists('tomato_dataset') and not os.path.exists('tomato_dataset.zip'):\n",
                "    print(\"Please upload 'tomato_dataset.zip' from your project folder...\")\n",
                "    uploaded = files.upload()\n",
                "\n",
                "# Extract if zip exists\n",
                "if os.path.exists('tomato_dataset.zip'):\n",
                "    print(\"Extracting tomato_dataset.zip...\")\n",
                "    !unzip -q tomato_dataset.zip -d /content/\n",
                "\n",
                "if os.path.exists('PlantDoc.zip'):\n",
                "    print(\"Extracting PlantDoc.zip...\")\n",
                "    !unzip -q PlantDoc.zip -d /content/\n",
                "\n",
                "# Verify dataset paths\n",
                "TRAIN_DIR = '/content/tomato_dataset/train'\n",
                "VALID_DIR = '/content/tomato_dataset/valid'\n",
                "TEST_DIR = '/content/tomato_dataset/test'\n",
                "\n",
                "if not os.path.exists(TRAIN_DIR):\n",
                "    # Fallback if unzipped into nested folder\n",
                "    for root, dirs, _ in os.walk('/content'):\n",
                "        if 'Tomato___healthy' in dirs or 'Tomato___Early_blight' in dirs:\n",
                "            TRAIN_DIR = root\n",
                "            print(f\"Found training classes in: {TRAIN_DIR}\")\n",
                "            break\n",
                "\n",
                "classes = sorted([d for d in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, d))])\n",
                "print(f\"\\n[OK] Found {len(classes)} classes:\")\n",
                "for i, c in enumerate(classes):\n",
                "    print(f\"  {i+1:02d}. {c}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Data Pipelines & Augmentation\n",
                "\n",
                "We set up batched `tf.data.Dataset` pipelines with prefetching and GPU caching."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "IMG_SIZE = (224, 224)\n",
                "BATCH_SIZE = 32\n",
                "SEED = 42\n",
                "\n",
                "# Load training dataset\n",
                "train_ds = tf.keras.utils.image_dataset_from_directory(\n",
                "    TRAIN_DIR,\n",
                "    image_size=IMG_SIZE,\n",
                "    batch_size=BATCH_SIZE,\n",
                "    shuffle=True,\n",
                "    seed=SEED,\n",
                "    label_mode='categorical'\n",
                ")\n",
                "\n",
                "class_names = train_ds.class_names\n",
                "NUM_CLASSES = len(class_names)\n",
                "\n",
                "# Load validation dataset\n",
                "if os.path.exists(VALID_DIR):\n",
                "    val_ds = tf.keras.utils.image_dataset_from_directory(\n",
                "        VALID_DIR,\n",
                "        image_size=IMG_SIZE,\n",
                "        batch_size=BATCH_SIZE,\n",
                "        shuffle=False,\n",
                "        label_mode='categorical'\n",
                "    )\n",
                "else:\n",
                "    # Split train_ds if no separate valid folder\n",
                "    val_size = int(0.2 * len(train_ds))\n",
                "    val_ds = train_ds.take(val_size)\n",
                "    train_ds = train_ds.skip(val_size)\n",
                "\n",
                "# Optimize pipeline performance\n",
                "AUTOTUNE = tf.data.AUTOTUNE\n",
                "train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)\n",
                "val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)\n",
                "\n",
                "print(f\"[OK] Loaded dataset with {NUM_CLASSES} classes.\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. MobileNetV2 Architecture with In-Graph Preprocessing\n",
                "\n",
                "**Critical Architecture Design:**\n",
                "- Model input expects **raw [0, 255] float32 pixels**.\n",
                "- `tf.keras.applications.mobilenet_v2.preprocess_input` is inside the computational graph so the mobile app does not need to perform manual normalization."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Data Augmentation Sequential Block\n",
                "data_augmentation = keras.Sequential([\n",
                "    layers.RandomFlip(\"horizontal_and_vertical\"),\n",
                "    layers.RandomRotation(0.15),\n",
                "    layers.RandomZoom(0.15),\n",
                "    layers.RandomContrast(0.1),\n",
                "    layers.RandomTranslation(0.08, 0.08)\n",
                "], name=\"data_augmentation\")\n",
                "\n",
                "# Load MobileNetV2 pre-trained on ImageNet\n",
                "base_model = tf.keras.applications.MobileNetV2(\n",
                "    input_shape=(224, 224, 3),\n",
                "    include_top=False,\n",
                "    weights='imagenet'\n",
                ")\n",
                "base_model.trainable = False  # Freeze for Phase 1\n",
                "\n",
                "# Build Complete Graph\n",
                "inputs = keras.Input(shape=(224, 224, 3), name=\"input_image\")\n",
                "x = data_augmentation(inputs)\n",
                "# Internal MobileNetV2 scaling: scales [0, 255] -> [-1, 1]\n",
                "x = tf.keras.applications.mobilenet_v2.preprocess_input(x)\n",
                "x = base_model(x, training=False)\n",
                "x = layers.GlobalAveragePooling2D(name=\"gap\")(x)\n",
                "x = layers.Dropout(0.25, name=\"dropout\")(x)\n",
                "x = layers.Dense(128, activation='relu', name=\"dense_1\")(x)\n",
                "x = layers.Dropout(0.15, name=\"dropout_2\")(x)\n",
                "outputs = layers.Dense(NUM_CLASSES, activation='softmax', name=\"predictions\")(x)\n",
                "\n",
                "model = keras.Model(inputs=inputs, outputs=outputs, name=\"AgriScan_MobileNetV2\")\n",
                "model.summary()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Phase 1: Train Top Classifier (Frozen Backbone)"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "model.compile(\n",
                "    optimizer=keras.optimizers.Adam(learning_rate=1e-3),\n",
                "    loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.08),\n",
                "    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_acc')]\n",
                ")\n",
                "\n",
                "callbacks_phase1 = [\n",
                "    keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=4, restore_best_weights=True),\n",
                "    keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-6)\n",
                "]\n",
                "\n",
                "print(\">>> Starting Phase 1 Training (10 Epochs) <<<\")\n",
                "history_phase1 = model.fit(\n",
                "    train_ds,\n",
                "    validation_data=val_ds,\n",
                "    epochs=10,\n",
                "    callbacks=callbacks_phase1\n",
                ")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Phase 2: Gentle Fine-Tuning (Top 35 Backbone Layers)"
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Unfreeze base model and freeze all but the top 35 layers\n",
                "base_model.trainable = True\n",
                "for layer in base_model.layers[:-35]:\n",
                "    layer.trainable = False\n",
                "\n",
                "trainable_count = sum([tf.keras.backend.count_params(w) for w in model.trainable_weights])\n",
                "print(f\"Trainable parameters for Fine-Tuning: {trainable_count:,}\")\n",
                "\n",
                "# Recompile with lower learning rate\n",
                "model.compile(\n",
                "    optimizer=keras.optimizers.Adam(learning_rate=1e-5),\n",
                "    loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.05),\n",
                "    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_acc')]\n",
                ")\n",
                "\n",
                "callbacks_phase2 = [\n",
                "    keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True),\n",
                "    keras.callbacks.ModelCheckpoint('best_model.keras', monitor='val_accuracy', save_best_only=True)\n",
                "]\n",
                "\n",
                "print(\">>> Starting Phase 2 Fine-Tuning (10 Epochs) <<<\")\n",
                "history_phase2 = model.fit(\n",
                "    train_ds,\n",
                "    validation_data=val_ds,\n",
                "    epochs=10,\n",
                "    callbacks=callbacks_phase2\n",
                ")\n",
                "\n",
                "# Evaluate on validation set\n",
                "eval_results = model.evaluate(val_ds)\n",
                "print(f\"\\n[Validation Final] Loss: {eval_results[0]:.4f} | Top-1 Accuracy: {eval_results[1]*100:.2f}% | Top-3 Accuracy: {eval_results[2]*100:.2f}%\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Real-World Field Benchmark on PlantDoc (Option A)\n",
                "\n",
                "This evaluates the model on real field photos taken in varied lighting and outdoor backgrounds."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "from PIL import Image\n",
                "\n",
                "# PlantDoc folder alignment mapping\n",
                "PLANTDOC_MAPPING = {\n",
                "    'Tomato Early blight leaf': 'Tomato___Early_blight',\n",
                "    'Tomato leaf late blight': 'Tomato___Late_blight',\n",
                "    'Tomato Septoria leaf spot': 'Tomato___Septoria_leaf_spot',\n",
                "    'Tomato leaf bacterial spot': 'Tomato___Bacterial_spot',\n",
                "    'Tomato leaf mosaic virus': 'Tomato___mosaic_virus',\n",
                "    'Tomato leaf yellow virus': 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',\n",
                "    'Tomato mold leaf': 'Tomato___Leaf_Mold',\n",
                "    'Tomato leaf': 'Tomato___healthy',\n",
                "    'Tomato two spotted spider mites leaf': 'Tomato___Spider_mites Two-spotted_spider_mite'\n",
                "}\n",
                "\n",
                "plantdoc_test_dir = '/content/PlantDoc/test'\n",
                "if not os.path.exists(plantdoc_test_dir):\n",
                "    plantdoc_test_dir = '/content/test'\n",
                "\n",
                "if os.path.exists(plantdoc_test_dir):\n",
                "    print(f\">>> Running Real-World Benchmark on {plantdoc_test_dir} <<<\")\n",
                "    correct = 0\n",
                "    total = 0\n",
                "    class_correct = {c: [0, 0] for c in class_names}\n",
                "\n",
                "    for folder in os.listdir(plantdoc_test_dir):\n",
                "        target_cls = PLANTDOC_MAPPING.get(folder)\n",
                "        if target_cls in class_names:\n",
                "            target_idx = class_names.index(target_cls)\n",
                "            folder_path = os.path.join(plantdoc_test_dir, folder)\n",
                "            for img_name in os.listdir(folder_path):\n",
                "                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):\n",
                "                    try:\n",
                "                        img_path = os.path.join(folder_path, img_name)\n",
                "                        img = Image.open(img_path).convert('RGB').resize((224, 224))\n",
                "                        arr = np.expand_dims(np.array(img, dtype=np.float32), axis=0)\n",
                "                        pred = model.predict(arr, verbose=0)[0]\n",
                "                        pred_idx = np.argmax(pred)\n",
                "                        total += 1\n",
                "                        class_correct[target_cls][1] += 1\n",
                "                        if pred_idx == target_idx:\n",
                "                            correct += 1\n",
                "                            class_correct[target_cls][0] += 1\n",
                "                    except Exception:\n",
                "                        pass\n",
                "\n",
                "    if total > 0:\n",
                "        print(f\"\\nPlantDoc Field Top-1 Accuracy: {(correct/total)*100:.2f}% ({correct}/{total})\")\n",
                "        print(\"-\" * 60)\n",
                "        for cls, (c, t) in class_correct.items():\n",
                "            if t > 0:\n",
                "                print(f\"{cls:<40} : {(c/t)*100:>5.1f}% ({c}/{t})\")\n",
                "else:\n",
                "    print(\"[Notice] PlantDoc test directory not found. Upload PlantDoc.zip to run field evaluation.\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 8. Export Quantized TensorFlow.js GraphModel\n",
                "\n",
                "Converts the trained model to a lightweight web model with **float16 quantization** for fast client-side inference."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "import tensorflowjs as tfjs\n",
                "\n",
                "OUTPUT_TFJS_DIR = '/content/agriscan_web_model'\n",
                "os.makedirs(OUTPUT_TFJS_DIR, exist_ok=True)\n",
                "\n",
                "# Strip data augmentation layer for production inference model\n",
                "prod_inputs = keras.Input(shape=(224, 224, 3), name=\"input_image\")\n",
                "px = tf.keras.applications.mobilenet_v2.preprocess_input(prod_inputs)\n",
                "px = base_model(px, training=False)\n",
                "px = model.get_layer(\"gap\")(px)\n",
                "px = model.get_layer(\"dense_1\")(px)\n",
                "prod_outputs = model.get_layer(\"predictions\")(px)\n",
                "prod_model = keras.Model(inputs=prod_inputs, outputs=prod_outputs, name=\"AgriScan_Production\")\n",
                "\n",
                "# Save as SavedModel first\n",
                "SAVED_MODEL_PATH = '/content/saved_model'\n",
                "prod_model.save(SAVED_MODEL_PATH)\n",
                "\n",
                "# Convert SavedModel to TFJS GraphModel with float16 quantization\n",
                "!tensorflowjs_converter \\\n",
                "    --input_format=tf_saved_model \\\n",
                "    --output_format=tfjs_graph_model \\\n",
                "    --quantize_float16=* \\\n",
                "    /content/saved_model \\\n",
                "    /content/agriscan_web_model\n",
                "\n",
                "# Save labels.json\n",
                "labels_path = os.path.join(OUTPUT_TFJS_DIR, 'labels.json')\n",
                "with open(labels_path, 'w', encoding='utf-8') as f:\n",
                "    json.dump(class_names, f, indent=2)\n",
                "\n",
                "print(f\"\\n[OK] Model successfully exported to {OUTPUT_TFJS_DIR}:\")\n",
                "for f in os.listdir(OUTPUT_TFJS_DIR):\n",
                "    size_mb = os.path.getsize(os.path.join(OUTPUT_TFJS_DIR, f)) / (1024 * 1024)\n",
                "    print(f\"  - {f} ({size_mb:.2f} MB)\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 9. Download Model Bundle for AgriScan App\n",
                "\n",
                "Zips and downloads the `model.json`, weight shards, and `labels.json`.\n",
                "Unzip these files directly into `scan-app/www/model/`."
            ]
        },
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Package model into zip\n",
                "!cd /content/agriscan_web_model && zip -r /content/agriscan_model_bundle.zip ./*\n",
                "\n",
                "print(\"\\n[DOWNLOAD] Downloading agriscan_model_bundle.zip to your local computer...\")\n",
                "files.download('/content/agriscan_model_bundle.zip')"
            ]
        }
    ]
}

notebook_path = os.path.join(os.path.dirname(__file__), "train_model.ipynb")
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print(f"[OK] Successfully generated Colab notebook at: {notebook_path}")
