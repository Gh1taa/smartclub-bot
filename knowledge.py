"""The club's information: text files in knowledge/ + the Google Sheet, searchable by meaning.

Each piece of text is turned into an embedding (a list of numbers that captures its meaning).
A question is turned into numbers the same way, and the closest pieces are returned.
Embeddings are saved in embeddings_cache.json so unchanged text is never sent to Gemini twice.
"""
import csv
import io
import json
import math
import os
import threading
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

KNOWLEDGE_DIR = ROOT / "knowledge"
CACHE_FILE = ROOT / "embeddings_cache.json"
EMBED_MODEL = "gemini-embedding-001"
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL", "")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=30_000))
_chunks: list[dict] = []  # {"title", "url", "text", "vector"}
_lock = threading.Lock()
_last_refresh = 0.0


def _split(text: str, max_words: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words - overlap)]


def _read_files() -> list[dict]:
    docs = []
    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        if path.suffix.lower() not in (".md", ".txt"):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        url = ""
        if lines and lines[0].lower().startswith("url:"):  # optional first line "URL: https://..."
            url, lines = lines[0][4:].strip(), lines[1:]
        text = "\n".join(lines)
        title = next((l.lstrip("# ").strip() for l in lines if l.strip()), path.stem)
        docs.append({"title": title, "url": url, "text": text})
    return docs


def _read_sheet() -> list[dict]:
    """Google Sheet columns: Sujet | Information | Lien | Actif ("non" hides a row)."""
    if not SHEET_CSV_URL:
        return []
    r = httpx.get(SHEET_CSV_URL, follow_redirects=True, timeout=30)
    r.raise_for_status()
    docs = []
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        info, title = row.get("information", ""), row.get("sujet", "")
        if info and row.get("actif", "").lower() not in ("non", "no", "0"):
            docs.append({"title": title or info[:60], "url": row.get("lien", ""), "text": f"{title}\n{info}"})
    return docs


def _embed(texts: list[str], task: str) -> list[list[float]]:
    vectors = []
    for i in range(0, len(texts), 50):
        result = client.models.embed_content(
            model=EMBED_MODEL, contents=texts[i:i + 50],
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=768))
        vectors += [e.values for e in result.embeddings]
    return vectors


def refresh() -> int:
    """Reload files + sheet. Only new or changed text is embedded. Returns the number of pieces."""
    global _chunks
    docs = _read_files()
    try:
        docs += _read_sheet()
    except Exception as e:
        print(f"[knowledge] Google Sheet not loaded: {e}")
    pieces = [{"title": d["title"], "url": d["url"], "text": p} for d in docs for p in _split(d["text"])]

    with _lock:
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}
        missing = [p["text"] for p in pieces if p["text"] not in cache]
        if missing:
            cache.update(zip(missing, _embed(missing, "RETRIEVAL_DOCUMENT")))
        cache = {p["text"]: cache[p["text"]] for p in pieces}  # forget deleted text
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
        _chunks = [{**p, "vector": cache[p["text"]]} for p in pieces]
    return len(_chunks)


def start_auto_refresh(minutes: float = 5):
    def loop():
        while True:
            time.sleep(minutes * 60)
            try:
                refresh()
            except Exception as e:
                print(f"[knowledge] refresh failed: {e}")
    threading.Thread(target=loop, daemon=True).start()


def refresh_if_old(minutes: float = 5):
    """For the website version (webapp.py), which can't run a background loop: reload on a message
    when the information is older than `minutes`."""
    global _last_refresh
    if time.time() - _last_refresh > minutes * 60:
        _last_refresh = time.time()
        try:
            print(f"[knowledge] {refresh()} pieces of club information loaded.")
        except Exception as e:
            print(f"[knowledge] refresh failed: {e}")


def _similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)


def search(query: str, k: int = 4) -> list[dict]:
    if not _chunks:
        return []
    q = _embed([query], "RETRIEVAL_QUERY")[0]
    best = sorted(_chunks, key=lambda c: _similarity(q, c["vector"]), reverse=True)[:k]
    return [{"title": c["title"], "url": c["url"], "text": c["text"]} for c in best]
