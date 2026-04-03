# NutriGuard Pro 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-FF4B4B.svg)](https://streamlit.io)

**NutriGuard Pro** is an AI-powered food safety and FSSAI compliance auditor that analyzes Indian packaged food labels to detect regulatory violations, assess nutritional quality, flag harmful ingredients, and provide personalized health verdicts based on user profiles (General, Diabetic, Child, Pregnant, Hypertension).

---

## 🎯 Key Features

### 🔍 **Multi-Agent Intelligence System**
- **5 Specialized AI Agents** working in sequence:
  - **LabelExtractorAgent**: Vision AI extracts structured data from food label images
  - **RegulatoryAuditorAgent**: Audits claims against FSSAI regulations using RAG (Retrieval-Augmented Generation)
  - **SanityAgent**: Cross-validates extracted data to prevent AI hallucinations
  - **WellnessAdvisorAgent**: Computes NutriScore (A-E) and personalized consumption verdicts
  - **EducationAgent**: Flags harmful ingredients, detects deceptive marketing, suggests healthy alternatives

### 🇮🇳 **India-Specific Compliance**
- Full FSSAI (Food Safety and Standards Authority of India) regulatory compliance checking
- Automated detection of HFSS (High Fat, Sugar, Salt) violations
- Profile-specific hard stops (e.g., caffeine warnings for children and pregnant users)
- RAG-powered FSSAI Gazette PDF search with semantic embeddings

### 🩺 **Personalized Health Analysis**
- **5 Health Profiles**: General, Diabetic, Child (under 12), Pregnant, Hypertension
- Dynamic NutriScore recalculation based on user profile
- RDA (Recommended Dietary Allowance) comparisons using ICMR + WHO guidelines
- Ingredient-level risk assessment with long-term health impact explanations

### 🧪 **Ingredient Intelligence**
- Database of **35+ high-risk additives** (INS codes, artificial colors, preservatives)
- Deception detection (e.g., "Made with Real Fruit" when fruit is 4th ingredient)
- Smart Swaps: Indian kitchen alternatives (e.g., Jaggery instead of HFCS)

### 🎨 **Professional UI**
- Modern dark-themed Streamlit interface
- Interactive NutriScore badges (color-coded A-E grades)
- Tabbed reports: Health Impact, Ingredients, FSSAI Compliance, RDA Breakdown, Alternatives
- Mobile-responsive design

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Upload (Streamlit)                   │
│                  Food Label Image (JPG/PNG)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NutriGuardOrchestrator (ADK)                    │
│                  Sequential Agent Pipeline                   │
└───┬────────────────────────────────────────────────────┬─────┘
    │                                                     │
    │  ┌──────────────────────────────────────────┐     │
    └─▶│  1. LabelExtractorAgent                  │     │
       │     - Gemini 2.0 Flash Vision            │     │
       │     - Extracts JSON (nutrients, claims)  │     │
       └──────────────┬───────────────────────────┘     │
                      │                                  │
                      ▼                                  │
       ┌──────────────────────────────────────────┐     │
       │  2. RegulatoryAuditorAgent               │     │
       │     - FSSAI RAG Tool                     │     │
       │     - AlloyDB Vector Search              │     │
       │     - Hard Limit Validation              │     │
       └──────────────┬───────────────────────────┘     │
                      │                                  │
                      ▼                                  │
       ┌──────────────────────────────────────────┐     │
       │  3. SanityAgent                          │     │
       │     - Cross-validation                   │     │
       │     - Hallucination prevention           │     │
       └──────────────┬───────────────────────────┘     │
                      │                                  │
                      ▼                                  │
       ┌──────────────────────────────────────────┐     │
       │  4. WellnessAdvisorAgent                 │     │
       │     - NutriScore Calculator              │     │
       │     - Profile-based Verdict Logic        │     │
       │     - RDA Comparisons                    │     │
       └──────────────┬───────────────────────────┘     │
                      │                                  │
                      ▼                                  │
       ┌──────────────────────────────────────────┐     │
       │  5. EducationAgent                       │     │
       │     - Ingredient DB Query                │     │
       │     - Deception Pattern Matching         │     │
       │     - Smart Swaps Recommendation         │     │
       └──────────────┬───────────────────────────┘     │
                      │                                  │
                      ▼                                  │
                  Final Report                           │
                      │                                  │
                      └──────────────────────────────────┘
