import streamlit as st
import tempfile, os, asyncio, json, uuid
from dotenv import load_dotenv
load_dotenv()

# ── Force ADC credentials before ADK initializes ─────────────────────────────
import google.auth
import google.auth.transport.requests

def _refresh_adc():
    """Pre-warm ADC credentials so async genai client doesn't hit metadata server."""
    try:
        creds, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(google.auth.transport.requests.Request())
        os.environ["GOOGLE_CLOUD_PROJECT"] = project or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        return True, creds.token[:20]
    except Exception as e:
        return False, str(e)

adc_ok, adc_info = _refresh_adc()

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from app import NutriGuardOrchestrator, APP_NAME, USER_ID
# ── rest of imports continue below ───────────────────────────────────────────

st.set_page_config(page_title="NutriGuard", page_icon="🛡️", layout="centered")

st.markdown("# 🛡️ NutriGuard")
st.markdown("**FSSAI Compliance Auditor** for Indian Packaged Foods")
st.divider()

uploaded = st.file_uploader(
    "Upload a food label photo",
    type=["jpg", "jpeg", "png"],
)

def run_agents(image_path: str) -> dict:
    """Run all agents and return {agent_name: text_output}."""
    # Refresh credentials before each run
    ok, info = _refresh_adc()
    if not ok:
        raise RuntimeError(f"ADC credential refresh failed: {info}\nRun: gcloud auth application-default login")

    session_id = f"st-{uuid.uuid4().hex[:8]}"
    runner = InMemoryRunner(agent=NutriGuardOrchestrator, app_name=APP_NAME)

    asyncio.run(runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id,
    ))

    message = Content(
        role="user",
        parts=[Part(text=f"Audit this food label image: {image_path}")]
    )

    outputs = {}
    current_author = None
    errors = []

    for event in runner.run(user_id=USER_ID, session_id=session_id, new_message=message):
        if hasattr(event, 'author') and event.author:
            current_author = event.author
        if hasattr(event, 'content') and event.content and current_author:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    outputs[current_author] = outputs.get(current_author, "") + part.text
        # Capture error events
        if hasattr(event, 'error_message') and event.error_message:
            errors.append(f"[{current_author}] {event.error_message}")

    if errors and not outputs:
        raise RuntimeError("All agents failed:\n" + "\n".join(errors))

    return outputs

def parse_json_from_text(text: str) -> dict | None:
    """Extract JSON object from agent text output."""
    try:
        start = text.find('{')
        end   = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return None

