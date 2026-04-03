# NutriGuard Pro - System Architecture Documentation

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Database Architecture](#database-architecture)
5. [Agent Pipeline Architecture](#agent-pipeline-architecture)
6. [Technology Stack Diagram](#technology-stack-diagram)
7. [Deployment Architecture](#deployment-architecture)

---

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                           │
│  ┌────────────────────────┐      ┌─────────────────────────────┐   │
│  │   Streamlit Web UI     │      │   CLI Application (app.py)  │   │
│  │   - Upload Interface   │      │   - Command-line audits     │   │
│  │   - Interactive Reports│      │   - Batch processing        │   │
│  │   - Dark Theme UI      │      │   - Debug mode              │   │
│  └────────────┬───────────┘      └──────────────┬──────────────┘   │
└───────────────┼──────────────────────────────────┼───────────────────┘
                │                                   │
                └───────────────┬───────────────────┘
                                │
┌───────────────────────────────┼───────────────────────────────────────┐
│                        APPLICATION LAYER                              │
│                                │                                       │
│  ┌────────────────────────────▼────────────────────────────────┐     │
│  │         NutriGuardOrchestrator (Google ADK)                 │     │
│  │         Sequential Multi-Agent Coordination                 │     │
│  └────────────────────────────┬────────────────────────────────┘     │
│                                │                                       │
│  ┌────────────────────────────▼────────────────────────────────┐     │
│  │                    AGENT PIPELINE                            │     │
│  │                                                              │     │
│  │  ┌──────────────────────────────────────────────────────┐  │     │
│  │  │ 1. LabelExtractorAgent                               │  │     │
│  │  │    - Vision AI (Gemini 2.0/2.5 Flash)               │  │     │
│  │  │    - Schema-enforced JSON extraction                │  │     │
│  │  │    - Multi-image stitching                          │  │     │
│  │  └──────────────────────┬───────────────────────────────┘  │     │
│  │                         │                                    │     │
│  │  ┌──────────────────────▼───────────────────────────────┐  │     │
│  │  │ 2. RegulatoryAuditorAgent                            │  │     │
│  │  │    - FSSAI compliance checking                       │  │     │
│  │  │    - Hard limit validation                           │  │     │
│  │  │    - RAG-powered regulation lookup                   │  │     │
│  │  └──────────────────────┬───────────────────────────────┘  │     │
│  │                         │                                    │     │
│  │  ┌──────────────────────▼───────────────────────────────┐  │     │
│  │  │ 3. SanityAgent                                        │  │     │
│  │  │    - Cross-validation logic                          │  │     │
│  │  │    - Hallucination prevention                        │  │     │
│  │  │    - Data consistency enforcement                    │  │     │
│  │  └──────────────────────┬───────────────────────────────┘  │     │
│  │                         │                                    │     │
│  │  ┌──────────────────────▼───────────────────────────────┐  │     │
│  │  │ 4. WellnessAdvisorAgent                              │  │     │
│  │  │    - NutriScore calculation (A-E)                    │  │     │
│  │  │    - Profile-specific risk assessment               │  │     │
│  │  │    - RDA comparison (ICMR + WHO)                     │  │     │
│  │  └──────────────────────┬───────────────────────────────┘  │     │
│  │                         │                                    │     │
│  │  ┌──────────────────────▼───────────────────────────────┐  │     │
│  │  │ 5. EducationAgent                                     │  │     │
│  │  │    - Ingredient risk analysis                        │  │     │
│  │  │    - Deception pattern matching                      │  │     │
│  │  │    - Smart swaps recommendation                      │  │     │
│  │  └──────────────────────────────────────────────────────┘  │     │
│  │                                                              │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                         DATA & AI SERVICES LAYER                       │
│                                                                        │
│  ┌───────────────────┐    ┌──────────────────┐   ┌─────────────────┐│
│  │   Gemini API      │    │   Vertex AI      │   │  AlloyDB        ││
│  │   - Vision Models │    │   - Embeddings   │   │  (PostgreSQL)   ││
│  │   - LLM Reasoning │    │   - text-emb-004 │   │  + pgvector     ││
│  │   - JSON Mode     │    │   - 768-dim      │   │  - Vector Search││
│  └───────────────────┘    └──────────────────┘   └─────────────────┘│
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Database Tables                             │  │
│  │  - fssai_regulations        (Vector search for regulations)    │  │
│  │  - ingredient_health_map    (Ingredient risk database)         │  │
│  │  - fssai_additives          (INS codes & ADI limits)           │  │
│  │  - fssai_fruit_content_rules (Minimum fruit % regulations)     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### Frontend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit UI (streamlit_app.py)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐       ┌──────────────────────────┐  │
│  │  Navigation Tabs     │       │  State Management        │  │
│  │  - Home              │       │  - session_state         │  │
│  │  - About             │       │  - audit_data cache      │  │
│  │  - AI Architecture   │       │  - scanned_profile       │  │
│  └──────────────────────┘       └──────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Home Tab Components                           │  │
│  │  ┌──────────────────┐    ┌──────────────────────────┐   │  │
│  │  │ Profile Selector │    │ File Uploader Widget     │   │  │
│  │  │ - 5 Health Types │    │ - Multi-image support    │   │  │
│  │  └──────────────────┘    └──────────────────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │         Audit Button & Status Display           │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │              Results Renderer                     │   │  │
│  │  │  - NutriScore Badge                              │   │  │
│  │  │  - Product Info Card                             │   │  │
│  │  │  - 5 Tabbed Reports                              │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Helper Functions                              │  │
│  │  - run_audit_async()    : Agent orchestration           │  │
│  │  - parse_json()         : AI output parsing             │  │
│  │  - render_results()     : Report rendering              │  │
│  │  - render_pbar()        : RDA progress bars             │  │
│  │  - verdict_pill()       : Verdict UI component          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Agent Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Agent Components                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Each Agent = LlmAgent + FunctionTool                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ LabelExtractorAgent                                        │ │
│  │  ┌─────────────────────┐     ┌──────────────────────────┐ │ │
│  │  │   LlmAgent          │────▶│  FunctionTool            │ │ │
│  │  │   - Instructions    │     │  extract_label_from_image│ │ │
│  │  │   - Model: Gemini   │     │  - Schema validation     │ │ │
│  │  └─────────────────────┘     │  - Vision API call       │ │ │
│  │                               └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ RegulatoryAuditorAgent                                     │ │
│  │  ┌─────────────────────┐     ┌──────────────────────────┐ │ │
│  │  │   LlmAgent          │────▶│  FunctionTool            │ │ │
│  │  │   - FSSAI Rules     │     │  audit_label_claims()    │ │ │
│  │  │   - Profile Logic   │     │  - Hard limit checks     │ │ │
│  │  └─────────────────────┘     │  - RAG query             │ │ │
│  │                               └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ SanityAgent                                                │ │
│  │  ┌─────────────────────┐     ┌──────────────────────────┐ │ │
│  │  │   LlmAgent          │────▶│  FunctionTool            │ │ │
│  │  │   - Validator       │     │  enforce_global_truth()  │ │ │
│  │  └─────────────────────┘     │  - Override logic        │ │ │
│  │                               └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ WellnessAdvisorAgent                                       │ │
│  │  ┌─────────────────────┐     ┌──────────────────────────┐ │ │
│  │  │   LlmAgent          │────▶│  FunctionTool            │ │ │
│  │  │   - Dietitian       │     │  generate_wellness_report│ │ │
│  │  │   - Clinical Logic  │     │  - NutriScore calc       │ │ │
│  │  └─────────────────────┘     │  - compute_nutri_score() │ │ │
│  │                               └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ EducationAgent                                             │ │
│  │  ┌─────────────────────┐     ┌──────────────────────────┐ │ │
│  │  │   LlmAgent          │────▶│  FunctionTool            │ │ │
│  │  │   - Toxicologist    │     │  analyse_ingredients()   │ │ │
│  │  │   - Educator        │     │  - DB lookup             │ │ │
│  │  └─────────────────────┘     │  - Deception check       │ │ │
│  │                               └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagram

### Request Flow (User → Report)

```
┌────────────┐
│   User     │
│ Uploads    │
│  Image     │
└─────┬──────┘
      │
      │ 1. HTTP POST (Streamlit)
      ▼
┌─────────────────┐
│  Streamlit App  │
│  - Stitch images│
│  - Save temp    │
└─────┬───────────┘
      │
      │ 2. Call run_audit_async(image_path, profile)
      ▼
┌───────────────────────────────────────┐
│  InMemoryRunner (Google ADK)          │
│  - Creates session                    │
│  - Iterates through agent pipeline    │
└─────┬─────────────────────────────────┘
      │
      │ 3. Sequential Agent Execution
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Pipeline                              │
│                                                                 │
│  Image → [LabelExtractor] → ExtractedLabel JSON                │
│           │                                                     │
│           └─→ Gemini Vision API (extract_label_from_image)     │
│                                                                 │
│  ExtractedLabel → [RegulatoryAuditor] → ComplianceReport       │
│                    │                                            │
│                    ├─→ audit_label_claims()                    │
│                    │   ├─→ Check hard limits                   │
│                    │   └─→ query_fssai_regulations() ───┐      │
│                    │                                     │      │
│                    │                                     ▼      │
│                    │                          ┌────────────────┐│
│                    │                          │  AlloyDB       ││
│                    │                          │  Vector Search ││
│                    │                          └────────────────┘│
│                    │                                            │
│  ComplianceReport → [SanityAgent] → Validated Report           │
│                      │                                          │
│                      └─→ enforce_global_truth()                │
│                                                                 │
│  (ExtractedLabel + ComplianceReport + Profile)                 │
│           ↓                                                     │
│  [WellnessAdvisor] → WellnessReport                            │
│           │                                                     │
│           ├─→ generate_wellness_report()                       │
│           │   └─→ compute_nutri_score()                        │
│           │                                                     │
│  ExtractedLabel → [EducationAgent] → EducationReport           │
│                    │                                            │
│                    ├─→ analyse_ingredients()                   │
│                    │   ├─→ _query_ingredient_map() ──┐         │
│                    │   │                             │         │
│                    │   │                             ▼         │
│                    │   │               ┌────────────────────┐  │
│                    │   │               │  AlloyDB           │  │
│                    │   │               │  ingredient_health_│  │
│                    │   │               │  map table         │  │
│                    │   │               └────────────────────┘  │
│                    │   │                                       │
│                    │   └─→ _check_deception()                 │
│                    │                                           │
└─────┬───────────────────────────────────────────────────────────┘
      │
      │ 4. Return aggregated results dict
      ▼
┌────────────────────────┐
│  Streamlit App         │
│  - Parse agent outputs │
│  - Render UI           │
└─────┬──────────────────┘
      │
      │ 5. Display HTML report
      ▼
┌────────────────┐
│     User       │
│  Views Report  │
└────────────────┘
```

### RAG Query Flow (FSSAI Regulation Lookup)

```
┌────────────────────────────────────┐
│  RegulatoryAuditorAgent            │
│  Needs to verify claim: "Low Sugar"│
└──────────┬─────────────────────────┘
           │
           │ 1. Call query_fssai_regulations(claim, nutrients)
           ▼
┌──────────────────────────────────────────────────────────────┐
│  tools/fssai_rag_tool.py                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Step 1: Construct query text                       │    │
│  │ "FSSAI regulation for claim: Low Sugar.            │    │
│  │  Nutrients: Sugar: 0.3g, Sodium: 50mg..."          │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                     │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │ Step 2: Generate embedding (768-dim)               │    │
│  │ → POST https://generativelanguage.googleapis.com/  │    │
│  │          v1beta/models/gemini-embedding-001        │    │
│  │   Payload:                                          │    │
│  │     {                                               │    │
│  │       "content": {"parts": [{"text": query}]},     │    │
│  │       "taskType": "RETRIEVAL_QUERY",               │    │
│  │       "outputDimensionality": 768                  │    │
│  │     }                                               │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                     │
│                       │ 3. Receive query_embedding [768 floats]
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Step 3: Vector similarity search in AlloyDB         │  │
│  │ SQL:                                                 │  │
│  │   SELECT regulation_text, claim_type,               │  │
│  │          threshold_value, threshold_unit,           │  │
│  │          1 - (embedding <=> query_emb) AS similarity│  │
│  │   FROM fssai_regulations                            │  │
│  │   ORDER BY embedding <=> query_emb                  │  │
│  │   LIMIT 3                                           │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          │ 4. Return top match
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Result:                                                       │
│  {                                                             │
│    "found": true,                                             │
│    "regulation_text": "Schedule I Row 10: Sugar-free claims   │
│                        require ≤0.5g/100g",                   │
│    "claim_type": "sugar_claims",                              │
│    "threshold_value": 0.5,                                    │
│    "threshold_unit": "g/100g",                                │
│    "similarity_score": 0.92                                   │
│  }                                                             │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         │ 5. Use in audit decision
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  RegulatoryAuditorAgent                                        │
│  Decision: actual_value (0.3g) ≤ threshold (0.5g) → COMPLIANT│
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Architecture

### AlloyDB Schema

```sql
-- ═══════════════════════════════════════════════════════════════
-- Table 1: fssai_regulations (Vector Search)
-- ═══════════════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE fssai_regulations (
    id               SERIAL PRIMARY KEY,
    regulation_text  TEXT NOT NULL,           -- Chunk from FSSAI Gazette
    claim_type       VARCHAR(100),            -- sugar_claims, sodium_claims, etc.
    threshold_value  FLOAT,                   -- Numeric limit (e.g., 0.5)
    threshold_unit   VARCHAR(50),             -- Unit (e.g., "g/100g")
    embedding        vector(768)              -- 768-dim embedding
);

-- Index for vector similarity search (cosine distance)
CREATE INDEX fssai_regulations_embedding_idx
ON fssai_regulations
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Sample Data:
-- | id | regulation_text                          | claim_type    | threshold_value | embedding      |
-- |----|------------------------------------------|---------------|-----------------|----------------|
-- | 1  | "Sugar-free: ≤0.5g/100g (Schedule I #10)"| sugar_claims  | 0.5             | [0.012, -0.34..]|
-- | 2  | "Low sodium: ≤120mg/100g (Schedule I #13)"| sodium_claims | 120             | [0.089, 0.12..] |


-- ═══════════════════════════════════════════════════════════════
-- Table 2: ingredient_health_map (Ingredient Risk DB)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE ingredient_health_map (
    id                  SERIAL PRIMARY KEY,
    ingredient_name     VARCHAR(255) UNIQUE NOT NULL,  -- E.g., "Palm Oil", "Maida"
    health_concern      TEXT NOT NULL,                 -- Long-term health impact
    natural_alternative TEXT,                          -- Indian kitchen swap
    risk_level          VARCHAR(20) CHECK (risk_level IN ('Low', 'Medium', 'High'))
);

-- Sample Data:
-- | id | ingredient_name | health_concern                          | natural_alternative           | risk_level |
-- |----|-----------------|----------------------------------------|-------------------------------|------------|
-- | 1  | Refined Sugar   | Insulin spike, inflammation, obesity   | Jaggery, dates paste, stevia  | High       |
-- | 2  | Palm Oil        | High sat fat, LDL increase, deforestation| Coconut oil, mustard oil    | Medium     |
-- | 3  | INS 211         | Hyperactivity in children, carcinogen  | Citric acid, vinegar          | High       |


-- ═══════════════════════════════════════════════════════════════
-- Table 3: fssai_additives (INS Codes & ADI Limits)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE fssai_additives (
    id                  SERIAL PRIMARY KEY,
    ins_code            VARCHAR(20) UNIQUE NOT NULL,   -- E.g., "INS 211", "INS 102"
    common_name         VARCHAR(255),                  -- E.g., "Sodium Benzoate"
    permitted_foods     TEXT,                          -- Where it can be used
    prohibited_foods    TEXT,                          -- Where it CANNOT be used
    health_concern      TEXT,                          -- Known risks
    adi_mg_per_kg       INT                            -- Acceptable Daily Intake (WHO)
);

-- Sample Data:
-- | ins_code | common_name       | permitted_foods              | prohibited_foods | health_concern                      | adi_mg_per_kg |
-- |----------|-------------------|------------------------------|------------------|-------------------------------------|---------------|
-- | INS 211  | Sodium Benzoate   | carbonated drinks, jams      | infant food      | Hyperactivity, possible carcinogen  | 250           |
-- | INS 102  | Tartrazine        | confectionery, beverages     | infant food      | Allergic reactions, banned in EU    | 100           |


-- ═══════════════════════════════════════════════════════════════
-- Table 4: fssai_fruit_content_rules (Fruit % Requirements)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE fssai_fruit_content_rules (
    id                  SERIAL PRIMARY KEY,
    product_category    VARCHAR(100) UNIQUE NOT NULL,  -- E.g., "jam", "fruit juice"
    minimum_fruit_pct   INT NOT NULL CHECK (minimum_fruit_pct BETWEEN 0 AND 100),
    regulation_ref      TEXT,                          -- FSSAI citation
    verification_method VARCHAR(50)                    -- "ingredient_position" or "nutrient_label"
);

-- Sample Data:
-- | id | product_category | minimum_fruit_pct | regulation_ref                    | verification_method    |
-- |----|------------------|-------------------|-----------------------------------|------------------------|
-- | 1  | jam              | 45                | FSS Regulation 2.4.7              | ingredient_position    |
-- | 2  | fruit juice      | 85                | FSS Regulation 2.3.2              | nutrient_label         |
-- | 3  | fruit drink      | 10                | FSS Regulation 2.3.4              | ingredient_position    |
```

### Database Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                       Database Tables                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  fssai_regulations (RAG Vector DB)                       │  │
│  │  - Used by: RegulatoryAuditorAgent                       │  │
│  │  - Query type: Vector similarity search                  │  │
│  │  - Purpose: Find relevant FSSAI rules for claims         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ingredient_health_map                                   │  │
│  │  - Used by: EducationAgent                               │  │
│  │  - Query type: LIKE '%ingredient%' (partial match)       │  │
│  │  - Purpose: Flag harmful ingredients, suggest swaps      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  fssai_additives                                         │  │
│  │  - Used by: EducationAgent (future enhancement)          │  │
│  │  - Query type: Exact match on ins_code                   │  │
│  │  - Purpose: Detailed INS code information & ADI limits   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  fssai_fruit_content_rules                               │  │
│  │  - Used by: EducationAgent (deception detection)         │  │
│  │  - Query type: Exact match on product_category           │  │
│  │  - Purpose: Verify "Real Fruit" claims                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

       ▲                  ▲                  ▲
       │                  │                  │
       │ Vector Search    │ Keyword Search   │ Exact Match
       │                  │                  │
┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
│ Regulatory  │   │  Education  │   │  Education  │
│  Auditor    │   │    Agent    │   │    Agent    │
│   Agent     │   │             │   │  (Deception)│
└─────────────┘   └─────────────┘   └─────────────┘
```

---

## 5. Agent Pipeline Architecture

### Sequential Execution Model

```
┌────────────────────────────────────────────────────────────────────┐
│              Google ADK SequentialAgent Pipeline                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Configuration (app.py):                                           │
│                                                                    │
│  NutriGuardOrchestrator = SequentialAgent(                         │
│      name="NutriGuardOrchestrator",                                │
│      description="FSSAI audit: Extract → Audit → Sanity → Advise", │
│      sub_agents=[                                                  │
│          LabelExtractorAgent,                                      │
│          RegulatoryAuditorAgent,                                   │
│          SanityAgent,                                              │
│          UserAdvisorAgent,                                         │
│          WellnessAdvisorAgent,                                     │
│          EducationAgent,                                           │
│      ]                                                             │
│  )                                                                 │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                          Execution Flow                            │
│                                                                    │
│  Input: Content(role="user", parts=[Part(text="Audit: img.jpg")]) │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Phase 1: Data Extraction                                     │ │
│  │                                                              │ │
│  │  LabelExtractorAgent                                         │ │
│  │   Input:  image_path                                         │ │
│  │   Process:                                                   │ │
│  │     1. Reads image bytes                                     │ │
│  │     2. Calls Gemini Vision API                               │ │
│  │     3. Enforces JSON schema (mandatory_warnings added)       │ │
│  │   Output: ExtractedLabel JSON                                │ │
│  │     {                                                        │ │
│  │       "product_name": "Coca-Cola",                           │ │
│  │       "brand": "The Coca-Cola Company",                      │ │
│  │       "nutrients": {...},                                    │ │
│  │       "ingredients": [...],                                  │ │
│  │       "health_claims": [...],                                │ │
│  │       "mandatory_warnings": ["Contains Caffeine"]            │ │
│  │     }                                                        │ │
│  │                                                              │ │
│  │  Memory: Stored in session context                           │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────▼───────────────────────────────────────┐ │
│  │ Phase 2: Regulatory Compliance                               │ │
│  │                                                              │ │
│  │  RegulatoryAuditorAgent                                      │ │
│  │   Input:  ExtractedLabel (from Phase 1 memory)               │ │
│  │   Process:                                                   │ │
│  │     1. Parse health_claims array                             │ │
│  │     2. For each claim:                                       │ │
│  │        a. Map to nutrient group (via CLAIM_SYNONYMS)         │ │
│  │        b. Check actual value vs HARD_LIMITS                  │ │
│  │        c. If violated → force non_compliant                  │ │
│  │        d. Else → query_fssai_regulations() RAG               │ │
│  │     3. Profile-specific hard stops:                          │ │
│  │        - Child/Pregnant + Caffeine → VIOLATION               │ │
│  │        - Diabetic + Sugar >5g → HIGH CONCERN                 │ │
│  │   Output: ComplianceReport                                   │ │
│  │     {                                                        │ │
│  │       "flags": [...],                                        │ │
│  │       "overall_status": "needs_review",                      │ │
│  │       "risk_score": 45,                                      │ │
│  │       "high_severity_count": 0                               │ │
│  │     }                                                        │ │
│  │                                                              │ │
│  │  Memory: Appended to session context                         │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────▼───────────────────────────────────────┐ │
│  │ Phase 3: Cross-Validation                                    │ │
│  │                                                              │ │
│  │  SanityAgent                                                 │ │
│  │   Input:  ComplianceReport (from Phase 2)                    │ │
│  │   Process:                                                   │ │
│  │     1. If high_severity_count > 0 BUT overall_status ≠      │ │
│  │        "non_compliant" → FORCE override                      │ │
│  │     2. Ensure risk_score ≥ 80 when high flags exist          │ │
│  │   Output: Validated ComplianceReport (with sanity_override)  │ │
│  │                                                              │ │
│  │  Memory: Updated in session context                          │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────▼───────────────────────────────────────┐ │
│  │ Phase 4: Health & Wellness                                   │ │
│  │                                                              │ │
│  │  WellnessAdvisorAgent                                        │ │
│  │   Input:  ExtractedLabel + ComplianceReport + user_profile   │ │
│  │   Process:                                                   │ │
│  │     1. Profile-specific nutrient weighting:                  │ │
│  │        - Diabetic: sugar * 2                                 │ │
│  │        - Child: flag artificial colors                       │ │
│  │     2. compute_nutri_score(nutrients, fruit_pct)             │ │
│  │        → Negative points (energy, sugar, fat, sodium)        │ │
│  │        → Positive points (protein, fiber, fruit)             │ │
│  │        → Final score → Grade (A-E)                           │ │
│  │     3. _get_verdict(grade, nutrients, high_flags)            │ │
│  │        → Regular / Occasional / Rare                         │ │
│  │     4. _daily_comparisons(nutrients)                         │ │
│  │        → "10.6g sugar = 21% of WHO daily limit"              │ │
│  │   Output: WellnessReport                                     │ │
│  │     {                                                        │ │
│  │       "nutri_score": "D",                                    │ │
│  │       "consumption_verdict": "Occasional",                   │ │
│  │       "body_impact": {                                       │ │
│  │         "benefits": [...],                                   │ │
│  │         "concerns": [...]                                    │ │
│  │       },                                                     │ │
│  │       "daily_comparison": [...]                              │ │
│  │     }                                                        │ │
│  │                                                              │ │
│  │  Memory: Appended to session context                         │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────▼───────────────────────────────────────┐ │
│  │ Phase 5: Ingredient Education                                │ │
│  │                                                              │ │
│  │  EducationAgent                                              │ │
│  │   Input:  ExtractedLabel                                     │ │
│  │   Process:                                                   │ │
│  │     1. _query_ingredient_map(ingredients)                    │ │
│  │        → AlloyDB LIKE query for each ingredient              │ │
│  │        → Returns risk_level + alternatives                   │ │
│  │     2. _check_deception(claims, ingredients, nutrients)      │ │
│  │        → Pattern matching:                                   │ │
│  │          • "Real Fruit" but fruit at position 3+ → Flag      │ │
│  │          • "Sugar Free" but contains dextrose → Flag         │ │
│  │          • "High Protein" but protein < 10g → Flag           │ │
│  │   Output: EducationReport                                    │ │
│  │     {                                                        │ │
│  │       "flagged_ingredients": [                               │ │
│  │         {                                                    │ │
│  │           "ingredient": "Palm Oil",                          │ │
│  │           "risk_level": "Medium",                            │ │
│  │           "concern": "High sat fat, LDL increase",           │ │
│  │           "alternative": "Coconut oil, mustard oil"          │ │
│  │         }                                                    │ │
│  │       ],                                                     │ │
│  │       "deception_flags": [...]                               │ │
│  │     }                                                        │ │
│  │                                                              │ │
│  │  Memory: Appended to session context                         │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│                         ▼                                         │
│                  Final Response                                   │
│                  All agent outputs aggregated                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Technology Stack Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Streamlit 1.55.0            Custom CSS (Dark Theme)               │
│  - File upload widgets       - Gradient badges                     │
│  - Tabbed navigation         - Progress bars                       │
│  - Interactive charts        - Mobile-responsive                   │
│                                                                    │
│  PIL (Pillow) 12.1.1                                               │
│  - Image stitching (multi-upload)                                  │
│  - Format conversion (PNG/JPG)                                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Python 3.10+                asyncio / nest_asyncio                │
│  - Type hints               - Concurrent agent execution            │
│  - Dataclasses              - Event loop management                 │
│                                                                    │
│  Pydantic 2.12.5                                                   │
│  - Schema validation (NutrientData, ExtractedLabel, etc.)          │
│  - Field validators (cap_fat, cap_sodium)                          │
│  - Enum types (ConsumptionVerdict, ComplianceStatus)               │
│                                                                    │
│  Google ADK 1.27.4                                                 │
│  - LlmAgent class                                                  │
│  - FunctionTool decorator                                          │
│  - SequentialAgent orchestrator                                    │
│  - InMemoryRunner session management                               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                        AI & ML LAYER                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Gemini API (google-genai 1.68.0)                                 │
│  ┌────────────────────────┐    ┌──────────────────────────────┐  │
│  │ Gemini 2.0 Flash       │    │ Gemini 2.5 Flash             │  │
│  │ - Vision extraction    │    │ - Agent reasoning            │  │
│  │ - JSON mode            │    │ - Complex instructions       │  │
│  │ - Low latency          │    │ - Higher accuracy            │  │
│  └────────────────────────┘    └──────────────────────────────┘  │
│                                                                    │
│  Vertex AI (vertexai 1.43.0)                                      │
│  - TextEmbeddingModel.from_pretrained("text-embedding-004")       │
│  - 768-dimensional embeddings                                      │
│  - Task types: RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  AlloyDB for PostgreSQL (Google Cloud)                            │
│  - High-performance managed PostgreSQL                             │
│  - Public IP connection (direct TCP)                               │
│  - Connection pooling (pool_pre_ping, pool_recycle=1800)          │
│                                                                    │
│  pgvector Extension 0.3.6                                          │
│  - Vector data type: vector(768)                                   │
│  - Operators: <=> (cosine distance), <-> (L2), <#> (inner product)│
│  - Index: IVFFLAT (Inverted File with Flat compression)            │
│                                                                    │
│  SQLAlchemy 2.0.48                                                 │
│  - ORM & query builder                                             │
│  - Connection engine management                                    │
│  - Text queries with parameter binding                             │
│                                                                    │
│  pg8000 1.31.5 (Pure Python PostgreSQL driver)                    │
│  - No libpq dependency                                             │
│  - Native Python sockets                                           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT PROCESSING                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PyPDF2 3.0.1                                                      │
│  - PDF parsing (FSSAI Gazette)                                     │
│  - Page-by-page text extraction                                    │
│  - Metadata reading                                                │
│                                                                    │
│  LangChain (langchain-core 1.2.22)                                 │
│  - Text splitters                                                  │
│  - Document loaders                                                │
│  - Chunking strategies (80-word chunks)                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      UTILITIES & HELPERS                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  python-dotenv 1.2.2        requests 2.33.0                        │
│  - .env file loading        - HTTP API calls                       │
│  - Environment vars         - Gemini embedding API                 │
│                                                                    │
│  httpx 0.28.1               aiofiles 25.1.0                        │
│  - Async HTTP client        - Async file I/O                       │
│  - SSE streaming                                                   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 7. Deployment Architecture

### Cloud Deployment (Recommended)

```
┌────────────────────────────────────────────────────────────────────┐
│                          Google Cloud Platform                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                      Cloud Run                               │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │  NutriGuard Container                                  │  │ │
│  │  │  - streamlit run streamlit_app.py                     │  │ │
│  │  │  - Auto-scaling (0-10 instances)                      │  │ │
│  │  │  - HTTPS endpoint                                     │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  └────────────────────────┬─────────────────────────────────────┘ │
│                           │                                        │
│                           │ HTTPS (IAM Auth)                       │
│                           │                                        │
│  ┌────────────────────────▼─────────────────────────────────────┐ │
│  │               Gemini API (Vertex AI)                         │ │
│  │  - Vision extraction (gemini-2.0-flash)                      │ │
│  │  - Agent LLM (gemini-2.5-flash)                              │ │
│  │  - Embeddings (text-embedding-004)                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │               AlloyDB (PostgreSQL)                           │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │ Cluster: nutriguard-cluster (us-central1)             │ │ │
│  │  │ Instance: nutriguard-primary                          │ │ │
│  │  │ - 4 vCPU, 16GB RAM                                    │ │ │
│  │  │ - 100GB SSD                                           │ │ │
│  │  │ - Public IP: 35.x.x.x (restricted to Cloud Run IPs)  │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 Secret Manager                               │ │
│  │  - GOOGLE_API_KEY                                            │ │
│  │  - DB_PASS                                                   │ │
│  │  - ALLOYDB_INSTANCE_URI                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │            Cloud Storage (Optional)                          │ │
│  │  - Uploaded images (gs://nutriguard-uploads/)                │ │
│  │  - FSSAI Gazette PDF cache                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

         ▲                             ▲
         │                             │
         │ HTTPS Requests              │ Database Queries
         │                             │
┌────────┴─────────┐         ┌────────┴───────────┐
│   End Users      │         │  AlloyDB Private   │
│   (Web Browser)  │         │  Service Connect   │
└──────────────────┘         └────────────────────┘
```

### Network Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        VPC Network (Optional)                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Subnet: nutriguard-subnet (us-central1)                    │  │
│  │ IP Range: 10.0.0.0/24                                      │  │
│  │                                                            │  │
│  │  ┌──────────────────────┐    ┌──────────────────────────┐ │  │
│  │  │  Cloud Run Service   │    │  AlloyDB Cluster         │ │  │
│  │  │  10.0.0.10           │────│  10.0.0.20 (Private IP)  │ │  │
│  │  └──────────────────────┘    └──────────────────────────┘ │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Firewall Rules                                             │  │
│  │  - Allow TCP:5432 from Cloud Run Service Account          │  │
│  │  - Deny all other ingress to AlloyDB                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Cloud NAT (for external API calls from Cloud Run)          │  │
│  │  - Gemini API: https://generativelanguage.googleapis.com   │  │
│  │  - Vertex AI: https://aiplatform.googleapis.com            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      Security Layers                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Authentication & Authorization                                 │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │ Cloud Run IAM                                            │  │
│     │  - Require authentication for web UI (optional)          │  │
│     │  - Service account for Gemini/Vertex AI access          │  │
│     └──────────────────────────────────────────────────────────┘  │
│                                                                    │
│  2. Secrets Management                                             │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │ Secret Manager                                           │  │
│     │  - GOOGLE_API_KEY (versioned)                            │  │
│     │  - DB credentials (auto-rotation enabled)                │  │
│     │  - Access: Cloud Run service account only                │  │
│     └──────────────────────────────────────────────────────────┘  │
│                                                                    │
│  3. Network Security                                               │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │ AlloyDB                                                  │  │
│     │  - Private IP within VPC (recommended)                   │  │
│     │  - OR Public IP with authorized networks only            │  │
│     │  - SSL/TLS enforced for all connections                  │  │
│     └──────────────────────────────────────────────────────────┘  │
│                                                                    │
│  4. Data Encryption                                                │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │ - At rest: AlloyDB encryption (CMEK optional)            │  │
│     │ - In transit: TLS 1.3 for all API calls                  │  │
│     │ - Uploaded images: Temporary, deleted after processing   │  │
│     └──────────────────────────────────────────────────────────┘  │
│                                                                    │
│  5. Input Validation                                               │
│     ┌──────────────────────────────────────────────────────────┐  │
│     │ - File type whitelist: JPG, PNG only                     │  │
│     │ - Max file size: 10MB per image                          │  │
│     │ - Pydantic schema validation for all agent outputs       │  │
│     │ - SQL injection prevention: Parameterized queries        │  │
│     └──────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2026-04-03
**Architecture Version:** 2.0
**Maintainer:** Danish
**Status:** Production-Ready