```

### Technology Stack

**AI & ML:**
- **Gemini 2.0 Flash / 2.5 Flash**: Vision AI for label extraction, LLM for agent reasoning
- **Google ADK (Agent Development Kit)**: Multi-agent orchestration framework
- **Vertex AI**: Text embeddings for semantic search (`text-embedding-004`)

**Database & Vector Search:**
- **AlloyDB for PostgreSQL**: Google Cloud's high-performance database
- **pgvector Extension**: Vector similarity search for FSSAI regulations
- **Connection**: Direct public IP connection with pg8000 driver

**Backend:**
- **Python 3.10+**: Core application language
- **Pydantic**: Data validation and schema enforcement
- **asyncio**: Asynchronous agent execution
- **SQLAlchemy**: Database ORM

**Frontend:**
- **Streamlit 1.55.0**: Interactive web application
- **PIL (Pillow)**: Image processing
- **Custom CSS**: Dark-themed, mobile-responsive UI

**Document Processing:**
- **PyPDF2**: FSSAI Gazette PDF parsing
- **LangChain**: PDF chunking and text splitting

**Deployment:**
- **Google Cloud Platform**: AlloyDB, Vertex AI
- **Environment Variables**: `.env` configuration
- **AlloyDB Auth Proxy**: Secure database connections (optional)

---

## 📋 Prerequisites

### Required Accounts & Services
1. **Google Cloud Account** with billing enabled
2. **AlloyDB Instance** (PostgreSQL-compatible)
3. **Vertex AI API** enabled
4. **Gemini API Key** (for embeddings and vision)

### Required Tools
- Python 3.10 or higher
- pip (Python package manager)
- Git
- (Optional) AlloyDB Auth Proxy binary

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Daniishhhhh/genai_apac.git
cd genai_apac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=your-gemini-api-key

# Gemini Model Selection
GOOGLE_GENAI_MODEL=gemini-2.5-flash

# AlloyDB Configuration
ALLOYDB_INSTANCE_URI=projects/YOUR_PROJECT/locations/us-central1/clusters/nutriguard-cluster/instances/nutriguard-primary
ALLOYDB_PUBLIC_IP=your-alloydb-public-ip
DB_NAME=fssai_db
DB_USER=postgres
DB_PASS=your-database-password
PROXY_PORT=5432
```

**How to Get AlloyDB Public IP:**
```bash
gcloud alloydb instances describe nutriguard-primary \
  --cluster=nutriguard-cluster \
  --region=us-central1 \
  --format='value(publicIpAddress)'
```

### 4. Setup Database

#### 4.1 Enable pgvector Extension
```bash
# Connect to AlloyDB via Cloud Shell or proxy
psql -h YOUR_ALLOYDB_IP -U postgres -d fssai_db

# Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 4.2 Seed FSSAI Regulations Database
```bash
# Ensure data/fssai_gazette.pdf exists
python3 seed_db.py
```

This will:
- Parse the FSSAI Gazette PDF
- Create 80-word chunks
- Generate embeddings using Vertex AI
- Store in `fssai_regulations` table with pgvector

#### 4.3 Seed Ingredient & Additive Data
```bash
python3 seed_v2.py
```

This creates:
- `fssai_additives`: INS codes, health concerns, ADI limits
- `fssai_fruit_content_rules`: Minimum fruit % requirements
- `ingredient_health_map`: 35+ harmful ingredients with alternatives

### 5. Verify Installation

```bash
# Test syntax
python3 -m py_compile app.py streamlit_app.py

# Test CLI mode
python3 app.py data/test_label.jpg
```

---

## 🎮 Usage

### Command-Line Mode

```bash
python3 app.py data/test_label.jpg
```

**Output:**
```
🔍 Auditing: data/test_label.jpg
─────────────────────────────────────────────

[LabelExtractorAgent]
Extracted: Coca-Cola 250ml, Sugar: 10.6g, Sodium: 10mg...

[RegulatoryAuditorAgent]
Checking claims: "Refreshing Taste"...
Status: Compliant

[SanityAgent]
Validation complete. No overrides needed.

[WellnessAdvisorAgent]
NutriScore: D
Verdict: Occasional consumption
Reason: High sugar (10.6g per 100ml)

[EducationAgent]
Flagged: Caffeine (High Risk)
Alternative: Coconut water, Nimbu pani

