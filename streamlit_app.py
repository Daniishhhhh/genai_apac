import streamlit as st
import tempfile, os, asyncio, json, uuid, ast
from dotenv import load_dotenv
import nest_asyncio
from PIL import Image

nest_asyncio.apply()
load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from app import NutriGuardOrchestrator, APP_NAME, USER_ID

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NutriGuard Pro — AI Food Safety Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS Styling ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="st-"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #060c1a; color: #e2e8f0; }

/* 🛠️ FIXED: Stop Streamlit from dimming/blurring the screen when agents are running */
[data-testid="stAppViewBlockContainer"] { filter: none !important; opacity: 1 !important; }

[data-testid="stSidebar"] { background: rgba(10,18,35,0.95); border-right: 1px solid rgba(56,189,248,0.15); }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h3 { color: #38bdf8 !important; font-size: 0.85rem; letter-spacing: 0.12em; text-transform: uppercase; }

.g-card { background: rgba(15,23,42,0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 28px 32px; backdrop-filter: blur(18px); margin-bottom: 20px; }
.g-card-accent { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.3); border-radius: 20px; padding: 28px 32px; backdrop-filter: blur(18px); margin-bottom: 20px; }
.hero-title { font-size: clamp(2.2rem,5vw,3.8rem); font-weight: 700; background: linear-gradient(135deg,#38bdf8 0%,#818cf8 50%,#f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.15; margin-bottom: 12px; }
.hero-sub { font-size: 1.05rem; color: #94a3b8; line-height: 1.7; max-width: 560px; }

.ns-badge { font-family: 'JetBrains Mono',monospace; font-size: 3.5rem; font-weight: 700; width: 96px; height: 96px; border-radius: 18px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.ns-A { background: linear-gradient(135deg,#059669,#10b981); color:#fff; }
.ns-B { background: linear-gradient(135deg,#65a30d,#84cc16); color:#fff; }
.ns-C { background: linear-gradient(135deg,#b45309,#f59e0b); color:#fff; }
.ns-D { background: linear-gradient(135deg,#c2410c,#f97316); color:#fff; }
.ns-E { background: linear-gradient(135deg,#991b1b,#ef4444); color:#fff; }

.verdict-regular { background:rgba(16,185,129,0.15); color:#10b981; border:1px solid #10b981; padding:6px 18px; border-radius:30px; font-size:0.85rem; font-weight:600; display:inline-block; }
.verdict-occasional { background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid #f59e0b; padding:6px 18px; border-radius:30px; font-size:0.85rem; font-weight:600; display:inline-block; }
.verdict-rare { background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid #ef4444; padding:6px 18px; border-radius:30px; font-size:0.85rem; font-weight:600; display:inline-block; }

.stat-row { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }
.stat-tile { flex:1; min-width:110px; background:rgba(30,41,59,0.6); border:1px solid rgba(255,255,255,0.07); border-radius:14px; padding:16px 14px 12px; text-align:center; }
.stat-val { font-family:'JetBrains Mono',monospace; font-size:1.4rem; font-weight:600; color:#f1f5f9; }
.stat-key { font-size:0.72rem; color:#64748b; margin-top:4px; text-transform:uppercase; letter-spacing:0.08em; }

.pbar-wrap { margin:8px 0; }
.pbar-label { display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; margin-bottom:5px; }
.pbar-bg { background:rgba(255,255,255,0.07); border-radius:6px; height:7px; }
.pbar-fill { height:7px; border-radius:6px; }
.pbar-green { background:linear-gradient(90deg,#059669,#10b981); }
.pbar-yellow { background:linear-gradient(90deg,#b45309,#f59e0b); }
.pbar-red { background:linear-gradient(90deg,#991b1b,#ef4444); }

.flag-row { display:flex; align-items:flex-start; gap:14px; padding:14px 16px; background:rgba(239,68,68,0.06); border-left:3px solid #ef4444; border-radius:0 12px 12px 0; margin-bottom:10px; }
.flag-name { font-weight:600; font-size:0.9rem; color:#f1f5f9; }
.flag-why { font-size:0.8rem; color:#94a3b8; margin-top:3px; line-height:1.5; }
.flag-swap { font-size:0.78rem; color:#34d399; margin-top:5px; }

.deception-row { padding:12px 16px; background:rgba(168,85,247,0.08); border-left:3px solid #a855f7; border-radius:0 12px 12px 0; margin-bottom:10px; }
.deception-claim { font-weight:600; font-size:0.88rem; color:#d8b4fe; }
.deception-issue { font-size:0.8rem; color:#94a3b8; margin-top:3px; }
.deception-reg { font-size:0.72rem; color:#6b7280; margin-top:4px; font-family:'JetBrains Mono',monospace; }

.section-label { font-size:0.7rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; color:#38bdf8; margin-bottom:14px; display:flex; align-items:center; gap:8px; }
.section-label::after { content:''; flex:1; height:1px; background:rgba(56,189,248,0.2); }

.comp-flag { padding:12px 16px; background:rgba(239,68,68,0.08); border-left:3px solid #ef4444; border-radius:0 10px 10px 0; margin-bottom:8px; }
.comp-ok   { padding:12px 16px; background:rgba(16,185,129,0.08); border-left:3px solid #10b981; border-radius:0 10px 10px 0; margin-bottom:8px; }

[data-testid="stFileUploadDropzone"] { background:rgba(15,23,42,0.6) !important; border:2px dashed rgba(56,189,248,0.35) !important; border-radius:16px !important; }

/* Main Top Navigation Tabs */
.stTabs [data-baseweb="tab-list"] { gap:6px; background:transparent; }
.stTabs [data-baseweb="tab"] { border-radius:10px; padding:12px 24px; background:rgba(30,41,59,0.5); color:#94a3b8; font-size:1rem; font-weight: 600;}
.stTabs [aria-selected="true"] { background:rgba(56,189,248,0.15) !important; color:#38bdf8 !important; border-bottom:3px solid #38bdf8; }

.stButton button { border-radius:12px; font-weight:600; font-family:'Space Grotesk',sans-serif; }
.stButton button[kind="primary"] { background:linear-gradient(135deg,#0ea5e9,#6366f1); border:none; color:#fff; }

@keyframes pulse-dot { 0%,100%{opacity:.4} 50%{opacity:1} }
.live-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#10b981; animation:pulse-dot 2s infinite; margin-right:6px; }

/* 🛠️ High-visibility glowing sidebar toggle button */
[data-testid="collapsedControl"] { 
    background: rgba(14, 165, 233, 0.2) !important; 
    border: 1px solid #38bdf8 !important;
    border-radius: 50% !important; 
    margin-top: 15px;
    margin-left: 15px;
    box-shadow: 0 0 15px rgba(56,189,248,0.4);
    transition: all 0.3s ease;
}
[data-testid="collapsedControl"]:hover { background: rgba(14, 165, 233, 0.4) !important; }
[data-testid="collapsedControl"] svg { fill: #38bdf8 !important; width: 24px; height: 24px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "scanned_profile" not in st.session_state:
    st.session_state.scanned_profile = "General"
if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

# ── Sidebar (Minimalist) ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ NutriGuard Pro")
    st.markdown('<div class="live-dot"></div><span style="font-size:0.75rem;color:#10b981;">All agents online</span>', unsafe_allow_html=True)
    st.divider()
    st.markdown("<div style='font-size:0.85rem; color:#94a3b8;'>Navigate using the tabs at the top of the screen to Scan Labels, read the About page, or explore the AI Architecture.</div>", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
async def run_audit_async(image_path: str, profile: str) -> dict:
    runner = InMemoryRunner(agent=NutriGuardOrchestrator, app_name=APP_NAME)
    sid = f"audit-{uuid.uuid4().hex[:8]}"
    await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sid)
    msg = Content(role="user", parts=[Part(text=f"Profile: {profile}. Audit this food label image: {image_path}")])
    results = {}
    async for event in runner.run_async(user_id=USER_ID, session_id=sid, new_message=msg):
        if hasattr(event, 'author') and event.author:
            if event.content and event.content.parts:
                txt = getattr(event.content.parts[0], 'text', '') or ''
                results[event.author] = results.get(event.author, "") + txt
    return results

def parse_json(text) -> dict:
    if not text: return {}
    if isinstance(text, dict): return text 
    try:
        clean = str(text).replace("```json","").replace("```","").strip()
        s, e = clean.find('{'), clean.rfind('}')
        if s >= 0 and e > s: 
            json_str = clean[s:e+1]
            try:
                return json.loads(json_str)
            except Exception:
                try:
                    json_str_fixed = json_str.replace("'", '"').replace("None", "null").replace("True", "true").replace("False", "false")
                    return json.loads(json_str_fixed)
                except Exception:
                    return ast.literal_eval(json_str)
    except Exception: 
        pass
    return {}

def pct_color(pct):
    if pct < 30: return "pbar-green"
    if pct < 65: return "pbar-yellow"
    return "pbar-red"

def render_pbar(label, value, unit, rda, rda_lbl):
    if value is None: return
    pct = min(round((value/rda)*100), 100)
    cls = pct_color(pct)
    col = "#10b981" if pct<30 else ("#f59e0b" if pct<65 else "#ef4444")
    st.markdown(f'<div class="pbar-wrap"><div class="pbar-label"><span>{label} — <strong style="color:{col}">{value}{unit}</strong></span><span style="color:{col};">{pct}% of daily {rda_lbl}</span></div><div class="pbar-bg"><div class="pbar-fill {cls}" style="width:{pct}%"></div></div></div>', unsafe_allow_html=True)

def verdict_pill(v):
    vl = v.lower()
    if "regular" in vl: return '<span class="verdict-regular">✅ Regular Consumption OK</span>'
    if "occasional" in vl: return '<span class="verdict-occasional">⚠️ Occasional / Moderate</span>'
    return '<span class="verdict-rare">🚨 Rare / Avoid</span>'


# ── Results Renderer ───────────────────────────────────────────────────────────
def render_results(raw: dict, profile: str):
    lbl       = parse_json(raw.get("LabelExtractorAgent",""))
    if "extract_label_from_image_response" in lbl: lbl = lbl["extract_label_from_image_response"]
    elif "extract_label_from_image" in lbl: lbl = lbl["extract_label_from_image"]

    audit     = parse_json(raw.get("SanityAgent","") or raw.get("RegulatoryAuditorAgent",""))
    well_raw  = raw.get("WellnessAdvisorAgent","")
    well      = parse_json(well_raw)
    edu_raw   = raw.get("EducationAgent","")
    edu       = parse_json(edu_raw)
    edu_inner = edu.get("analyse_ingredients_response", edu)

    nutrients = lbl.get("nutrients", {})
    score     = well.get("nutri_score","C").upper()
    verdict   = well.get("consumption_verdict","Occasional")
    reason    = well.get("verdict_reason","")
    product   = lbl.get("product_name") or well.get("product_name") or "Unknown Product"
    brand     = lbl.get("brand") or well.get("brand") or "Unknown Brand"
    warnings  = lbl.get("mandatory_warnings", [])
    
    flags     = audit.get("flags",[])
    high_ct   = audit.get("high_severity_count",0)
    overall   = audit.get("overall_status","needs_review")

    if overall=="non_compliant" or high_ct>0:
        st.error(f"🚨 **{product}** by {brand} — {high_ct} FSSAI violation(s) detected")
    elif overall=="needs_review":
        st.warning(f"⚠️ **{product}** by {brand} — some claims need verification")
    else:
        st.success(f"✅ **{product}** by {brand} — passes FSSAI compliance checks")

    if warnings:
        for w in warnings:
            st.markdown(f'<div style="padding:10px 14px; background:rgba(220, 38, 38, 0.15); border:1px solid #dc2626; border-radius:8px; color:#fca5a5; font-size:0.9rem; font-weight:600; margin-bottom:10px;">🛑 LABEL WARNING: {w}</div>', unsafe_allow_html=True)

    col_score, col_info = st.columns([1,2])
    with col_score:
        st.markdown(f'<div class="g-card" style="text-align:center;padding:32px 20px;"><div style="font-size:0.7rem;letter-spacing:.14em;text-transform:uppercase;color:#38bdf8;margin-bottom:16px;">Nutri-Score</div><div class="ns-badge ns-{score}" style="margin:0 auto 16px;">{score}</div><div style="font-size:0.8rem;color:#64748b;line-height:1.5;">A = Best &nbsp;·&nbsp; E = Worst<br>FSSAI + WHO Indian RDAs</div><div style="margin-top:16px;">{verdict_pill(verdict)}</div><div style="font-size:0.78rem;color:#64748b;margin-top:10px;">{reason}</div></div>', unsafe_allow_html=True)

    with col_info:
        st.markdown(f'<div class="g-card"><div class="section-label">Product info</div><div style="font-size:1.3rem;font-weight:700;color:#f1f5f9;">{product}</div><div style="font-size:0.9rem;color:#64748b;margin-bottom:16px;">by {brand} &nbsp;·&nbsp; {lbl.get("net_weight","—")} &nbsp;·&nbsp; Profile: <strong style="color:#38bdf8;">{profile}</strong></div><div style="font-size:0.75rem;color:#475569;margin-bottom:10px;">FSSAI: {lbl.get("fssai_license") or "Not found"} &nbsp;·&nbsp; Confidence: {round(lbl.get("extraction_confidence",0)*100)}%</div>', unsafe_allow_html=True)
        n = nutrients
        tile_html = '<div class="stat-row">'
        for key,unit,label in [("calories_kcal","kcal","Energy"),("total_sugars_g","g","Sugar"),("sodium_mg","mg","Sodium"),("saturated_fat_g","g","Sat.Fat"),("protein_g","g","Protein"),("total_carbs_g","g","Carbs")]:
            v = n.get(key); d = f"{v}{unit}" if v is not None else "—"
            tile_html += f'<div class="stat-tile"><div class="stat-val">{d}</div><div class="stat-key">{label}</div></div>'
        tile_html += '</div></div>'
        st.markdown(tile_html, unsafe_allow_html=True)

    t1,t2,t3,t4,t5 = st.tabs(["🩺 Health Impact","🧪 Ingredients","⚖️ FSSAI Compliance","📊 RDA Breakdown", "💡 Healthy Alternatives"])

    # 🛠️ FIXED: Bulletproof Health Impact Tab
    with t1:
        impact = well.get("body_impact", {})
        benefits, concerns = [], []
        
        if isinstance(impact, str):
            concerns = [impact] # AI hallucinated a string
        elif isinstance(impact, dict):
            benefits = impact.get("benefits", [])
            concerns = impact.get("concerns", [])
            
        if not benefits and not concerns: # Deep fallback
            benefits = well.get("benefits", [])
            concerns = well.get("concerns", [])
            
        if isinstance(benefits, str): benefits = [benefits]
        if isinstance(concerns, str): concerns = [concerns]
        
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="section-label">✅ Benefits</div>', unsafe_allow_html=True)
            if not benefits:
                st.markdown('<div style="padding:10px 14px;background:rgba(30,41,59,0.5);border-radius:10px;font-size:0.85rem;color:#94a3b8;">No specific health benefits identified for this profile.</div>', unsafe_allow_html=True)
            else:
                for b in benefits: st.markdown(f'<div style="padding:10px 14px;background:rgba(16,185,129,0.08);border-left:3px solid #10b981;border-radius:0 10px 10px 0;margin-bottom:8px;font-size:0.85rem;color:#d1fae5;line-height:1.6;">{b}</div>', unsafe_allow_html=True)
        
        with cb:
            st.markdown('<div class="section-label">⚠️ Concerns</div>', unsafe_allow_html=True)
            if not concerns:
                st.markdown('<div style="padding:10px 14px;background:rgba(30,41,59,0.5);border-radius:10px;font-size:0.85rem;color:#94a3b8;">No major health concerns identified.</div>', unsafe_allow_html=True)
            else:
                for c in concerns: st.markdown(f'<div style="padding:10px 14px;background:rgba(239,68,68,0.08);border-left:3px solid #ef4444;border-radius:0 10px 10px 0;margin-bottom:8px;font-size:0.85rem;color:#fecaca;line-height:1.6;">{c}</div>', unsafe_allow_html=True)

        daily = well.get("daily_comparison", [])
        if daily:
            st.markdown('<div class="section-label" style="margin-top:16px;">📏 Compared to your daily limits</div>', unsafe_allow_html=True)
            for line in daily: st.markdown(f'<div style="padding:8px 14px;background:rgba(30,41,59,0.6);border-radius:10px;margin-bottom:6px;font-size:0.83rem;color:#94a3b8;">📌 {line}</div>', unsafe_allow_html=True)
        
        ps = edu_inner.get("preservative_impact_summary","")
        if ps:
            st.markdown('<div class="section-label" style="margin-top:16px;">🧬 Long-term additive impact</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="padding:14px 18px;background:rgba(168,85,247,0.08);border:1px solid rgba(168,85,247,0.2);border-radius:14px;font-size:0.85rem;color:#e9d5ff;line-height:1.7;">{ps}</div>', unsafe_allow_html=True)
            
    with t2:
        flagged    = edu_inner.get("flagged_ingredients",[])
        deceptions = edu_inner.get("deception_flags",[])
        if deceptions:
            st.markdown('<div class="section-label">🎭 Deceptive Marketing Claims Detected</div>', unsafe_allow_html=True)
            for d in deceptions: st.markdown(f'<div class="deception-row"><div class="deception-claim">⚠️ "{d.get("claim","")}"</div><div class="deception-issue">{d.get("issue","")}</div><div class="deception-reg">Regulation: {d.get("regulation","")}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding:10px 14px;background:rgba(16,185,129,0.08);border-left:3px solid #10b981;border-radius:0 10px 10px 0;margin-bottom:12px;font-size:0.85rem;color:#d1fae5;">✅ No deceptive marketing claims detected</div>', unsafe_allow_html=True)
        if flagged:
            for group,label,css in [([ f for f in flagged if f.get("risk_level")=="High"],"🔴 High Risk",""),([ f for f in flagged if f.get("risk_level")=="Medium"],"🟡 Medium Risk","medium"),([ f for f in flagged if f.get("risk_level")=="Low"],"⚪ Low Risk","low")]:
                if not group: continue
                st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
                for item in group: st.markdown(f'<div class="flag-row {css}"><div style="flex:1;"><div class="flag-name">{item.get("ingredient","")} <span style="font-size:0.72rem;color:#64748b;">→ {item.get("matched_to","")}</span></div><div class="flag-why">{item.get("concern","")}</div><div class="flag-swap">✨ Safer swap: {item.get("alternative","")}</div></div></div>', unsafe_allow_html=True)
        ingredients = lbl.get("ingredients",[])
        if ingredients:
            st.markdown('<div class="section-label" style="margin-top:16px;">📜 Full ingredients (as printed, in order)</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.8rem;line-height:2;padding:12px 16px;background:rgba(30,41,59,0.4);border-radius:12px;">{" &nbsp;·&nbsp; ".join([f"<span style=color:#94a3b8;>{i}</span>" for i in ingredients])}</div>', unsafe_allow_html=True)

    with t3:
        claims = lbl.get("health_claims",[])
        if not claims: st.markdown('<div style="padding:14px 18px;background:rgba(30,41,59,0.5);border-radius:12px;color:#64748b;font-size:0.85rem;">No health claims found on this label.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section-label">Health claims found ({len(claims)})</div>', unsafe_allow_html=True)
            claims_html = "".join([f"<li style='margin-bottom:6px;'>{c}</li>" for c in claims])
            st.markdown(f"<div style='background:rgba(15,23,42,0.5); border:1px solid rgba(56,189,248,0.2); padding:16px 20px; border-radius:12px; margin-bottom:20px;'><ul style='margin:0; padding-left:20px; color:#e2e8f0; font-size:0.85rem;'>{claims_html}</ul></div>", unsafe_allow_html=True)
        if flags:
            st.markdown('<div class="section-label">FSSAI Audited Flags</div>', unsafe_allow_html=True)
            for flag in flags:
                is_bad = flag.get("status")=="non_compliant"
                css, icon = ("comp-flag", "🚨") if is_bad else ("comp-ok", "✅")
                ref = f'<div style="font-size:0.72rem;color:#475569;margin-top:4px;font-family:JetBrains Mono,monospace;">{flag.get("regulation_reference","")[:180]}</div>' if flag.get("regulation_reference") else ""
                st.markdown(f'<div class="{css}"><div style="font-weight:600;font-size:0.88rem;color:#f1f5f9;">{icon} "{flag.get("claim","")}"</div><div style="font-size:0.8rem;color:#94a3b8;margin-top:4px;">{flag.get("explanation","")}</div>{ref}</div>', unsafe_allow_html=True)
        violated = audit.get("violated_groups",[])
        if violated:
            st.markdown('<div class="section-label" style="margin-top:16px;">⚡ Nutrient threshold violations</div>', unsafe_allow_html=True)
            for g in violated: st.markdown(f'<span style="display:inline-block;background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);color:#fca5a5;border-radius:8px;padding:4px 14px;font-size:0.8rem;margin:4px 4px 4px 0;">{g.replace("_"," ").title()}</span>', unsafe_allow_html=True)
                
    with t4:
        RDAS = {
            "General":          {"sugar":50,"sodium":2000,"sat_fat":22,"calories":2000,"protein":60},
            "Diabetic":         {"sugar":25,"sodium":1500,"sat_fat":20,"calories":1800,"protein":60},
            "Child (under 12)": {"sugar":25,"sodium":1200,"sat_fat":15,"calories":1600,"protein":35},
            "Pregnant":         {"sugar":50,"sodium":2000,"sat_fat":22,"calories":2400,"protein":75},
            "Hypertension":     {"sugar":50,"sodium":1000,"sat_fat":15,"calories":2000,"protein":60},
        }
        rda = RDAS.get(profile, RDAS["General"])
        st.markdown(f'<div class="section-label">How 100g of this product fills your daily limits ({profile} profile)</div>', unsafe_allow_html=True)
        render_pbar("Sugar",        nutrients.get("total_sugars_g"), "g",   rda["sugar"],   "limit (WHO)")
        render_pbar("Sodium",       nutrients.get("sodium_mg"),      "mg",  rda["sodium"],  "limit (ICMR)")
        render_pbar("Saturated Fat",nutrients.get("saturated_fat_g"),"g",   rda["sat_fat"], "limit")
        render_pbar("Calories",     nutrients.get("calories_kcal"),  "kcal",rda["calories"],"intake")
        render_pbar("Protein",      nutrients.get("protein_g"),      "g",   rda["protein"], "need")
        st.markdown(f'<div style="margin-top:16px;padding:12px 16px;background:rgba(30,41,59,0.5);border-radius:12px;font-size:0.78rem;color:#475569;">RDA values for <strong style="color:#38bdf8;">{profile}</strong> profile. Switch in sidebar to update. Sources: ICMR Dietary Guidelines 2024, WHO Sugar Recommendation.</div>', unsafe_allow_html=True)
        ns_bd = well.get("nutri_score_breakdown",{})
        if ns_bd:
            st.markdown('<div class="section-label" style="margin-top:20px;">🔢 NutriScore point breakdown</div>', unsafe_allow_html=True)
            ca2,cb2 = st.columns(2)
            with ca2:
                st.markdown("**Negative points** (higher = worse)")
                for k in ["energy","sugars","sat_fat","sodium"]:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#94a3b8;padding:3px 0;"><span>{k.replace("_"," ").title()}</span><span style="color:#ef4444;font-weight:600;">+{ns_bd.get(k,0)}</span></div>', unsafe_allow_html=True)
            with cb2:
                st.markdown("**Positive points** (higher = better)")
                for k in ["protein","fibre","fruit"]:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#94a3b8;padding:3px 0;"><span>{k.title()}</span><span style="color:#10b981;font-weight:600;">-{ns_bd.get(k,0)}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="margin-top:12px;font-size:0.9rem;color:#f1f5f9;">Final score: <strong style="color:#38bdf8;">{well.get("nutri_score_points","—")}</strong> → Grade <strong style="font-size:1.1rem;">{score}</strong></div>', unsafe_allow_html=True)

    with t5:
        st.markdown('<div class="section-label">✨ Smart Swaps & Better Choices</div>', unsafe_allow_html=True)
        flagged = edu_inner.get("flagged_ingredients", [])
        has_alts = False
        for item in flagged:
            alt = item.get("alternative", "")
            if alt and alt.strip() != "":
                has_alts = True
                st.markdown(f'''<div style="padding:16px 20px; background:rgba(16,185,129,0.08); border-left:4px solid #10b981; border-radius:0 12px 12px 0; margin-bottom:14px;">
                    <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:4px; text-transform: uppercase; letter-spacing: 0.05em;">Instead of <span style="color:#fecaca; font-weight:600;">{item.get("ingredient", "this")}</span></div>
                    <div style="font-size:1.2rem; color:#10b981; font-weight:700; margin-bottom:8px;">Try 👉 {alt}</div>
                    <div style="font-size:0.85rem; color:#cbd5e1; line-height:1.5;"><strong>Why?</strong> {item.get("concern", "")}</div>
                </div>''', unsafe_allow_html=True)
        if not has_alts: st.markdown('<div style="padding:14px 18px;background:rgba(30,41,59,0.5);border-radius:12px;color:#64748b;font-size:0.85rem;">✅ No major red-flag ingredients found to swap! This product is relatively clean based on your current health profile.</div>', unsafe_allow_html=True)


# ── Main Application Layout ────────────────────────────────────────────────────
tab_home, tab_about, tab_arch = st.tabs(["🏠 Home — Scan Label", "ℹ️ About NutriGuard", "🤖 AI Architecture"])

with tab_home:
    st.markdown('<div style="margin-top:10px; margin-bottom: 20px;"><p class="hero-title">NutriGuard Pro</p><p class="hero-sub">AI-Powered Food Safety & FSSAI Compliance Auditor</p></div>', unsafe_allow_html=True)
    
    col_profile, col_upload = st.columns([1, 2])
    with col_profile:
        st.markdown('<div class="g-card" style="padding: 20px;">', unsafe_allow_html=True)
        st.markdown("### 1. Select Health Profile")
        health_profile = st.selectbox("Who is eating this?", ["General", "Diabetic", "Child (under 12)", "Pregnant", "Hypertension"], help="Re-weights risk thresholds based on your health context.", label_visibility="collapsed")
        st.caption(f"Currently auditing for: **{health_profile}**")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_upload:
        st.markdown('<div class="g-card-accent" style="padding: 20px;">', unsafe_allow_html=True)
        st.markdown("### 2. Upload Label Photo(s)")
        uploaded_files = st.file_uploader("Upload Front & Back", type=["jpg","jpeg","png"], accept_multiple_files=True, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_files:
        img_col, ctrl_col = st.columns([1,1.6])
        with img_col:
            st.markdown('<div class="g-card" style="padding:16px;">', unsafe_allow_html=True)
            for uf in uploaded_files:
                st.image(uf, width='stretch')
                st.markdown(f'<div style="font-size:0.75rem;color:#475569;text-align:center;margin-top:4px;margin-bottom:12px;">{uf.name}</div>', unsafe_allow_html=True)
            if st.button("↩ Scan different product(s)", use_container_width=True):
                st.session_state.audit_data = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with ctrl_col:
            if st.session_state.audit_data is None:
                st.markdown('<div class="g-card-accent"><div style="font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:8px;">Ready to audit</div><div style="font-size:0.85rem;color:#64748b;line-height:1.6;margin-bottom:20px;">5 specialised AI agents will analyse this label — NutriScore, FSSAI compliance, ingredient risks, deceptive claims, and personalised health verdict.</div></div>', unsafe_allow_html=True)
                if st.button("🚀 Run Multi-Agent Audit", type="primary", use_container_width=True):
                    with st.status("🧠 Agent squad running...", expanded=True) as s:
                        st.write("👁️ LabelExtractorAgent — preparing images...")
                        images = [Image.open(uf) for uf in uploaded_files]
                        widths, heights = zip(*(i.size for i in images))
                        combined_img = Image.new('RGB', (max(widths), sum(heights)))
                        y_offset = 0
                        for img in images:
                            combined_img.paste(img, (0, y_offset))
                            y_offset += img.size[1]
                        
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                            combined_img.save(tmp.name, format="JPEG")
                            tmp_path = tmp.name
                        
                        try:
                            loop = asyncio.new_event_loop()
                            try:
                                st.write("👁️ LabelExtractorAgent — reading combined label data...")
                                raw = loop.run_until_complete(run_audit_async(tmp_path, health_profile))
                            finally:
                                pending = asyncio.all_tasks(loop)
                                if pending: loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                                loop.close()
                            st.write("⚖️ RegulatoryAuditorAgent — checking FSSAI claims...")
                            st.write("🛡️ SanityAgent — verifying compliance logic...")
                            st.write("🩺 WellnessAdvisorAgent — computing NutriScore...")
                            st.write("🧪 EducationAgent — scanning ingredient database...")
                            s.update(label="✅ Audit complete!", state="complete")
                            st.session_state.audit_data = raw
                            st.session_state.scanned_profile = health_profile
                        except Exception as e:
                            s.update(label="❌ Audit failed", state="error")
                            st.error(f"Error: {e}")
                        finally:
                            os.unlink(tmp_path)
                    if st.session_state.audit_data: st.rerun()
            else:
                st.markdown('<div style="padding:10px 16px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:12px;font-size:0.85rem;color:#34d399;margin-bottom:12px;"><span class="live-dot"></span> Audit complete — full report below</div>', unsafe_allow_html=True)

        if st.session_state.audit_data:
            st.divider()
            render_results(st.session_state.audit_data, st.session_state.scanned_profile)

with tab_about:
    st.markdown("""
    <div style="margin-top:20px; margin-bottom: 20px;">
        <h2 style="color:#f1f5f9;">ℹ️ About NutriGuard Pro</h2>
        <p style="color:#94a3b8; font-size: 1.1rem;">Your Food Label Has Secrets. We Expose Them.</p>
    </div>
    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
        <div style="flex: 1; background: rgba(15,23,42,0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <div style="font-size: 2rem; margin-bottom: 10px;">🔍</div>
            <h4 style="color: #38bdf8;">Step 1: Upload</h4>
            <p style="color: #94a3b8; font-size: 0.9rem;">Photograph any Indian packaged food — Maggi, Kurkure, protein powder. Our Vision Agent reads every pixel.</p>
        </div>
        <div style="flex: 1; background: rgba(15,23,42,0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <div style="font-size: 2rem; margin-bottom: 10px;">🤖</div>
            <h4 style="color: #38bdf8;">Step 2: Analyse</h4>
            <p style="color: #94a3b8; font-size: 0.9rem;">5 specialist agents check FSSAI compliance, compute NutriScore, map risks, and detect deceptive marketing.</p>
        </div>
        <div style="flex: 1; background: rgba(15,23,42,0.6); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <div style="font-size: 2rem; margin-bottom: 10px;">📋</div>
            <h4 style="color: #38bdf8;">Step 3: Report</h4>
            <p style="color: #94a3b8; font-size: 0.9rem;">A plain-English verdict — should you eat this? Personalised for your age, medical condition, and lifestyle.</p>
        </div>
    </div>
    
    <h3 style="color:#f1f5f9; margin-top: 30px; margin-bottom: 20px;">Why This Matters</h3>
    
    **🏷️ Label Fraud is Real**
    "Made with Real Fruit" can legally mean fruit is 4th in the ingredient list — after sugar and artificial flavours. FSSAI Regulation 7 covers this, but no one checks at the shop.
    
    **🧪 Hidden Additives**
    INS 211, INS 102, Hydrogenated Oil appear in hundreds of Indian snacks. Most consumers don't know what they mean or what they do to your body over time.
    
    **👶 Children Are Vulnerable**
    Tartrazine and Sunset Yellow are linked to hyperactivity in children. NutriGuard auto-escalates any such ingredient when you select the Child profile.
    
    **🩺 Personalised Risk**
    A diabetic needs to know 5g sugar is already too much. A pregnant person needs to know which preservatives to avoid entirely. Generic labels don't tell you this. We do.
    """, unsafe_allow_html=True)

# 🛠️ FIXED: Used pure Markdown to prevent HTML rendering glitches
with tab_arch:
    st.markdown("""
## 🧠 The Multi-Agent Architecture: How NutriGuard Pro Thinks

NutriGuard Pro doesn't just read labels; it debates them. We utilize a **Sequential Multi-Agent System** where five specialized AI personas collaborate, fact-check each other, and synthesize data to provide a medically and legally sound verdict.

---

### 🤖 Agent Squad

* **👁️ LabelExtractorAgent (The Vision Specialist)**
  * **The Role:** The frontline data pipeline.
  * **How it works:** It uses state-of-the-art multimodal vision to scan every pixel of a food package. It bypasses marketing fluff to extract the raw truth: the microscopic ingredient lists, hidden nutritional tables, and mandatory FSSAI warning text (like "Not recommended for children"). It translates images into structured, machine-readable JSON data.

* **⚖️ RegulatoryAuditorAgent (The FSSAI Enforcer)**
  * **The Role:** The legal compliance officer.
  * **How it works:** This agent takes the raw data and audits every marketing claim against Indian law. If a package claims to be "Healthy" but exceeds the High Fat, Sugar, and Salt (HFSS) thresholds, this agent throws a red flag. It actively looks for profile-specific hard stops, such as flagging caffeinated beverages for children or pregnant users.

* **🛡️ SanityAgent (The Truth Guard)**
  * **The Role:** The hallucination killer.
  * **How it works:** Large Language Models can sometimes be overly optimistic or misinterpret data. The SanityAgent sits in the middle of the pipeline to cross-reference the Extractor's raw data with the Auditor's conclusions. It ensures no discrepancies exist and guarantees that the final report is grounded strictly in the printed facts.

* **🩺 WellnessAdvisorAgent (The Clinical Dietitian)**
  * **The Role:** The personalized health calculator.
  * **How it works:** It computes a dynamic Nutri-Score (A–E). Unlike generic calculators, it re-weights its algorithm based on the user's specific health profile. It compares the extracted nutrients against WHO guidelines and ICMR dietary limits to generate a strict consumption verdict.

* **🧪 EducationAgent (The Food Scientist)**
  * **The Role:** The toxicologist and health coach.
  * **How it works:** It scans the ingredient list for chemical preservatives, artificial colors, and synthetic additives (INS codes). It translates complex chemical names into plain-English long-term health impacts and generates actionable "Smart Swaps".

---

### 📡 The Infrastructure: Powering the Intelligence

NutriGuard Pro is built on a modern, enterprise-grade AI stack designed for speed, accuracy, and absolute factual grounding.

* **🔵 Gemini 2.5 Flash:** The core cognitive engine. We leverage Gemini's massive context window and lightning-fast multimodal reasoning to instantly process high-resolution images.
* **🟢 AlloyDB + pgvector:** Our high-performance, PostgreSQL-compatible database deployed on Google Cloud. It acts as our semantic memory bank.
* **🟡 Google ADK (Agent Development Kit):** The orchestration framework. The ADK wires our five agents together, handling complex routing and sequential memory.
* **🔴 FSSAI Gazette RAG:** The source of truth. NutriGuard Pro uses Retrieval-Augmented Generation to fetch exact clauses from the official FSSAI Gazette.
    """)

