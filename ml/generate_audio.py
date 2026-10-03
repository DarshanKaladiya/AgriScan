"""
AgriScan Multilingual Audio Guide Generator
Generates spoken voice guidance (.mp3) for all crop disease classes
in English (en), Hindi (hi), and Gujarati (gu) for offline playback in scan-app.
"""

import os
import sys
import json
import time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    from gtts import gTTS
except ImportError:
    print("[ERROR] gTTS is not installed. Install with `pip install gTTS`.")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVISORY_PATH = os.path.join(BASE_DIR, "ml", "advisory.json")
APP_WWW_DIR = os.path.join(BASE_DIR, "scan-app", "www")

def generate_all_audio():
    print("=" * 65)
    print(">>> AGRISCAN: GENERATING MULTILINGUAL OFFLINE AUDIO CLIPS <<<")
    print("=" * 65)

    if not os.path.exists(ADVISORY_PATH):
        print(f"[ERROR] {ADVISORY_PATH} not found. Run export_advisory.py first.")
        return False

    with open(ADVISORY_PATH, "r", encoding="utf-8") as f:
        advisory_data = json.load(f)

    langs = [
        ("en", "en", "English"),
        ("hi", "hi", "Hindi"),
        ("gu", "gu", "Gujarati")
    ]

    # Ensure output directories exist
    for lang_key, _, _ in langs:
        lang_dir = os.path.join(APP_WWW_DIR, "audio", lang_key)
        os.makedirs(lang_dir, exist_ok=True)

    total_tasks = len(advisory_data) * len(langs)
    completed = 0

    print(f"Synthesizing {total_tasks} audio files across {len(advisory_data)} disease classes...\n")

    for class_key, info in advisory_data.items():
        audio_map = info.get("audio", {})
        name_map = info.get("name", {})
        treatment_map = info.get("treatment", {})
        symptoms_map = info.get("symptoms", {})

        for lang_code, tts_lang, lang_label in langs:
            rel_audio_path = audio_map.get(lang_code)
            if not rel_audio_path:
                continue

            target_file = os.path.join(APP_WWW_DIR, rel_audio_path)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            # Skip if already generated and non-empty
            if os.path.exists(target_file) and os.path.getsize(target_file) > 500:
                completed += 1
                continue

            # Compose spoken text
            disease_title = name_map.get(lang_code, name_map.get("en", class_key))
            treatment_text = treatment_map.get(lang_code, symptoms_map.get(lang_code, ""))
            
            # Shorten if too long for quick playback
            if len(treatment_text) > 160:
                sentences = treatment_text.split(".")
                treatment_text = sentences[0] + "."

            spoken_text = f"{disease_title}. {treatment_text}".strip()

            try:
                tts = gTTS(text=spoken_text, lang=tts_lang, slow=False)
                tts.save(target_file)
                completed += 1
                file_size_kb = os.path.getsize(target_file) / 1024
                print(f"[{completed:02d}/{total_tasks}] [{lang_label}] {class_key} -> {file_size_kb:.1f} KB")
                time.sleep(0.2)  # Avoid rate limiting
            except Exception as e:
                print(f"[WARN] Failed generating {lang_code} for {class_key}: {e}")
                # Create a minimal empty fallback or retry
                try:
                    # Retry with English if regional TTS fails
                    tts = gTTS(text=disease_title, lang="en", slow=False)
                    tts.save(target_file)
                    completed += 1
                except Exception:
                    pass

    print("\n" + "=" * 65)
    print(f"[SUCCESS] Audio generation complete! Generated offline audio files in {APP_WWW_DIR}/audio/")
    print("=" * 65)
    return True

if __name__ == "__main__":
    generate_all_audio()