─────────────────────────────────────────────
✅ Audit complete.
```

### Web Interface (Streamlit)

```bash
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501`

**Features:**
1. **Select Health Profile** (General / Diabetic / Child / Pregnant / Hypertension)
2. **Upload Label Images** (front + back of package)
3. **Run Multi-Agent Audit** (5-10 seconds processing)
4. **View Interactive Report**:
   - NutriScore badge (A-E color-coded)
   - Traffic light verdict (Regular / Occasional / Rare)
   - 5 tabs: Health Impact, Ingredients, FSSAI Compliance, RDA Breakdown, Alternatives

**Example Output:**
- **Product**: Maggi 2-Minute Noodles
- **NutriScore**: D
- **Verdict**: Occasional (High sodium: 810mg/100g)
- **Flagged**: MSG (INS 621), Maida, Palm Oil
- **FSSAI Violations**: 1 (Exceeds sodium threshold for "Low Sodium" claim)
- **Smart Swaps**: Replace MSG with Natural Spices, Use whole wheat pasta

---

## 🗂️ Project Structure

```
genai_apac/
├── agents/                     # AI Agent definitions
│   ├── label_extractor.py      # Vision AI → JSON extraction
│   ├── regulatory_auditor.py   # FSSAI compliance checker
│   ├── sanity_agent.py         # Data validation
│   ├── wellness_advisor.py     # NutriScore calculator
│   ├── education_agent.py      # Ingredient analyzer
│   ├── user_advisor.py         # Report formatter
│   └── nutri_score.py          # NutriScore algorithm
│
├── tools/                      # Utility functions
│   └── fssai_rag_tool.py       # AlloyDB vector search
│
├── schemas/                    # Data models
│   ├── label_schema.py         # Pydantic models
│   └── product.py              # Product schemas
│
├── data/                       # Test assets
│   ├── fssai_gazette.pdf       # FSSAI regulations PDF
│   ├── test_label.jpg          # Sample label image
│   └── test_label1.png         # Sample label image
│
├── local_cache/                # Cached data
│   └── fssai_norms.json        # Pre-computed norms
│
├── .streamlit/                 # Streamlit config
│   └── config.toml             # Theme settings
│
├── app.py                      # CLI application
├── streamlit_app.py            # Web UI application
├── seed_db.py                  # FSSAI regulations seeder
├── seed_v2.py                  # Ingredient DB seeder
├── requirements.txt            # Python dependencies
├── .env.save                   # Environment template
├── .gitignore                  # Git ignore rules
├── alloydb-auth-proxy          # AlloyDB proxy binary (optional)
└── README.md                   # This file
```

---

## 🔧 Configuration

### Health Profiles & RDA Values

**Defined in:** `streamlit_app.py` (lines 310-316)

```python
RDAS = {
    "General":          {"sugar": 50,  "sodium": 2000, "sat_fat": 22, "calories": 2000, "protein": 60},
    "Diabetic":         {"sugar": 25,  "sodium": 1500, "sat_fat": 20, "calories": 1800, "protein": 60},
    "Child (under 12)": {"sugar": 25,  "sodium": 1200, "sat_fat": 15, "calories": 1600, "protein": 35},
    "Pregnant":         {"sugar": 50,  "sodium": 2000, "sat_fat": 22, "calories": 2400, "protein": 75},
    "Hypertension":     {"sugar": 50,  "sodium": 1000, "sat_fat": 15, "calories": 2000, "protein": 60},
}
```

### FSSAI Hard Limits

**Defined in:** `agents/regulatory_auditor.py` (lines 32-38)

```python
HARD_LIMITS = {
    "sugar_claims":     {"nutrient": "total_sugars_g",  "limit": 0.5,  "unit": "g/100g"},
    "sodium_claims":    {"nutrient": "sodium_mg",       "limit": 120,  "unit": "mg/100g"},
    "fat_claims":       {"nutrient": "saturated_fat_g", "limit": 0.5,  "unit": "g/100g"},
    "trans_fat_claims": {"nutrient": "trans_fat_g",     "limit": 0.2,  "unit": "g/100g"},
    "protein_claims":   {"nutrient": "protein_g",       "limit": 10.0, "unit": "g/100g"},
}
```

### NutriScore Grade Thresholds

**Defined in:** `agents/nutri_score.py` (lines 77-82)

```python
def _score_to_grade(score: int) -> str:
    if score <= -1: return "A"
    if score <=  2: return "B"
    if score <= 10: return "C"
    if score <= 18: return "D"
    return "E"
