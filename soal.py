import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
import os

# --- 1. KONFIGURASI API ---
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
        # Mencari model yang tersedia secara dinamis
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR ---
def export_to_word(text, school_name):
    doc = Document()
    h = doc.add_heading(school_name, 0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def export_to_pdf(text, school_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, school_name, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    # PDF Sederhana hanya merender teks (Tabel Markdown akan dikonversi ke teks linear)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI STREAMLIT ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    /* Memperbaiki tampilan tabel di Streamlit */
    div[data-testid="stMarkdownContainer"] table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #ddd;
    }
    div[data-testid="stMarkdownContainer"] th {
        background-color: #f2f2f2;
        padding: 10px;
        border: 1px solid #ddd;
    }
    div[data-testid="stMarkdownContainer"] td {
        padding: 10px;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Penilaian Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Sumber Materi:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Masukkan Materi Pelajaran:", height=300)
    else:
        file_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan Dokumen**")
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk_soal = st.multiselect(
        "Bentuk Soal:",
        ["Pilihan Ganda (PG)", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"],
        default=["Pilihan Ganda (PG)", "Benar/Salah"]
    )
    jumlah = st.slider("Jumlah Soal", 1, 40, 5)
    
    if st.button("Generate Dokumen Rapi ✨"):
        if materi_final:
            with st.spinner("Menyusun tabel dan naskah soal..."):
                try:
                    str_bentuk = ", ".join(bentuk_soal)
                    prompt = (
                        f"Materi: {materi_final[:5000]}. Mapel: {mapel}. Sekolah: SMP NEGERI 2 KALIPARE. "
                        f"Buatkan {jumlah} soal dengan variasi bentuk: {str_bentuk}.\n\n"
                        f"FORMAT WAJIB:\n"
                        f"1. **KISI-KISI SOAL**: Buat satu tabel Markdown dengan kolom (No, Tujuan Pembelajaran, Materi, Indikator, Level Kognitif, No Soal).\n"
                        f"2. **KARTU SOAL**: Buat tabel Markdown terpisah untuk SETIAP nomor soal. Setiap tabel berisi baris: Nomor, TP, Materi, Indikator, Level, Kunci, dan Rumusan Soal.\n"
                        f"3. **NASKAH SOAL**: Tulis soal secara sistematis. Beri jarak antar nomor. Gunakan stimulus teks yang relevan sebelum pertanyaan.\n"
                        f"4. **KUNCI & PEMBAHASAN**: Daftar kunci jawaban beserta penjelasan logisnya.\n\n"
                        f"PENTING: Gunakan sintaks tabel Markdown '|' secara konsisten agar rapi."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("### 📋 Hasil Perangkat Ujian")
                    st.markdown(hasil)
                    
                    st.divider()
                    st.download_button("📥 Simpan ke Word", data=export_to_word(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.docx", use_container_width=True)
                    st.download_button("📥 Simpan ke PDF", data=export_to_pdf(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal: {e}")
        else:
            st.warning("Materi kosong!")
