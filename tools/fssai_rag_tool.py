import os
import sqlalchemy
from dotenv import load_dotenv
from google.cloud.alloydb.connector import Connector

load_dotenv()

import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

def _validate_env():
    required = {
        "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "ALLOYDB_INSTANCE_URI": os.getenv("ALLOYDB_INSTANCE_URI"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASS": os.getenv("DB_PASS"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(
            f"\n❌ Missing environment variables: {missing}\n"
            f"Run: source .env\n"
            f"Current values: { {k: os.getenv(k, 'NOT SET') for k in required} }"
        )
    return required

def get_embeddings_model():
    """
    Uses Vertex AI SDK directly — works with ADC in Cloud Shell.
    No API key needed. No deprecated imports.
    """
    env = _validate_env()
    vertexai.init(
        project=env["GOOGLE_CLOUD_PROJECT"],
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    return TextEmbeddingModel.from_pretrained("text-embedding-004")

def embed_texts(texts: list[str], model=None) -> list[list[float]]:
    """Embed a batch of texts using Vertex AI."""
    if model is None:
        model = get_embeddings_model()
    inputs = [TextEmbeddingInput(t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
    embeddings = model.get_embeddings(inputs)
    return [e.values for e in embeddings]

def embed_query(query: str, model=None) -> list[float]:
    """Embed a single query string."""
    if model is None:
        model = get_embeddings_model()
    inputs = [TextEmbeddingInput(query, task_type="RETRIEVAL_QUERY")]
    return model.get_embeddings(inputs)[0].values

from urllib.parse import quote_plus   # add this at the top of the file

def get_db_connection():
    env = _validate_env()

    host = os.getenv("ALLOYDB_PUBLIC_IP")
    if not host:
        raise EnvironmentError(
            "❌ ALLOYDB_PUBLIC_IP not set in .env\n"
            "Run: gcloud alloydb instances describe nutriguard-primary "
            "--cluster=nutriguard-cluster --region=us-central1 "
            "--format='value(publicIpAddress)'"
        )

    port = int(os.getenv("PROXY_PORT", "5432"))
    db   = os.getenv("DB_NAME", "fssai_db")
    user = quote_plus(env["DB_USER"])    # encodes special chars safely
    pwd  = quote_plus(env["DB_PASS"])    # 850326@Genai → 850326%40Genai

    connection_url = f"postgresql+pg8000://{user}:{pwd}@{host}:{port}/{db}"
    
    print(f"  Connecting directly → {host}:{port}/{db}")
    print(f"  User: {env['DB_USER']} (encoded for URL)")

    return sqlalchemy.create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"ssl_context": True},
    )
def query_fssai_regulations(claim: str, nutrient_context: str) -> dict:
    """MCP Tool: Vector similarity search on FSSAI regulation database."""
    import google.auth, google.auth.transport.requests, requests as http_requests

    # Get embedding via REST (same pattern as seed_db.py)
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    region     = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    query_text = f"FSSAI regulation for claim: {claim}. Nutrients: {nutrient_context}"

    resp = http_requests.post(
        f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/{region}/publishers/google/models/text-embedding-004:predict",
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        json={"instances": [{"content": query_text, "task_type": "RETRIEVAL_QUERY"}]},
        timeout=30,
    )
    resp.raise_for_status()
    query_embedding = resp.json()["predictions"][0]["embeddings"]["values"]
    emb_str = str(query_embedding)

    engine = get_db_connection()
    with engine.connect() as conn:
        # KEY FIX: pass embedding ONCE as :emb, reference it twice via CTE
        result = conn.execute(
            sqlalchemy.text("""
                WITH query_vec AS (
                    SELECT CAST(:emb AS vector) AS vec
                )
                SELECT
                    r.regulation_text,
                    r.claim_type,
                    r.threshold_value,
                    r.threshold_unit,
                    1 - (r.embedding <=> q.vec) AS similarity
                FROM fssai_regulations r, query_vec q
                ORDER BY r.embedding <=> q.vec
                LIMIT 3
            """),
            {"emb": emb_str}
        )
        rows = result.fetchall()

    if not rows:
        return {"found": False, "claim": claim}

    top = rows[0]
    return {
        "found": True,
        "claim": claim,
        "regulation_text": top[0],
        "claim_type": top[1],
        "threshold_value": top[2],
        "threshold_unit": top[3],
        "similarity_score": float(top[4]),
        "supporting_regulations": [r[0] for r in rows[1:]],
    }