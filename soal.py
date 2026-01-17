import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
# =========================
# CONFIG HALAMAN
# =========================
st.set_page_config(
    page_title="Generator Soal OI",
    page_icon="📘",
    layout="centered"
)

# =========================
# LOAD API KEY (AMAN)
# =========================
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY belum diset di Streamlit Secrets")
    st.stop()

genai.configure(api_key=api_key)

# =========================
# CSS & JS KUSTOM
# =========================
st.markdown("""
<style>
.stTextArea textarea {
    background: rgba(255,255,255,0.95);
    border-radius: 20px !important;
    border: 2px solid #e0e0e0 !important;
}
div.stButton > button {
    background: linear-gradient(135deg, #007bff, #00c6ff);
    color: white !important;
    border-radius: 50px !important;
    padding: 14px 30px !important;
    font-weight: 700 !important;
}
.exam-paper {
    background: white;
    padding: 40px;
    border-left: 5px solid #007bff;
    border-radius: 12px;
    margin-top: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
}
</style>

<script>
const scrollResult = () => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
};
</script>
""", unsafe_allow_html=True)

# =========================
# UI
# =========================
st.title("📘 Generator Soal Olimpiade Informatika")
st.caption("Didukung oleh Google Gemini")

materi = st.text_area(
    "🧠 Materi / Topik Soal",
    placeholder="Contoh: Dynamic Programming, Graph BFS/DFS, Greedy, Segment Tree...",
    height=150
)

tingkat = st.selectbox(
    "🎯 Tingkat Kesulitan",
    ["Mudah", "Sedang", "Sulit"]
)

# =========================
# GENERATE SOAL
# =========================
if st.button("🚀 Generate Soal"):
    if not materi.strip():
        st.warning("Materi tidak boleh kosong!")
    else:
        with st.spinner("Menyusun soal OI..."):
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
Buat satu soal Olimpiade Informatika tingkat {tingkat}.

Materi utama: {materi}

Format WAJIB:
1. Judul Soal
2. Deskripsi Masalah
3. Format Input
4. Format Output
5. Contoh Input
6. Contoh Output
7. Penjelasan Singkat

Gunakan bahasa Indonesia.
Soal harus orisinal dan layak lomba OI.
"""

            response = model.generate_content(prompt)

        st.markdown(
            f"""
            <div class="exam-paper">
            {response.text.replace('\n', '<br>')}
            </div>
            <script>scrollResult();</script>
            """,
            unsafe_allow_html=True
        )

