"""
Quick Setup Guide for NutriGuard Pro
====================================

This file provides a quick-start checklist for setting up and running NutriGuard Pro.

Prerequisites Checklist:
------------------------
□ Python 3.10+ installed
□ Google Cloud account with billing enabled
□ AlloyDB instance running
□ Gemini API key obtained
□ Vertex AI API enabled

Environment Setup (5 minutes):
------------------------------

1. Install dependencies:
   pip install -r requirements.txt

2. Create .env file with these variables:
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_API_KEY=your-gemini-api-key
   GOOGLE_GENAI_MODEL=gemini-2.5-flash
   ALLOYDB_INSTANCE_URI=projects/.../instances/...
   ALLOYDB_PUBLIC_IP=your-alloydb-ip
   DB_NAME=fssai_db
   DB_USER=postgres
   DB_PASS=your-password
   PROXY_PORT=5432

3. Get AlloyDB Public IP:
   gcloud alloydb instances describe nutriguard-primary \
     --cluster=nutriguard-cluster \
     --region=us-central1 \
     --format='value(publicIpAddress)'

Database Setup (10-15 minutes):
-------------------------------

1. Connect to AlloyDB:
   psql -h YOUR_ALLOYDB_IP -U postgres -d fssai_db

2. Enable pgvector:
   CREATE EXTENSION IF NOT EXISTS vector;

3. Seed FSSAI regulations:
   python3 seed_db.py

   This will:
   - Parse data/fssai_gazette.pdf
   - Generate 768-dim embeddings
   - Store ~500 regulation chunks in AlloyDB

4. Seed ingredient database:
   python3 seed_v2.py

   This creates:
   - ingredient_health_map (35+ harmful ingredients)
   - fssai_additives (INS codes)
   - fssai_fruit_content_rules

Run the Application:
-------------------

Option 1 - CLI Mode:
   python3 app.py data/test_label.jpg

Option 2 - Web UI:
   streamlit run streamlit_app.py
   # Navigate to http://localhost:8501

Testing the Installation:
-------------------------

1. Syntax check:
   python3 -m py_compile app.py streamlit_app.py

2. Test label extraction:
   python3 -c "from agents.label_extractor import extract_label_from_image; \
               print(extract_label_from_image('data/test_label.jpg'))"

3. Test NutriScore:
   python3 -c "from agents.nutri_score import compute_nutri_score; \
               print(compute_nutri_score({'calories_kcal': 500, 'total_sugars_g': 15, \
               'sodium_mg': 300, 'saturated_fat_g': 5, 'protein_g': 8, 'fiber_g': 2}))"

4. Test database connection:
   python3 -c "from tools.fssai_rag_tool import get_db_connection; \
               engine = get_db_connection(); print('✅ Database connected')"

Common Issues & Fixes:
---------------------

Issue: "AlloyDB connection failed"
Fix: Verify ALLOYDB_PUBLIC_IP is set correctly in .env

Issue: "Dimension mismatch: got 1024, expected 768"
Fix: Already fixed! Check tools/fssai_rag_tool.py line 105 has outputDimensionality: 768

Issue: "GOOGLE_API_KEY not set"
Fix: Ensure .env file is in project root and contains valid API key

Issue: "KeyError: mandatory_warnings"
Fix: Already fixed! Schema now includes mandatory_warnings field

Project Structure Overview:
---------------------------

genai_apac/
├── agents/              # 5 AI agents
├── tools/               # FSSAI RAG tool
├── schemas/             # Pydantic models
├── data/                # Test images + FSSAI PDF
├── app.py               # CLI application
├── streamlit_app.py     # Web UI
├── seed_db.py           # FSSAI regulations seeder
├── seed_v2.py           # Ingredient DB seeder
├── README.md            # Full documentation
└── ARCHITECTURE.md      # System architecture

Next Steps:
----------

1. Read README.md for full documentation
2. Review ARCHITECTURE.md for system design
3. Test with sample images in data/
4. Configure health profiles in streamlit UI
5. Deploy to Cloud Run (optional)

Support:
--------
- Documentation: README.md
- Architecture: ARCHITECTURE.md
- Issues: https://github.com/Daniishhhhh/genai_apac/issues

Built with ❤️ for healthier India 🇮🇳
"""