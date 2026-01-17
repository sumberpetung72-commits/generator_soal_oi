import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI KEAMANAN & INISIALISASI MODEL ---
def init_api():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan! Masukkan GEMINI_API_KEY di menu Secrets.")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        if available_models:
            selected_model = available_models[0]
            return genai.GenerativeModel(selected_model)
        else:
            st.error("❌ Tidak ada model Gemini yang aktif.")
            st.stop()
                
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EXPORT KE WORD DENGAN KOP SEKOLAH ---
def export_to_word(text):
    doc = Document()
    
    # Menambah Header SMP NEGERI 2 KALIPARE di Word
    header = doc.add_heading('SMP NEGERI 2 KALIPARE', 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subheader = doc.add_paragraph('PERANGKAT PENILAIAN PEMBELAJARAN')
    subheader.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("_" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Isi konten
    doc.add_paragraph(text)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN ANTARMUKA (UI) ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .header-box {
        background-color: #007bff;
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
    }
    .main-card {
        background-color: white; 
        padding: 30px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #28a745, #85d017);
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold;
        height: 3.5em;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HEADER SEKOLAH ---
st.markdown("""
    <div class="header-box">
        <h1 style='margin:0;'>SMP NEGERI 2 KALIPARE</h1>
        <p style='margin:0;'>Sistem Generator Soal & Perangkat Ujian Otomatis</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Metode Input Materi:", ["Teks Manual", "Upload PDF"])
    
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Masukkan Materi Pelajaran:", height=300, placeholder="Tempel materi di sini...")
    else:
        file_pdf = st.file_uploader("Pilih file PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages:
                materi_final += page.extract_text()
            st.success("Teks PDF berhasil dimuat!")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan**")
    jenjang = st.selectbox("Jenjang", ["SMP", "Lainnya"])
    jumlah = st.slider("Jumlah Soal", 1, 30, 10)
    
    if st.button("Generate Soal Sekarang ✨"):
        if materi_final:
            with st.spinner("🤖 AI sedang menyusun soal untuk SMPN 2 Kalipare..."):
                try:
                    prompt = (
                        f"Bertindaklah sebagai guru profesional di SMP NEGERI 2 KALIPARE. "
                        f"Buatkan {jumlah} soal pilihan ganda HOTS jenjang {jenjang} "
                        f"berdasarkan materi berikut: {materi_final[:5000]}. "
                        f"Sertakan kisi-kisi dan kunci jawabannya."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("---")
                    st.success("✅ Soal Berhasil Dibuat!")
                    st.markdown(hasil)
                    
                    word_file = export_to_word(hasil)
                    st.download_button(
                        label="📥 Download File untuk SMPN 2 Kalipare (.docx)",
                        data=word_file,
                        file_name="Soal_SMPN2_Kalipare.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Gagal memproses AI: {e}")
        else:
            st.warning("Materi tidak boleh kosong!")

st.markdown("<br><center style='color: #888;'>© 2026 Perangkat AI - SMP NEGERI 2 KALIPARE</center>", unsafe_allow_html=True)
