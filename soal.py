import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import os

# --- 1. KONFIGURASI KEAMANAN API ---
def init_api():
    try:
        # Mengambil API Key dari Secrets Streamlit Cloud
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan! Pastikan sudah memasukkan GEMINI_API_KEY di menu Secrets.")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        # Menggunakan gemini-1.0-pro untuk kompatibilitas maksimal dengan v1beta
        return genai.GenerativeModel('gemini-1.0-pro')
    except Exception as e:
        st.error(f"Kesalahan Inisialisasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EXPORT KE WORD ---
def export_to_word(text):
    doc = Document()
    doc.add_heading('GuruAI Pro: Perangkat Ujian', 0)
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN ANTARMUKA (UI) ---
st.set_page_config(page_title="GuruAI Pro", page_icon="🎓", layout="wide")

# CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; 
        padding: 30px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #007bff, #00c6ff);
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold;
        height: 3.5em;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0, 123, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. KONTEN UTAMA ---
st.title("🎓 GuruAI Pro: Generator Soal HOTS")
st.write("Buat soal ujian dan kisi-kisi otomatis berbasis Kurikulum Merdeka.")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Pilih Sumber Materi:", ["Ketik Teks Manual", "Unggah Dokumen PDF"])
    
    materi_final = ""
    if input_choice == "Ketik Teks Manual":
        materi_final = st.text_area("Masukkan Materi Pelajaran:", height=300, placeholder="Tempel materi di sini...")
    else:
        file_pdf = st.file_uploader("Upload PDF Materi", type=["pdf"])
        if file_pdf:
            with st.spinner("Membaca dokumen..."):
                reader = PdfReader(file_pdf)
                for page in reader.pages:
                    materi_final += page.extract_text()
            st.success("Teks PDF berhasil diambil!")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan Soal**")
    jenjang = st.selectbox("Jenjang Sekolah", ["SD", "SMP", "SMA/SMK"])
    jumlah = st.slider("Jumlah Soal PG", 1, 20, 5)
    
    if st.button("Generate Sekarang ✨"):
        if materi_final:
            with st.spinner("🤖 AI sedang menyusun soal..."):
                try:
                    prompt = (
                        f"Bertindaklah sebagai pakar pembuat soal Kurikulum Merdeka. "
                        f"Berdasarkan materi: {materi_final[:5000]}. "
                        f"Buatkan {jumlah} soal pilihan ganda standar HOTS untuk jenjang {jenjang}. "
                        f"Sertakan tabel kisi-kisi dan kunci jawaban di akhir."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil_teks = response.text
                    
                    st.markdown("---")
                    st.success("✅ Soal Berhasil Dibuat!")
                    st.markdown(hasil_teks)
                    
                    # Tombol Download
                    word_file = export_to_word(hasil_teks)
                    st.download_button(
                        label="📥 Download File Word (.docx)",
                        data=word_file,
                        file_name="Soal_GuruAI_Pro.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memproses AI: {e}")
        else:
            st.warning("Mohon masukkan materi terlebih dahulu!")

st.markdown("<br><center style='color: #888;'>© 2026 GuruAI Pro Indonesia</center>", unsafe_allow_html=True)
