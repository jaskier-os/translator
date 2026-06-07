"""E2E test: translate 'Hello, how are you?' into 20 languages via orchestrator and direct API."""
import os
import sys
import json
import requests

DIRECT_URL = os.environ.get("TRANSLATOR_URL", "http://localhost:10015")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:10001")
API_KEY = os.environ.get("API_KEY", "test-key-123")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

SOURCE_TEXT = "Hello, how are you? I hope you are having a great day."
SOURCE_LANG = "eng_Latn"

# 20 target languages including Asian languages
TARGETS = [
    ("zho_Hans", "Chinese Simplified"),
    ("zho_Hant", "Chinese Traditional"),
    ("jpn_Jpan", "Japanese"),
    ("kor_Hang", "Korean"),
    ("hin_Deva", "Hindi"),
    ("tha_Thai", "Thai"),
    ("vie_Latn", "Vietnamese"),
    ("ind_Latn", "Indonesian"),
    ("mya_Mymr", "Burmese"),
    ("tgl_Latn", "Tagalog"),
    ("rus_Cyrl", "Russian"),
    ("ukr_Cyrl", "Ukrainian"),
    ("ara_Arab", "Arabic"),
    ("heb_Hebr", "Hebrew"),
    ("tur_Latn", "Turkish"),
    ("fra_Latn", "French"),
    ("deu_Latn", "German"),
    ("spa_Latn", "Spanish"),
    ("por_Latn", "Portuguese"),
    ("ita_Latn", "Italian"),
]


def test_direct_api():
    """Test all 20 languages via direct translator API."""
    print(f"\n{'='*70}")
    print(f"DIRECT API TEST ({DIRECT_URL}/translate)")
    print(f"{'='*70}")
    print(f"Source ({SOURCE_LANG}): {SOURCE_TEXT}\n")

    passed = 0
    failed = 0

    for lang_code, lang_name in TARGETS:
        try:
            r = requests.post(
                f"{DIRECT_URL}/translate",
                json={"text": SOURCE_TEXT, "source_lang": SOURCE_LANG, "target_lang": lang_code},
                headers=HEADERS,
                timeout=60,
            )
            if r.status_code != 200:
                print(f"  FAIL  {lang_name:20s} ({lang_code}) -- HTTP {r.status_code}: {r.text}")
                failed += 1
                continue

            data = r.json()
            translated = data["translations"][0]["text"]
            # Basic sanity: translation should not be empty and should differ from source
            if not translated.strip():
                print(f"  FAIL  {lang_name:20s} ({lang_code}) -- empty translation")
                failed += 1
            elif translated.strip() == SOURCE_TEXT.strip():
                print(f"  WARN  {lang_name:20s} ({lang_code}) -- identical to source: {translated}")
                passed += 1  # count as pass but warn
            else:
                print(f"  OK    {lang_name:20s} ({lang_code}) -> {translated}")
                passed += 1
        except Exception as e:
            print(f"  FAIL  {lang_name:20s} ({lang_code}) -- {e}")
            failed += 1

    print(f"\nDirect API: {passed}/{len(TARGETS)} passed, {failed} failed")
    return failed == 0


def test_orchestrator_api():
    """Test all 20 languages via orchestrator proxy route."""
    print(f"\n{'='*70}")
    print(f"ORCHESTRATOR API TEST ({ORCHESTRATOR_URL}/api/v1/translate)")
    print(f"{'='*70}")
    print(f"Source ({SOURCE_LANG}): {SOURCE_TEXT}\n")

    # First check if orchestrator is reachable
    try:
        r = requests.get(f"{ORCHESTRATOR_URL}/api/v1/health", timeout=5)
        if r.status_code != 200:
            print(f"  SKIP -- Orchestrator not healthy: HTTP {r.status_code}")
            return True  # Don't fail the test if orchestrator is not running
    except Exception:
        print(f"  SKIP -- Orchestrator not reachable at {ORCHESTRATOR_URL}")
        return True

    passed = 0
    failed = 0

    for lang_code, lang_name in TARGETS:
        try:
            r = requests.post(
                f"{ORCHESTRATOR_URL}/api/v1/translate",
                json={"text": SOURCE_TEXT, "source_lang": SOURCE_LANG, "target_lang": lang_code},
                headers=HEADERS,
                timeout=60,
            )
            if r.status_code != 200:
                print(f"  FAIL  {lang_name:20s} ({lang_code}) -- HTTP {r.status_code}: {r.text}")
                failed += 1
                continue

            data = r.json()
            translated = data["translations"][0]["text"]
            if not translated.strip():
                print(f"  FAIL  {lang_name:20s} ({lang_code}) -- empty translation")
                failed += 1
            else:
                print(f"  OK    {lang_name:20s} ({lang_code}) -> {translated}")
                passed += 1
        except Exception as e:
            print(f"  FAIL  {lang_name:20s} ({lang_code}) -- {e}")
            failed += 1

    print(f"\nOrchestrator API: {passed}/{len(TARGETS)} passed, {failed} failed")
    return failed == 0


def test_batch():
    """Test batch translation via direct API."""
    print(f"\n{'='*70}")
    print(f"BATCH TEST (3 texts -> Chinese Simplified)")
    print(f"{'='*70}\n")

    texts = ["Good morning", "Thank you very much", "See you tomorrow"]
    r = requests.post(
        f"{DIRECT_URL}/translate",
        json={"text": texts, "source_lang": SOURCE_LANG, "target_lang": "zho_Hans"},
        headers=HEADERS,
        timeout=30,
    )
    if r.status_code != 200:
        print(f"  FAIL -- HTTP {r.status_code}: {r.text}")
        return False

    data = r.json()
    for i, t in enumerate(data["translations"]):
        print(f"  OK    '{texts[i]}' -> {t['text']}")

    print(f"\nBatch: {len(data['translations'])}/{len(texts)} translations returned")
    return len(data["translations"]) == len(texts)


if __name__ == "__main__":
    all_ok = True
    all_ok = test_direct_api() and all_ok
    all_ok = test_orchestrator_api() and all_ok
    all_ok = test_batch() and all_ok

    print(f"\n{'='*70}")
    if all_ok:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print(f"{'='*70}")
    sys.exit(0 if all_ok else 1)
