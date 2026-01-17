import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
import os

# --- 1. KONFIGURASI API DENGAN AUTO-FALLBACK ---
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
        
        if 'models/gemini-1.5-flash' in available_models:
            target = 'models/gemini-1.5-flash'
        else:
            target = available_models[0]
            
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"Kesalahan Inisialisasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (ADAPTASI FORMAT KARTU SOAL) ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Header Identitas Sekolah sesuai format docx
    h = doc.add_heading('Format Kartu Soal (Kurikulum Merdeka)', 1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Identitas Sekolah: {school_name}")
    doc.add_paragraph(f"Mata Pelajaran: {mapel}")
    doc.add_paragraph("Kelas / Fase: VII / Fase D")
    doc.add_paragraph("Kurikulum: Kurikulum Merdeka")
    doc.add_paragraph("Penyusun: [Nama Guru]")
    doc.add_paragraph("-" * 30)
    
    lines = text.split('\n')
    table_data = []

    for line in lines:
        clean_line = line.strip()
        # Deteksi tabel markdown
        if '|' in clean_line and not all(c in '|- ' for c in clean_line):
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells: table_data.append(cells)
        else:
            if table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < len(table_data[0]):
                                table.cell(r, c).text = val
                except: pass
                doc.add_paragraph("")
                table_data = []
            
            if clean_line and not all(c in '|- ' for c in clean_line):
                if clean_line.startswith('###'):
                    doc.add_heading(clean_line.replace('###', ''), level=2)
                else:
                    doc.add_paragraph(clean_line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    th, td { border: 1px solid #ddd !important; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Guru & Kartu Soal Standar</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Metode Input:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        file_pdf = st.file_uploader("Pilih PDF Materi", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter Administrasi**")
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    fitur = st.multiselect(
        "Komponen Dokumen:",
        ["Kisi-kisi", "Kartu Soal", "Naskah Soal", "Analisis Butir Soal", "Daftar Nilai"],
        default=["Kartu Soal", "Naskah Soal"]
    )
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Dokumen ✨"):
        if materi_final:
            with st.spinner("Menyusun dokumen sesuai format SMPN 2 Kalipare..."):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel}. Materi: {materi_final[:3000]}.\n"
                        f"Buat {jumlah} soal sesuai komponen: {', '.join(fitur)}.\n\n"
                        f"KHUSUS UNTUK KARTU SOAL, gunakan tabel Markdown dengan baris berikut untuk SETIAP nomor:\n"
                        f"- Capaian Pembelajaran (CP)\n"
                        f"- Tujuan Pembelajaran (TP)\n"
                        f"- Materi Utama\n"
                        f"- Indikator Soal (Disajikan [stimulus], peserta didik dapat [tindakan] [materi])\n"
                        f"- Level Kognitif (L1/L2/L3)\n"
                        f"- Bentuk Soal\n"
                        f"- Nomor Soal | Kunci Jawaban | Skor\n"
                        f"- Stimulus\n"
                        f"- Rumusan Soal\n"
                        f"- Pilihan Jawaban (A, B, C, D)\n\n"
                        f"Pastikan tabel menggunakan pembatas '|' yang rapi."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil_ai = response.text
                    
                    st.markdown("### 📋 Pratinjau Dokumen")
                    st.markdown(hasil_ai)
                    
                    st.divider()
                    st.download_button(
                        "📥 Download Word (Format Standar)", 
                        data=export_to_word(hasil_ai, "SMP NEGERI 2 KALIPARE", mapel), 
                        file_name=f"Perangkat_Ujian_{mapel}.docx", 
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        else:
            st.warning("Mohon masukkan materi materi.")
