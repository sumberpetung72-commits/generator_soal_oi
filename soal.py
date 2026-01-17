import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
import os

# --- 1. KONFIGURASI API (OPTIMASI KECEPATAN) ---
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
        
        # Menggunakan gemini-1.5-flash untuk proses 3x lebih cepat
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (KONVERSI TABEL OTOMATIS) ---
def export_to_word(text, school_name):
    doc = Document()
    header = doc.add_heading(school_name, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    lines = text.split('\n')
    table_data = []
    is_table = False

    for line in lines:
        if '|' in line and '---' not in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                is_table = True
        else:
            if is_table and table_data:
                # Membuat tabel asli di Word
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            table.cell(r, c).text = val
                except:
                    pass
                doc.add_paragraph("")
                table_data = []
                is_table = False
            
            if line.strip() and not is_table:
                if line.startswith('###'):
                    doc.add_heading(line.replace('###', ''), level=1)
                else:
                    doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. FUNGSI EKSPOR PDF ---
def export_to_pdf(text, school_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, school_name, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    
    lines = text.split('\n')
    for line in lines:
        clean_line = line.replace('|', ' ').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_line)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. UI TAMPILAN ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Perangkat Ujian Cepat (Gemini 1.5 Flash)</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Sumber Materi:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Masukkan Materi:", height=300)
    else:
        file_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan**")
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG", "Uraian"])
    jumlah = st.slider("Jumlah Soal", 1, 30, 5)
    
    if st.button("Generate Cepat ✨"):
        if materi_final:
            with st.spinner("⚡ AI Flash sedang bekerja cepat..."):
                try:
                    prompt = (
                        f"Materi: {materi_final[:3500]}. Mapel: {mapel}. Sekolah: SMP NEGERI 2 KALIPARE. "
                        f"Buat {jumlah} soal dengan bentuk {', '.join(bentuk)}.\n\n"
                        f"OUTPUT WAJIB:\n"
                        f"1. TABEL KISI-KISI: (No | TP | Materi | Indikator | Level | No Soal).\n"
                        f"2. TABEL KARTU SOAL: Buat per nomor soal (No | TP | Materi | Indikator | Level | Kunci | Rumusan Soal).\n"
                        f"3. NASKAH SOAL: Rapi dengan stimulus HOTS.\n"
                        f"4. KUNCI & PEMBAHASAN."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("### 📋 Hasil Generate")
                    st.markdown(hasil)
                    
                    st.divider()
                    st.download_button("📥 Word (Tabel Rapi)", data=export_to_word(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.docx", use_container_width=True)
                    st.download_button("📥 PDF", data=export_to_pdf(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal: {e}")
        else:
            st.warning("Materi tidak boleh kosong!")
