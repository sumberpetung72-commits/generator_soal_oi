import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import os

# --- 1. KONFIGURASI KEAMANAN & INISIALISASI MODEL ---
def init_api():
    try:
        # Mengambil API Key dari Secrets Streamlit Cloud
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan! Masukkan GEMINI_API_KEY di menu Secrets.")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        # STRATEGI AUTO-DETECT: Mencari model yang tersedia untuk API Key Anda
        with st.spinner("Menghubungkan ke server Google AI..."):
            available_models = [
                m.name for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            
            if available_models:
                # Mengambil model pertama yang tersedia (biasanya gemini-1.5-flash atau pro)
                selected_model = available_models[0]
                return genai.GenerativeModel(selected_model)
            else:
                st.error("❌ Tidak ada model Gemini yang aktif untuk API Key ini.")
                st.stop()
                
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.info("Saran: Pastikan API Key Anda benar dan sudah mengaktifkan Generative Language API di Google AI Studio.")
        st.stop()

# Inisialisasi Model
model = init_api()

# --- 2. FUNGSI EXPORT KE WORD ---
def export_to_word(text):
    doc = Document()
    doc.add_heading('GuruAI Pro: Hasil Perangkat Ujian', 0)
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN ANTARMUKA (UI) ---
st.set_page_config(page_title="GuruAI Pro", page_icon="🎓", layout="wide")

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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. KONTEN UTAMA ---
st.title("🎓 GuruAI Pro: Generator Soal")
st.write("Aplikasi pembuat soal otomatis berbasis AI untuk Guru Indonesia.")

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
    jenjang = st.selectbox("Jenjang", ["SD", "SMP", "SMA/SMK"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Soal ✨"):
        if materi_final:
            with st.spinner("🤖 AI sedang berpikir..."):
                try:
                    prompt = (
                        f"Buatkan {jumlah} soal pilihan ganda HOTS jenjang {jenjang} "
                        f"berdasarkan materi berikut: {materi_final[:5000]}. "
                        f"Berikan juga kisi-kisi dan kunci jawabannya."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("---")
                    st.success("Selesai!")
                    st.markdown(hasil)
                    
                    # Download Button
                    word_file = export_to_word(hasil)
                    st.download_button(
                        label="📥 Download ke Word (.docx)",
                        data=word_file,
                        file_name="Soal_GuruAI.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Gagal memproses AI: {e}")
        else:
            st.warning("Materi tidak boleh kosong!")

st.markdown("<br><center style='color: #888;'>© 2026 GuruAI Pro</center>", unsafe_allow_html=True)
