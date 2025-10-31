import streamlit as st

st.set_page_config(
    page_title="NyayBuddy",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom dark background with readable text
st.markdown(
    """
    <style>
        .stApp {
            background-color: #1c1c1c;  /* Deep grey background */
            color: #f0f0f0;  /* Light text color */
        }

        .stTextInput > div > div > input,
        .stTextArea textarea {
            background-color: #2b2b2b;
            color: white;
        }

        .stButton>button {
            background-color: #007acc;
            color: white;
            border-radius: 8px;
        }

        .stButton>button:hover {
            background-color: #005fa3;
        }

        .stMarkdown, p, h1, h2, h3 {
            color: #f5f5f5 !important;
        }

        .stSidebar {
            background-color: #222222;
        }
    </style>
    """,
    unsafe_allow_html=True
)

import streamlit as st
from pathlib import Path
import json, base64
from rag import Retriever
from template_generator import generate_fir, generate_rti_application
from utils import detect_language, tts_play_bytes, transcribe_audio_streamlit

st.set_page_config(
    page_title='BAKU THE "NYAY BUDDY" - Auto multilingual RAG',
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme + header
st.markdown(
    """
    <style>
    :root { --bg:#071025; --card:#0f1724; --muted:#9CA3AF; --accent:#00E5FF; --text:#E6EEF8; }
    .stApp { background-color: var(--bg); color: var(--text); }
    .card { background: rgba(255,255,255,0.02); padding: 14px; border-radius: 12px; }
    .title { color: var(--accent); font-weight:700; }
    .muted { color: var(--muted); }
    .stButton>button { background-color: #0b1220; color: var(--text); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title" style="font-size:28px">⚖️ BAKU THE \"NYAY BUDDY\"</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">Auto multilingual RAG — Developed by ANURAG SAINI (BAKU)</div>', unsafe_allow_html=True)
st.markdown("---")

# Background watermark (logo)
LOGO = Path("nyay_buddy_logo.png")
if LOGO.exists():
    try:
        b64 = base64.b64encode(LOGO.read_bytes()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{b64}"); background-size: 28%; background-position: right 6% top 8%; background-repeat: no-repeat; opacity:0.12; }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

# Load KB & Retriever
KB_PATH = Path("data/kb.json")
if not KB_PATH.exists():
    st.error("Missing data/kb.json. Please add the dataset to data/kb.json")
    st.stop()

with open(KB_PATH, "r", encoding="utf-8") as f:
    kb = json.load(f)

retriever = Retriever(kb)

# Sidebar helplines
st.sidebar.header("Quick Helplines")
st.sidebar.markdown("""
- **Emergency:** 112  
- **Legal Aid (NALSA):** 15100  
- **Women Helpline:** 181  
- **Child Helpline:** 1098  
- **Cybercrime:** 1930
""")
st.sidebar.markdown("---")
if st.sidebar.button("Show sample questions"):
    sample = "\n".join([entry.get("question") or entry.get("title") for entry in kb[:30]])
    st.sidebar.text_area("Sample questions (copy-paste)", value=sample, height=300)

# Tabs
tab1, tab2 = st.tabs(["Ask Nyay Buddy", "Templates & Help"])

with tab1:
    st.header("Ask a legal question (Text or Audio)")
    col1, col2 = st.columns([3,1])

    with col1:
        user_q = st.text_area("Enter your question here:", height=150, placeholder="Ask in English, हिन्दी or ਪੰਜਾਬੀ")
        lang_override = st.selectbox("Language (Auto-detect if Auto):", ["Auto", "English", "Hindi", "Punjabi"])

        if st.button("Get Answer"):
            if not user_q or not user_q.strip():
                st.warning("Please enter a question.")
            else:
                # decide language code
                if lang_override == "Auto":
                    lang = detect_language(user_q)
                else:
                    lang = {"English":"en","Hindi":"hi","Punjabi":"pa"}[lang_override]

                with st.spinner("Retrieving relevant documents..."):
                    contexts = retriever.retrieve(user_q, top_k=6)
                    answer = retriever.generate_answer(user_q, contexts, lang=lang)

                st.markdown("### Answer")
                st.write(answer)

                # Show helpline if present
                if contexts and contexts[0].get("helpline"):
                    st.info(f"📞 Relevant helpline: {contexts[0].get('helpline')}")

                # Combine and show non-repetitive steps
                steps_seen = set()
                combined_steps = []
                for c in contexts:
                    for s in c.get("steps", []):
                        if s not in steps_seen:
                            combined_steps.append(s)
                            steps_seen.add(s)
                if combined_steps:
                    st.markdown("### Actionable Steps")
                    for i, s in enumerate(combined_steps[:6], start=1):
                        st.write(f"{i}. {s}")

                # Sources and acts
                st.markdown("### Sources & Acts")
                for c in contexts:
                    title = c.get("title", "-")
                    law = c.get("law_reference", "-")
                    src = c.get("source", "-")
                    score = c.get("score", None)
                    if score is not None:
                        st.write(f"- **{title}** — {law} — _{src}_  (score {score:.3f})")
                    else:
                        st.write(f"- **{title}** — {law} — _{src}_")

                # TTS playback
                if st.button("🔊 Play Answer (TTS)"):
                    audio_bytes = tts_play_bytes(answer, lang=lang)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.warning("TTS currently unavailable.")

    with col2:
        st.markdown("### Voice Input (upload)")
        audio_file = st.file_uploader("Upload audio (wav/mp3/m4a)", type=["wav","mp3","m4a"])
        if audio_file:
            with st.spinner("Transcribing audio..."):
                txt = transcribe_audio_streamlit(audio_file)
            if txt:
                st.success("Transcribed text:")
                st.write(txt)
                st.info("Copy the transcribed text into the question box and click Get Answer.")

        st.markdown("---")
        st.markdown("Developed by ANURAG SAINI (BAKU)")

with tab2:
    st.header("Generate FIR / RTI Templates")
    with st.form("fir_form"):
        cname = st.text_input("Complainant Name")
        caddr = st.text_area("Complainant Address")
        contact = st.text_input("Contact (phone/email)")
        accused = st.text_input("Accused Name (if known)")
        idate = st.date_input("Incident date")
        iplace = st.text_input("Incident place")
        idetails = st.text_area("Incident details")
        suspected = st.text_input("Suspected sections (e.g., Section 379 IPC)")
        submitted = st.form_submit_button("Generate FIR")
    if submitted:
        doc_bytes = generate_fir({
            "complainant_name": cname,
            "complainant_address": caddr,
            "contact": contact,
            "accused_name": accused,
            "incident_date": idate.strftime("%Y-%m-%d"),
            "incident_place": iplace,
            "incident_details": idetails,
            "suspected_sections": suspected
        })
        st.download_button("📄 Download FIR (DOCX)", data=doc_bytes, file_name="FIR_draft.docx")

st.markdown("---")
st.markdown("<small style='color:#9CA3AF'>Developed by ANURAG SAINI (BAKU) — BAKU THE \\\"NYAY BUDDY\\\"</small>", unsafe_allow_html=True)
