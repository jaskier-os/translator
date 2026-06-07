"""End-to-end tests for the translator service."""
import os
import requests

BASE_URL = os.environ.get("TRANSLATOR_URL", "http://localhost:10015")
API_KEY = os.environ.get("API_KEY", "your-api-key-here")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "model" in data
    print(f"Health: {data}")


def test_translate_en_to_zh():
    r = requests.post(
        f"{BASE_URL}/translate",
        json={"text": "Hello, how are you?", "source_lang": "eng_Latn", "target_lang": "zho_Hans"},
        headers=HEADERS,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["translations"]) == 1
    print(f"EN->ZH: {data['translations'][0]['text']}")


def test_translate_zh_to_en():
    r = requests.post(
        f"{BASE_URL}/translate",
        json={"text": "你好，你好吗？", "source_lang": "zho_Hans", "target_lang": "eng_Latn"},
        headers=HEADERS,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["translations"]) == 1
    print(f"ZH->EN: {data['translations'][0]['text']}")


def test_translate_batch():
    r = requests.post(
        f"{BASE_URL}/translate",
        json={"text": ["Hello", "Goodbye", "Thank you"], "source_lang": "eng_Latn", "target_lang": "zho_Hans"},
        headers=HEADERS,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["translations"]) == 3
    for t in data["translations"]:
        print(f"  {t['text']}")


def test_auth_required():
    r = requests.post(f"{BASE_URL}/translate", json={"text": "test", "target_lang": "zho_Hans"})
    assert r.status_code == 401


if __name__ == "__main__":
    test_health()
    test_translate_en_to_zh()
    test_translate_zh_to_en()
    test_translate_batch()
    test_auth_required()
    print("All tests passed.")
