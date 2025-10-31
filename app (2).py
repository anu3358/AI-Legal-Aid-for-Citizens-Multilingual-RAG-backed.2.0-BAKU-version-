# app.py

# 1️⃣ Imports first
import streamlit as st
from pathlib import Path
import json, base64
from rag import Retriever
from template_generator import generate_fir, generate_rti_application
from utils import detect_language, tts_play_bytes, transcribe_audio_streamlit, translate_text

# 2️⃣ Page config (must be first Streamlit command)
st.set_page_config(
    page_title='BAKU THE "NYAY BUDDY" - Auto multilingual RAG',
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3️⃣ Custom dark theme & background
st.markdown("""
    <style>
    .stApp {
        background-color: #0b132b;
        color: #e0e6ed;
        background-image: url("https://raw.githubusercontent.com/yourusername/yourrepo/main/nyay_buddy_logo.png");
        background-size: 25%;
        background-position: right top;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.98;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #1e1e1e;
        color: white;
    }
    .stButton>button {
        background-color: #00C4FF;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0090cc;
    }
    .stSidebar {
        background-color: #121212;
        color: white;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00C4FF !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4️⃣ Header
st.markdown("""
<h1 style="color:#00C4FF; margin-bottom:0;">⚖️ BAKU THE "NYAY BUDDY"</h1>
<p style="color:#cbd5e1; margin-top:0;">Auto multilingual RAG - ANURAG SAINI</p>
""", unsafe_allow_html=True)

# 5️⃣ Load Knowledge Base (dataset)
KB_PATH = Path("data/kb.json")
if not KB_PATH.exists():
    st.error("❌ Missing dataset file. Please add `data/kb.json` to your GitHub repo.")
    st.stop()

with open(KB_PATH, "r", encoding="utf-8") as f:
    kb = json.load(f)

retriever = Retriever(kb)

# 6️⃣ Sidebar — Helplines
st.sidebar.header("Quick Helplines")
st.sidebar.markdown("""
- **Emergency:** 112  
- **Legal Aid (NALSA):** 15100  
- **Women Helpline:** 181  
- **Child Helpline:** 1098  
- **Cybercrime:** 1930
""")

if st.sidebar.button("Show Sample Questions"):
    sample = "\n".join([q.get("question") or q.get("title") for q in kb[:25]])
    st.sidebar.text_area("Sample questions", value=sample, height=300)

# 7️⃣ Tabs
tab1, tab2 = st.tabs(["Ask Nyay Buddy", "Generate FIR / RTI"])

with tab1:
    st.header("Ask a Legal Question (Text or Audio)")
    col1, col2 = st.columns([3, 1])

    with col1:
        user_q = st.text_area("Enter your question:", height=150, placeholder="Type or paste here (English / हिन्दी / ਪੰਜਾਬੀ)")
        lang_override = st.selectbox("Language (Auto-detect if Auto):", ["Auto", "English", "Hindi", "Punjabi"])

        if st.button("Get Answer"):
            if not user_q.strip():
                st.warning("Please type a question.")
            else:
                # Language detection
                if lang_override == "Auto":
                    lang = detect_language(user_q)
                else:
                    lang = {"English": "en", "Hindi": "hi", "Punjabi": "pa"}[lang_override]

                with st.spinner("🔍 Retrieving relevant laws and generating answer..."):
                    contexts = retriever.retrieve(user_q, top_k=6)
                    answer = retriever.generate_answer(user_q, contexts, lang=lang)

                st.subheader("Answer")
                st.write(answer)

                # Helpline
                if contexts and contexts[0].get("helpline"):
                    st.info(f"📞 Relevant Helpline: {contexts[0].get('helpline')}")

                # Steps
                steps_seen = set()
                all_steps = []
                for c in contexts:
                    for step in c.get("steps", []):
                        if step not in steps_seen:
                            steps_seen.add(step)
                            all_steps.append(step)
                if all_steps:
                    st.subheader("Action Steps")
                    for i, s in enumerate(all_steps[:6], start=1):
                        st.write(f"{i}. {s}")

                # Sources
                st.subheader("Relevant Acts / Sources")
                for c in contexts:
                    st.write(f"- **{c.get('title', '-')}:** {c.get('law_reference', '-')}")
                
                # TTS
                if st.button("🔊 Play Answer (Audio)"):
                    audio_bytes = tts_play_bytes(answer, lang=lang)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.warning("TTS unavailable.")

    with col2:
        st.markdown("### Voice Input (Audio Upload)")
        audio_file = st.file_uploader("Upload your question (wav/mp3/m4a):", type=["wav", "mp3", "m4a"])
        if audio_file:
            with st.spinner("🎙️ Transcribing..."):
                txt = transcribe_audio_streamlit(audio_file)
            if txt:
                st.success("Transcribed Text:")
                st.write(txt)
                st.info("Copy it to the question box and click Get Answer.")

        st.markdown("---")
        st.markdown("<small>Developed by ANURAG SAINI (BAKU)</small>", unsafe_allow_html=True)

with tab2:
    st.header("Auto FIR / RTI Template Generator")

    with st.form("fir_form"):
        cname = st.text_input("Complainant Name")
        caddr = st.text_area("Complainant Address")
        contact = st.text_input("Contact (Phone / Email)")
        accused = st.text_input("Accused Name (if known)")
        idate = st.date_input("Incident Date")
        iplace = st.text_input("Incident Place")
        idetails = st.text_area("Incident Details")
        suspected = st.text_input("Suspected Sections (e.g., Section 379 IPC)")
        submitted = st.form_submit_button("Generate FIR")

    if submitted:
        fir_data = {
            "complainant_name": cname,
            "complainant_address": caddr,
            "contact": contact,
            "accused_name": accused,
            "incident_date": idate.strftime("%Y-%m-%d"),
            "incident_place": iplace,
            "incident_details": idetails,
            "suspected_sections": suspected
        }
        doc_bytes = generate_fir(fir_data)
        st.download_button("📄 Download FIR (DOCX)", data=doc_bytes, file_name="FIR_draft.docx")

st.markdown("---")
st.markdown("<small style='color:#9CA3AF;'>Developed by ANURAG SAINI (BAKU) — BAKU THE 'NYAY BUDDY'</small>", unsafe_allow_html=True)
