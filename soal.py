import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import os

# --- 1. KONFIGURASI KEAMANAN API ---
def init_api():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan di Secrets!")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        # Menggunakan versi terbaru yang paling stabil
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI WORD ---
def export_to_word(text):
    doc = Document()
    doc.add_heading('GuruAI Pro: Hasil Perangkat Ujian', 0)
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN UI ---
st.set_page_config(page_title="GuruAI Pro", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 20px; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 25px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #007bff, #00c6ff);
        color: white !important; border-radius: 12px !important;
        border: none !important; font-weight: bold; height: 3.5em; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. KONTEN ---
st.title("📝 Generator Soal AI")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Input Materi:", ["Teks", "PDF"])
    materi_final = ""
    if input_choice == "Teks":
        materi_final = st.text_area("Masukkan Materi:", height=300)
    else:
        file_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages:
                materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter**")
    jenjang = st.selectbox("Jenjang", ["SD", "SMP", "SMA"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Mulai Generate ✨"):
        if materi_final:
            with st.spinner("AI sedang bekerja..."):
                try:
                    # Instruksi lebih detail agar hasil lebih bagus
                    prompt = f"Buatkan {jumlah} soal Pilihan Ganda standar HOTS untuk jenjang {jenjang} berdasarkan materi berikut ini. Sertakan kunci jawaban di bagian akhir: {materi_final[:5000]}"
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.success("Berhasil Membuat Soal!")
                    st.markdown(hasil)
                    
                    st.download_button(
                        label="📥 Download Hasil ke Word",
                        data=export_to_word(hasil),
                        file_name="soal_ujian_ai.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Gagal saat generate soal: {e}")
        else:
            st.warning("Materi belum diisi!")