```

---

## 🐛 Debugging & Troubleshooting

### Common Issues

#### 1. **AlloyDB Connection Failed**

**Error:**
```
❌ ALLOYDB_PUBLIC_IP not set in .env
```

**Solution:**
```bash
# Get AlloyDB public IP
gcloud alloydb instances describe nutriguard-primary \
  --cluster=nutriguard-cluster \
  --region=us-central1 \
  --format='value(publicIpAddress)'

# Add to .env
ALLOYDB_PUBLIC_IP=35.x.x.x
```

#### 2. **Embedding Dimension Mismatch**

**Error:**
```
dimension mismatch: got 1024, expected 768
```

**Fix:** Already applied in `tools/fssai_rag_tool.py` (line 105):
```python
"outputDimensionality": 768  # Forces 768-dim embeddings
```

#### 3. **Duplicate Return Statement**

**Error:**
```
unreachable code after return statement
```

**Fix:** Already applied in `tools/fssai_rag_tool.py` (removed duplicate lines 131-132)

#### 4. **Missing mandatory_warnings Field**

**Error:**
```
KeyError: 'mandatory_warnings'
```

**Fix:** Already applied in `agents/label_extractor.py` (line 35) - schema now includes `mandatory_warnings` array

#### 5. **Gemini API Rate Limits**

**Error:**
```
429 Too Many Requests
```

**Solution:**
- Reduce batch size in `seed_db.py` (line 105) from 5 to 3
- Add delays between requests
- Use service account with higher quotas

---

## 🧪 Testing

### Unit Tests (Manual)

```bash
# Test label extraction
python3 -c "from agents.label_extractor import extract_label_from_image; print(extract_label_from_image('data/test_label.jpg'))"

# Test NutriScore calculation
python3 -c "from agents.nutri_score import compute_nutri_score; print(compute_nutri_score({'calories_kcal': 500, 'total_sugars_g': 15, 'sodium_mg': 300, 'saturated_fat_g': 5, 'protein_g': 8, 'fiber_g': 2}))"

# Test FSSAI RAG
python3 -c "from tools.fssai_rag_tool import query_fssai_regulations; print(query_fssai_regulations('sugar free', 'Sugar: 0.3g'))"
```

### Integration Test

```bash
# Full pipeline test
python3 app.py data/test_label.jpg
```

**Expected Output:**
- All 5 agents execute successfully
- No Python errors
- Final report with NutriScore, verdict, and flagged ingredients

---

## 📊 Database Schema

### fssai_regulations Table

```sql
CREATE TABLE fssai_regulations (
    id               SERIAL PRIMARY KEY,
    regulation_text  TEXT NOT NULL,
    claim_type       VARCHAR(100),
    threshold_value  FLOAT,
    threshold_unit   VARCHAR(50),
    embedding        vector(768)
);

CREATE INDEX ON fssai_regulations USING ivfflat (embedding vector_cosine_ops);
```

### ingredient_health_map Table

```sql
CREATE TABLE ingredient_health_map (
    id                  SERIAL PRIMARY KEY,
    ingredient_name     VARCHAR(255) UNIQUE NOT NULL,
    health_concern      TEXT NOT NULL,
    natural_alternative TEXT,
    risk_level          VARCHAR(20) CHECK (risk_level IN ('Low', 'Medium', 'High'))
);
```

### fssai_additives Table

```sql
CREATE TABLE fssai_additives (
    id                  SERIAL PRIMARY KEY,
    ins_code            VARCHAR(20) UNIQUE NOT NULL,
    common_name         VARCHAR(255),
    permitted_foods     TEXT,
    prohibited_foods    TEXT,
    health_concern      TEXT,
    adi_mg_per_kg       INT
);
```

---

## 🚢 Deployment

### Option 1: Cloud Run (Recommended)

```bash
# Build container
docker build -t gcr.io/YOUR_PROJECT/nutriguard .

# Push to GCR
docker push gcr.io/YOUR_PROJECT/nutriguard

# Deploy
gcloud run deploy nutriguard \
  --image gcr.io/YOUR_PROJECT/nutriguard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY,ALLOYDB_PUBLIC_IP=$ALLOYDB_PUBLIC_IP
```

### Option 2: Compute Engine / VM

```bash
# SSH into VM
gcloud compute ssh nutriguard-vm

# Clone repo and setup
git clone https://github.com/Daniishhhhh/genai_apac.git
cd genai_apac
pip3 install -r requirements.txt

# Run with nohup
nohup streamlit run streamlit_app.py --server.port 8501 &
```

### Option 3: Local Development

```bash
streamlit run streamlit_app.py
```

Access at: `http://localhost:8501`

---

