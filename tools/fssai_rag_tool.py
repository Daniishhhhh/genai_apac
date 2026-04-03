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

    # AFTER
    return sqlalchemy.create_engine(
    connection_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"ssl_context": False},   # AlloyDB on public IP: plain TCP, no SSL
)

# Remove the 'import vertexai' and 'vertexai.init' lines

# Inside tools/fssai_rag_tool.py

# tools/fssai_rag_tool.py

def query_fssai_regulations(claim: str, nutrient_context: str) -> dict:
    import requests as http_requests
    import sqlalchemy

    api_key = os.getenv("GOOGLE_API_KEY")
    query_text = f"FSSAI regulation for claim: {claim}. Nutrients: {nutrient_context}"

    # We use v1beta to support outputDimensionality
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"

    payload = {
        "content": {"parts": [{"text": query_text}]},
        "taskType": "RETRIEVAL_QUERY",
        "outputDimensionality": 768  # <--- THIS FIXES THE DIMENSION ERROR
    }

    resp = http_requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    
    query_embedding = resp.json()["embedding"]["values"]
    
    # Ensure the database connection uses the correct host/port
    engine = get_db_connection()
    with engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT regulation_text, claim_type, threshold_value, threshold_unit,
                1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                FROM fssai_regulations
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT 3
            """),
            {"emb": str(query_embedding)}
        )
        rows = result.fetchall()

    if not rows: return {"found": False}
    top = rows[0]
    return {
        "found": True, "regulation_text": top[0], "similarity_score": float(top[4])
    }
    top = rows[0]
    return {
        "found": True,
        "claim": claim,
        "regulation_text": top[0],
        "claim_type": top[1],
        "threshold_value": top[2],
        "threshold_unit": top[3],
        "similarity_score": float(top[4])
    }