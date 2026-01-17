import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import os

# --- 1. KONFIGURASI KEAMANAN API ---
# Fungsi untuk mengambil API Key dari Secrets Streamlit
def init_api():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            # Fallback jika dijalankan lokal
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan! Masukkan GEMINI_API_KEY di menu Secrets Streamlit.")
            st.stop()
            
        genai.configure(api_key=api_key)
       return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Terjadi kesalahan konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR KE WORD ---
def export_to_word(text):
    doc = Document()
    doc.add_heading('GuruAI Pro: Hasil Perangkat Ujian', 0)
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. TAMPILAN UI (CSS KUSTOM) ---
st.set_page_config(page_title="GuruAI Pro", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .main-card {
        background-color: white; 
        padding: 30px; 
        border-radius: 20px; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border: 1px solid #f0f0f0;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #007bff, #00c6ff);
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold;
        height: 3.5em;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 123, 255, 0.4);
    }
    .footer {
        text-align: center; color: #aaa; font-size: 13px; padding: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🎓 GuruAI Pro")
    st.info("Solusi AI untuk mempermudah administrasi guru Indonesia.")
    st.divider()
    st.markdown("""
    ### 📖 Cara Kerja:
    1. Pilih sumber materi (Teks/PDF).
    2. Tentukan jenjang & jumlah soal.
    3. Klik **Generate**.
    4. Unduh file Word yang sudah jadi.
    """)
    st.divider()
    st.caption("Versi 1.1 | Kurikulum Merdeka")

# --- 5. KONTEN UTAMA ---
st.title("📝 Generator Soal & Kisi-kisi Otomatis")
st.write("Buat soal HOTS, kisi-kisi, dan kartu soal dalam hitungan detik.")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Metode Input Materi:", ["Ketik/Tempel Teks", "Unggah Dokumen PDF"])
    
    materi_final = ""
    if input_choice == "Ketik/Tempel Teks":
        materi_final = st.text_area("Masukkan Materi Pelajaran:", height=300, 
                                    placeholder="Contoh: Ekosistem adalah hubungan timbal balik antara makhluk hidup...")
    else:
        file_pdf = st.file_uploader("Upload file PDF buku atau ringkasan", type=["pdf"])
        if file_pdf:
            with st.spinner("Mengekstrak teks dari PDF..."):
                reader = PdfReader(file_pdf)
                for page in reader.pages:
                    materi_final += page.extract_text()
            st.success("Teks PDF berhasil dibaca!")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter Ujian**")
    jenjang = st.selectbox("Jenjang", ["SD (Fase A-C)", "SMP (Fase D)", "SMA (Fase E-F)"])
    jumlah = st.slider("Jumlah Soal PG", 1, 25, 5)
    
    st.divider()
    
    if st.button("Mulai Proses AI ✨"):
        if materi_final:
            prog_bar = st.progress(0)
            msg = st.empty()
            
            try:
                msg.text("🤖 AI sedang menganalisis materi...")
                prog_bar.progress(30)
                
                prompt = f"""
                Sebagai pakar pendidikan Indonesia, analisis materi berikut: {materi_final[:7000]}
                Berdasarkan materi tersebut, buatkan perangkat ujian untuk {jenjang} meliputi:
                1. Tabel Kisi-kisi (Tujuan Pembelajaran, Indikator, Level Kognitif, No Soal).
                2. {jumlah} Soal Pilihan Ganda (PG) Standar HOTS.
                3. Kunci Jawaban dan Pembahasan Singkat.
                4. Kartu Soal.
                Format output harus rapi menggunakan Markdown.
                """
                
                response = model.generate_content(prompt)
                hasil_ai = response.text
                
                prog_bar.progress(80)
                msg.text("📝 Menyusun dokumen...")
                
                st.markdown("---")
                st.markdown("### 📋 Hasil Preview")
                st.markdown(hasil_ai)
                
                # Tombol Download
                file_word = export_to_word(hasil_ai)
                st.download_button(
                    label="📥 Download Hasil (Format Word .docx)",
                    data=file_word,
                    file_name="Perangkat_Ujian_GuruAI.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                
                prog_bar.progress(100)
                msg.text("✅ Berhasil dibuat!")
                
            except Exception as e:
                st.error(f"Terjadi kendala teknis: {e}")
        else:
            st.warning("Silakan masukkan materi terlebih dahulu.")

st.markdown('<div class="footer">© 2026 GuruAI Pro - Aplikasi AI Khusus Guru Indonesia</div>', unsafe_allow_html=True)