## 🔒 Security Notes

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use Secret Manager in production**:
   ```bash
   gcloud secrets create google-api-key --data-file=-
   ```
3. **AlloyDB IAM Authentication** (recommended over password):
   ```python
   # In tools/fssai_rag_tool.py
   from google.cloud.alloydb.connector import Connector
   connector = Connector()
   conn = connector.connect("INSTANCE_URI", "pg8000", user="postgres")
   ```
4. **Restrict AlloyDB Public IP** to authorized networks only
5. **Use VPC Peering** for production AlloyDB access

---

## 🎓 How It Works: Agent Flow

### Sequential Execution

```
User Input (Image)
    ↓
[Agent 1: LabelExtractorAgent]
    → Gemini Vision API
    → Extracts: product_name, brand, nutrients[], ingredients[], health_claims[], mandatory_warnings[]
    → Output: ExtractedLabel JSON
    ↓
[Agent 2: RegulatoryAuditorAgent]
    → Receives: ExtractedLabel
    → For each health_claim:
        • Maps claim to nutrient group (sugar_claims, sodium_claims, etc.)
        • Checks actual value vs FSSAI hard limits
        • Queries AlloyDB vector DB for regulation text (RAG)
        • Flags violations
    → Output: ComplianceReport (flags[], overall_status, risk_score)
    ↓
[Agent 3: SanityAgent]
    → Receives: ComplianceReport
    → Cross-validates:
        • If high-severity flags exist, forces overall_status = "non_compliant"
        • Ensures product_name/brand match ExtractedLabel (fixes AI hallucinations)
    → Output: Validated ComplianceReport
    ↓
[Agent 4: WellnessAdvisorAgent]
    → Receives: ExtractedLabel + ComplianceReport + user_profile
    → Computes NutriScore:
        • Negative points: energy, sugars, sat_fat, sodium
        • Positive points: protein, fiber, fruit %
        • Final score → Grade (A-E)
    → Profile Overrides:
        • Diabetic: Doubles sugar penalty
        • Child: Auto-escalates if artificial colors present
    → Consumption Verdict: Regular / Occasional / Rare
    → Output: WellnessReport
    ↓
[Agent 5: EducationAgent]
    → Receives: ExtractedLabel
    → Queries ingredient_health_map DB (partial match)
    → Deception Pattern Matching:
        • "Made with Real Fruit" + fruit at position 3+ → Flag
        • "Sugar Free" + dextrose/fructose in ingredients → Flag
        • "High Protein" + protein < 10g/100g → Flag
    → Output: EducationReport (flagged_ingredients[], deception_flags[], swap_suggestions[])
    ↓
[Streamlit UI]
    → Merges all agent outputs
    → Renders:
        • NutriScore badge
        • Verdict pill
        • 5-tab report (Health, Ingredients, Compliance, RDA, Alternatives)
```

---

## 🤝 Contributing

We welcome contributions! Areas for improvement:

1. **Add more FSSAI regulations** to vector DB
2. **Expand ingredient_health_map** (currently 35 items)
3. **Support multilingual labels** (Hindi, Tamil, Bengali)
4. **Add barcode scanning** via EAN-13 API
5. **Export reports as PDF**

### Development Workflow

```bash
# Fork the repo
git checkout -b feature/your-feature-name

# Make changes
# Test locally
python3 app.py data/test_label.jpg

# Commit
git add .
git commit -m "feat: add barcode scanning support"

# Push and create PR
git push origin feature/your-feature-name
```

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🙏 Acknowledgments

- **FSSAI** for publicly available gazette PDFs
- **Google Cloud** for Gemini API and AlloyDB
- **Streamlit** for rapid UI development
- **LangChain** for RAG utilities

---

## 📧 Contact

**Maintainer**: Danish
**GitHub**: [Daniishhhhh/genai_apac](https://github.com/Daniishhhhh/genai_apac)
**Issues**: [Report bugs here](https://github.com/Daniishhhhh/genai_apac/issues)

---

## 🔗 Related Resources

- [FSSAI Official Website](https://www.fssai.gov.in/)
- [FSSAI Gazette (PDF Source)](https://www.fssai.gov.in/cms/food-safety-and-standards-regulations.php)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [AlloyDB Documentation](https://cloud.google.com/alloydb/docs)
- [Google ADK Documentation](https://github.com/google/adk-toolkit)
- [NutriScore Official](https://www.santepubliquefrance.fr/en/nutri-score)

---

**Built with ❤️ for healthier India** 🇮🇳
