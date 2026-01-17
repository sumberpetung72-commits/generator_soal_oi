import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO

# --- 1. KONFIGURASI KEAMANAN API ---
# Di Streamlit Cloud, masukkan API Key di Settings > Secrets:
# GEMINI_API_KEY = "KODE_API_ANDA"
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ API Key tidak ditemukan! Masukkan GEMINI_API_KEY di menu Secrets Streamlit.")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. FUNGSI PEMBUAT WORD ---
def export_to_word(text):
    doc = Document()
    doc.add_heading('GuruAI: Perangkat Ujian Otomatis', 0)
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN UI (CSS KUSTOM) ---
st.set_page_config(page_title="GuruAI Pro", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; 
        padding: 25px; 
        border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #007bff, #00c6ff);
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold;
        height: 3em;
        width: 100%;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        text-align: center; color: #888; font-size: 12px; padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR PANDUAN ---
with st.sidebar:
    st.title("🎓 GuruAI Pro")
    st.write("Dibuat untuk membantu Guru menyusun soal HOTS secara instan.")
    st.divider()
    st.markdown("""
    **Cara Pakai:**
    1. Pilih metode input materi.
    2. Atur jenjang & jumlah soal.
    3. Klik **Generate**.
    4. Download hasil ke Word.
    """)
    st.divider()
    st.caption("v1.0 - Kurikulum Merdeka Ready")

# --- 5. KONTEN UTAMA ---
st.title("📝 Generator Soal & Kisi-kisi AI")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_type = st.radio("Metode Input Materi:", ["Teks Manual", "Upload File PDF"])
    
    materi_final = ""
    if input_type == "Teks Manual":
        materi_final = st.text_area("Tempel Materi Pelajaran:", height=300, placeholder="Contoh: Ekosistem adalah...")
    else:
        file_pdf = st.file_uploader("Pilih file PDF materi", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages:
                materi_final += page.extract_text()
            st.success("Teks PDF berhasil diekstrak!")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan**")
    jenjang = st.selectbox("Jenjang Pendidikan", ["SD", "SMP", "SMA/SMK"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Soal ✨"):
        if materi_final:
            with st.spinner("🤖 AI sedang menyusun soal..."):
                prompt = f"""
                Bertindaklah sebagai ahli kurikulum Indonesia. Materi: {materi_final[:6000]}
                Buatkan:
                1. Tabel Kisi-kisi (TP, Indikator, Level Kognitif, No Soal).
                2. {jumlah} Soal Pilihan Ganda jenjang {jenjang} berbasis HOTS.
                3. Kartu Soal dan Kunci Jawaban.
                Gunakan format Markdown yang rapi.
                """
                try:
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("---")
                    st.markdown(hasil)
                    
                    # Download Button
                    word_file = export_to_word(hasil)
                    st.download_button(
                        label="📥 Download ke Word (.docx)",
                        data=word_file,
                        file_name="perangkat_ujian_guruai.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Error AI: {e}")
        else:
            st.warning("Masukkan materi dulu!")

st.markdown('<div class="footer">© 2026 GuruAI Pro - Solusi Administrasi Guru</div>', unsafe_allow_html=True)
