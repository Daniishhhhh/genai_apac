import os
import sys
import PyPDF2
import sqlalchemy
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

from tools.fssai_rag_tool import get_db_connection, _validate_env

PDF_PATH = "data/fssai_gazette.pdf"

def get_embeddings_via_rest(texts: list, api_key: str) -> list:
    embeddings = []
    for text in texts:
        resp = http_requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "content": {"parts": [{"text": text}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                "outputDimensionality": 768
            },
            timeout=30,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"]["values"])
    return embeddings

def seed_fssai_database():
    # ── Validate env ──────────────────────────────────────────────────────────
    try:
        env = _validate_env()
    except EnvironmentError as e:
        print(e); sys.exit(1)

    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        print("❌ GOOGLE_API_KEY not set in .env"); sys.exit(1)

    print(f"\n--- Starting Seeding Process for {env['GOOGLE_CLOUD_PROJECT']} ---")

    # ── Parse PDF ─────────────────────────────────────────────────────────────
    if not os.path.exists(PDF_PATH):
        print(f"❌ PDF not found at '{PDF_PATH}'"); sys.exit(1)

    print(f"Parsing PDF: {PDF_PATH}...")
    chunks = []
    with open(PDF_PATH, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        for page in reader.pages:
            text = page.extract_text()
            if not text: continue
            words = text.split()
            for i in range(0, len(words), 80):
                chunk = " ".join(words[i:i+80])
                if len(chunk) > 50:
                    chunks.append(chunk)

    print(f"✅ Created {len(chunks)} text chunks from {total_pages} pages.")

    # ── Test embedder with one chunk ──────────────────────────────────────────
    print("Testing embedding API with one chunk...")
    try:
        test_result = get_embeddings_via_rest(["test FSSAI regulation"], API_KEY)  # ← fixed
        print(f"✅ Embedder working. Vector dimension: {len(test_result[0])}")
    except Exception as e:
        print(f"❌ Embedding API failed: {e}")
        print("   Check: GOOGLE_API_KEY is set correctly in .env")
        sys.exit(1)

    # ── Connect AlloyDB ───────────────────────────────────────────────────────
    print("Connecting to AlloyDB...")
    try:
        engine = get_db_connection()
        with engine.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        print("✅ AlloyDB connected.")
    except Exception as e:
        print(f"❌ AlloyDB failed: {e}"); sys.exit(1)

    # ── Create schema ─────────────────────────────────────────────────────────
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS fssai_regulations (
                id               SERIAL PRIMARY KEY,
                regulation_text  TEXT NOT NULL,
                claim_type       VARCHAR(100),
                threshold_value  FLOAT,
                threshold_unit   VARCHAR(50),
                embedding        vector(768)
            );
        """))
        if "--reset" in sys.argv:
            conn.execute(sqlalchemy.text("TRUNCATE TABLE fssai_regulations;"))
            print("  ⚠️  Table cleared.")
        conn.commit()
    print("✅ Schema ready.")

    # ── Embed and insert ──────────────────────────────────────────────────────
    print(f"Embedding and inserting {len(chunks)} chunks (batch size 5)...")
    batch_size    = 5
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    inserted      = 0

    with engine.connect() as conn:
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i:i+batch_size]
            batch_num   = (i // batch_size) + 1
            try:
                embeddings = get_embeddings_via_rest(batch_texts, API_KEY)  # ← fixed
            except Exception as e:
                print(f"  ⚠️  Batch {batch_num} failed: {e}. Skipping.")
                continue

            for text, emb in zip(batch_texts, embeddings):
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO fssai_regulations (regulation_text, embedding)
                        VALUES (:text, CAST(:emb AS vector))
                    """),
                    {"text": text, "emb": str(emb)}
                )
                inserted += 1

            conn.commit()
            print(f"  ✅ Batch {batch_num}/{total_batches} — {inserted} rows total")

    print(f"\n🎉 Done! {inserted} regulation chunks stored in AlloyDB.")
    print("Next: python3 app.py data/test_label.jpg")


if __name__ == "__main__":
    seed_fssai_database()