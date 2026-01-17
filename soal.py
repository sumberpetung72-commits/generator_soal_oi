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
            st.error("⚠️ API Key tidak ditemukan!")
            st.stop()
            
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(available_models[0]) if available_models else None
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
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, school_name, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI STREAMLIT ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    /* Menambah styling khusus tabel agar rapi di Streamlit */
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #f2f2f2; }
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
    mapel = st.text_input("Mata Pelajaran", "Umum")
    bentuk_soal = st.multiselect(
        "Pilih Bentuk Soal:",
        ["Pilihan Ganda (PG)", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"],
        default=["Pilihan Ganda (PG)"]
    )
    jumlah = st.slider("Total Jumlah Soal", 1, 40, 5)
    
    if st.button("Generate Dokumen Rapi ✨"):
        if materi_final and bentuk_soal:
            with st.spinner("AI sedang merapikan tabel dan naskah soal..."):
                try:
                    str_bentuk = ", ".join(bentuk_soal)
                    prompt = (
                        f"Anda adalah Guru Profesional di SMP NEGERI 2 KALIPARE. Materi: {materi_final[:5000]}. "
                        f"Buatkan dokumen untuk mata pelajaran {mapel} dengan jumlah {jumlah} soal yang terdiri dari: {str_bentuk}.\n\n"
                        f"WAJIB IKUTI FORMAT BERIKUT:\n"
                        f"1. **KISI-KISI SOAL**: Buat dalam bentuk TABEL MARKDOWN (Kolom: No, Tujuan Pembelajaran, Materi, Indikator Soal, Level Kognitif, No Soal).\n"
                        f"2. **KARTU SOAL**: Buat dalam bentuk TABEL MARKDOWN untuk SETIAP nomor soal (Kolom: Nomor, Kompetensi Dasat/TP, Materi, Indikator, Level, Kunci, Rumusan Soal).\n"
                        f"3. **NASKAH SOAL**: Tampilkan soal secara teratur. Gunakan format tebal (bold) untuk stimulus soal. Pilihan jawaban A, B, C, D disusun ke bawah.\n"
                        f"4. **KUNCI JAWABAN**: Berikan kunci jawaban dan pembahasan singkat.\n\n"
                        f"Pastikan tabel Markdown memiliki garis pembatas yang jelas agar rapi di Streamlit."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.success("✅ Dokumen Berhasil Disusun!")
                    st.markdown(hasil) # Streamlit otomatis merender tabel Markdown
                    
                    st.divider()
                    st.download_button("Download Word (.docx)", data=export_to_word(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.docx", use_container_width=True)
                    st.download_button("Download PDF (.pdf)", data=export_to_pdf(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal: {e}")
        else:
            st.warning("Lengkapi materi dan bentuk soal!")