if uploaded:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(uploaded, width=300)
    with col2:
        st.markdown(f"**{uploaded.name}**")
        st.markdown(f"`{uploaded.size / 1024:.1f} KB`")
        audit_btn = st.button("🔍 Audit Label", type="primary", use_container_width=True)

    if audit_btn:
        suffix = os.path.splitext(uploaded.name)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(uploaded.getvalue())
            tmp_path = f.name

        with st.spinner("Running FSSAI compliance audit..."):
            try:
                outputs = run_agents(tmp_path)
                error = None
            except Exception as e:
                error = str(e)
            finally:
                os.unlink(tmp_path)

        if error:
            st.error(f"Audit failed: {error}")
            st.code(error)
        else:
            # ── Parse structured data from agent outputs ───────────────────
            extractor_text = outputs.get("LabelExtractorAgent", "")
            auditor_text   = outputs.get("RegulatoryAuditorAgent", "")
            advisor_text   = outputs.get("UserAdvisorAgent", "")

            label_data   = parse_json_from_text(extractor_text)
            audit_data   = parse_json_from_text(auditor_text)

            # ── Traffic light banner ───────────────────────────────────────
            overall = (audit_data or {}).get("overall_status", "needs_review")
            risk    = (audit_data or {}).get("risk_score", 0)
            flags   = (audit_data or {}).get("flags", [])
            n_high  = (audit_data or {}).get("high_severity_count", 0)
            n_claims= (audit_data or {}).get("total_claims_checked", 0)
            product = (audit_data or {}).get("product_name", "Product")
            brand   = (audit_data or {}).get("brand", "")

            if overall == "non_compliant" or n_high > 0:
                st.error(f"🚨 NON-COMPLIANT — {n_high} misleading claim(s) found in {product}")
            elif overall == "needs_review":
                st.warning(f"⚠️ NEEDS REVIEW — {product} by {brand}")
            else:
                st.success(f"✅ COMPLIANT — {product} by {brand} passes FSSAI checks")

            # ── Real metrics ───────────────────────────────────────────────
            c1, c2, c3 = st.columns(3)
            c1.metric("Risk Score", f"{risk}/100",
                      delta="High" if risk >= 35 else ("Medium" if risk >= 15 else "Low"),
                      delta_color="inverse")
            c2.metric("Claims Checked", n_claims)
            c3.metric("Flags Found", n_high,
                      delta=f"{n_high} critical" if n_high else "None",
                      delta_color="inverse" if n_high else "off")

            st.divider()

            # ── Tabs ───────────────────────────────────────────────────────
            tab1, tab2, tab3 = st.tabs(["📋 Extracted Label", "⚖️ Compliance Flags", "💬 Summary"])

            with tab1:
                if label_data:
                    nutrients = label_data.get("nutrients", {})
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**{label_data.get('product_name', '—')}**")
                        st.markdown(f"Brand: `{label_data.get('brand', '—')}`")
                        st.markdown(f"Net weight: `{label_data.get('net_weight', '—')}`")
                        st.markdown(f"FSSAI: `{label_data.get('fssai_license', 'Not found')}`")
                        st.markdown(f"Confidence: `{label_data.get('extraction_confidence', 0)*100:.0f}%`")
                    with col_b:
                        st.markdown("**Nutrients per 100g**")
                        nutrient_table = {
                            "Calories (kcal)":     nutrients.get("calories_kcal"),
                            "Protein (g)":         nutrients.get("protein_g"),
                            "Total Carbs (g)":     nutrients.get("total_carbs_g"),
                            "Total Sugars (g)":    nutrients.get("total_sugars_g"),
                            "Sodium (mg)":         nutrients.get("sodium_mg"),
                            "Saturated Fat (g)":   nutrients.get("saturated_fat_g"),
                            "Trans Fat (g)":       nutrients.get("trans_fat_g"),
                        }
                        for k, v in nutrient_table.items():
                            st.markdown(f"`{k}` — **{v if v is not None else 'N/A'}**")

                    if label_data.get("health_claims"):
                        st.markdown("**Health claims on pack:**")
                        for c in label_data["health_claims"]:
                            st.markdown(f"- {c}")
                    if label_data.get("ingredients"):
                        with st.expander("Ingredients list"):
                            st.write(", ".join(label_data["ingredients"]))
                else:
                    st.text(extractor_text)

            with tab2:
                if flags:
                    for flag in flags:
                        sev = flag.get("severity", "low")
                        status = flag.get("status", "")
                        icon = "🚨" if sev == "high" else ("⚠️" if sev == "medium" else "ℹ️")
                        color = "red" if status == "non_compliant" else "orange"
                        with st.expander(f"{icon} {flag.get('claim', '—')} — {status.replace('_', ' ').title()}"):
                            st.markdown(f"**Finding:** {flag.get('explanation', '—')}")
                            ref = flag.get("regulation_reference", "")
                            if ref:
                                st.caption(f"Regulation: {ref[:200]}")
                elif audit_data:
                    st.success("No compliance flags found.")
                else:
                    st.text(auditor_text)

            with tab3:
                st.write(advisor_text or "No summary generated.")

            st.divider()
            st.caption("⚕️ NutriGuard audits FSSAI regulatory compliance only. "
                       "For dietary advice, consult a registered dietitian.")

else:
    st.markdown("""
    ### How it works
    1. **Upload** any Indian packaged food label photo
    2. **Gemini Vision** extracts nutrients and health claims
    3. **FSSAI RAG** checks each claim against official regulations
    4. **Get a verdict** — compliant, flagged, or non-compliant
    """)
    st.info("Try it with Maggi, Kurkure, Haldiram's, or any protein powder.")

st.divider()

# Show ADC status in sidebar for debugging
with st.sidebar:
    st.markdown("### System Status")
    if adc_ok:
        st.success(f"ADC credentials active")
    else:
        st.error(f"ADC credentials missing — run `gcloud auth application-default login`")
        st.code("gcloud auth application-default login")
    st.markdown(f"Model: `{os.getenv('GOOGLE_GENAI_MODEL', 'gemini-2.5-flash')}`")
    st.markdown(f"Project: `{os.getenv('GOOGLE_CLOUD_PROJECT', 'not set')}`")
st.caption("Gen AI Academy APAC Edition · Google ADK 1.27.4 + Gemini 2.5 Flash + AlloyDB AI")
