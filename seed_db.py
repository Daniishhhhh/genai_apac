import os
import sys
import PyPDF2
import sqlalchemy
import google.auth
import google.auth.transport.requests
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

from tools.fssai_rag_tool import get_db_connection, _validate_env

PDF_PATH = "data/fssai_gazette.pdf"


def get_embeddings_via_rest(texts: list, project_id: str, region: str = "us-central1") -> list:
    """Direct REST call to Vertex AI — bypasses broken metadata server credentials."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    token = credentials.token

    url = (
        f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/{region}/publishers/google/models/text-embedding-004:predict"
    )
    payload = {
        "instances": [
            {"content": t, "task_type": "RETRIEVAL_DOCUMENT"} for t in texts
        ]
    }
    resp = http_requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return [p["embeddings"]["values"] for p in resp.json()["predictions"]]


def seed_fssai_database():
    # ── Validate env ──────────────────────────────────────────────────────────
    try:
        env = _validate_env()
    except EnvironmentError as e:
        print(e); sys.exit(1)

    PROJECT_ID = env["GOOGLE_CLOUD_PROJECT"]
    REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    print(f"\n--- Starting Seeding Process for {PROJECT_ID} ---")

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

    # ── Test ADC credentials ──────────────────────────────────────────────────
    print("Checking ADC credentials...")
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(google.auth.transport.requests.Request())
        print(f"✅ ADC credentials valid. Token prefix: {credentials.token[:20]}...")
    except Exception as e:
        print(f"❌ ADC credentials failed: {e}")
        print("   Run: gcloud auth application-default login")
        sys.exit(1)

    # ── Test embedder with one chunk ──────────────────────────────────────────
    print("Testing embedding API with one chunk...")
    try:
        test_result = get_embeddings_via_rest(["test FSSAI regulation"], PROJECT_ID, REGION)
        print(f"✅ Embedder working. Vector dimension: {len(test_result[0])}")
    except Exception as e:
        print(f"❌ Embedding API failed: {e}")
        print("   Check: gcloud services enable aiplatform.googleapis.com")
        sys.exit(1)

    # ── Connect AlloyDB ────────────────────────────────────────────────────────
    print("Connecting to AlloyDB...")
    try:
        engine = get_db_connection()
        with engine.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        print("✅ AlloyDB connected.")
    except Exception as e:
        print(f"❌ AlloyDB failed: {e}"); sys.exit(1)

    # ── Create schema ──────────────────────────────────────────────────────────
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

    # ── Embed and insert ───────────────────────────────────────────────────────
    print(f"Embedding and inserting {len(chunks)} chunks (batch size 5)...")
    batch_size = 5
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    inserted = 0

    with engine.connect() as conn:
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            try:
                embeddings = get_embeddings_via_rest(batch_texts, PROJECT_ID, REGION)
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