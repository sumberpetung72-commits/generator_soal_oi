import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
import os
import re

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
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"Kesalahan Konfigurasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (DENGAN TABEL NYATA) ---
def export_to_word(text, school_name):
    doc = Document()
    
    # Header Sekolah
    section = doc.sections[0]
    header = doc.add_heading(school_name, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Memproses Teks: Mencari Tabel Markdown dan mengubahnya jadi Tabel Word
    lines = text.split('\n')
    is_table = False
    table_data = []

    for line in lines:
        if '|' in line:
            # Lewati garis pemisah markdown |---|
            if '---' in line:
                continue
            # Ambil data kolom
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                is_table = True
        else:
            if is_table and table_data:
                # Gambar Tabel di Word
                row_count = len(table_data)
                col_count = len(table_data[0])
                table = doc.add_table(rows=row_count, cols=col_count)
                table.style = 'Table Grid'
                for r in range(row_count):
                    for c in range(len(table_data[r])):
                        table.cell(r, c).text = table_data[r][c]
                doc.add_paragraph("") # Spasi setelah tabel
                table_data = []
                is_table = False
            
            if line.strip():
                if line.startswith('###'):
                    doc.add_heading(line.replace('###', ''), level=1)
                elif line.startswith('**'):
                    p = doc.add_paragraph()
                    p.add_run(line.replace('**', '')).bold = True
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
    pdf.set_font("Arial", size=9)
    
    # PDF rendering sederhana (mengubah tabel markdown jadi baris rapi)
    lines = text.split('\n')
    for line in lines:
        line = line.replace('|', '  ').replace('---', '')
        clean_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_line)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. UI STREAMLIT ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    table { width: 100%; border-collapse: collapse; border: 1px solid #ddd; }
    th, td { padding: 8px; border: 1px solid #ddd; text-align: left; }
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
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk_soal = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah = st.slider("Jumlah Soal", 1, 40, 5)
    
    if st.button("Generate Dokumen Rapi ✨"):
        if materi_final:
            with st.spinner("Sedang memproses..."):
                try:
                    prompt = (
                        f"Buatkan dokumen ujian SMP NEGERI 2 KALIPARE Mapel {mapel}. Materi: {materi_final[:4000]}.\n"
                        f"Variasi soal: {', '.join(bentuk_soal)}. Total: {jumlah} soal.\n\n"
                        f"WAJIB FORMAT:\n"
                        f"1. KISI-KISI: Buat satu tabel Markdown (No | TP | Materi | Indikator | Level | No Soal).\n"
                        f"2. KARTU SOAL: Buat tabel Markdown per nomor soal.\n"
                        f"3. NASKAH SOAL: List soal rapi.\n"
                        f"4. KUNCI JAWABAN."
                    )
                    response = model.generate_content(prompt)
                    hasil = response.text
                    st.markdown(hasil)
                    
                    st.divider()
                    st.download_button("📥 Download Word (Tabel Nyata)", data=export_to_word(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.docx", use_container_width=True)
                    st.download_button("📥 Download PDF", data=export_to_pdf(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal: {e}")
