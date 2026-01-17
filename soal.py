import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
from io import BytesIO
import os

# --- 1. KONFIGURASI API ---
def init_api():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan!")
            st.stop()
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"Error Inisialisasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (FORMAT STANDAR SMPN 2 KALIPARE) ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Judul Dokumen
    title = doc.add_heading('PERANGKAT PENILAIAN KURIKULUM MERDEKA', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Header Identitas
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}")
    doc.add_paragraph(f"Mata Pelajaran: {mapel}")
    doc.add_paragraph("Kelas / Fase: VII / Fase D")
    doc.add_paragraph("Kurikulum: Kurikulum Merdeka")
    doc.add_paragraph("-" * 40)
    
    lines = text.split('\n')
    table_data = []

    for line in lines:
        clean_line = line.strip()
        # Deteksi Tabel Markdown
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
                    doc.add_heading(clean_line.replace('###', ''), level=1)
                elif clean_line.startswith('**'):
                    p = doc.add_paragraph()
                    p.add_run(clean_line.replace('**', '')).bold = True
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
    th, td { border: 1px solid #ddd !important; padding: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Penilaian Lengkap & Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_source = st.radio("Sumber Materi:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_source == "Teks Manual":
        materi_final = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        file_pdf = st.file_uploader("Pilih PDF Materi", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter Dokumen**")
    mapel_name = st.text_input("Mata Pelajaran", "Seni Rupa")
    
    # PILIHAN BENTUK SOAL LENGKAP
    bentuk_terpilih = st.multiselect(
        "Pilih Bentuk Soal:",
        ["Pilihan Ganda (PG)", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"],
        default=["Pilihan Ganda (PG)", "Uraian"]
    )
    
    fitur_tambahan = st.multiselect(
        "Fitur Tambahan:",
        ["Analisis Butir Soal", "Daftar Nilai"],
        default=[]
    )
    
    jumlah_soal = st.slider("Total Soal", 1, 30, 5)
    
    if st.button("Generate Administrasi Lengkap ✨"):
        if materi_final and bentuk_terpilih:
            with st.spinner("Menyusun dokumen standar Kurikulum Merdeka..."):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mata Pelajaran: {mapel_name}. Materi: {materi_final[:3500]}.\n"
                        f"Buat {jumlah_soal} soal dengan variasi bentuk: {', '.join(bentuk_terpilih)}.\n\n"
                        f"STRUKTUR OUTPUT:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No | TP | Materi | Indikator | Level | No Soal)\n"
                        f"2. ### KARTU SOAL (WAJIB sesuai format: Capaian Pembelajaran, Tujuan Pembelajaran, Materi Utama, Indikator Soal, Level Kognitif, Bentuk Soal, No Soal|Kunci|Skor, Stimulus, Rumusan Soal, Pilihan Jawaban)\n"
                        f"3. ### NASKAH SOAL (Disusun rapi per nomor)\n"
                        f"4. ### KUNCI JAWABAN & PEMBAHASAN\n"
                        f"5. Tambahkan komponen: {', '.join(fitur_tambahan)} jika dipilih.\n\n"
                        f"PENTING: Gunakan tabel Markdown '|' untuk semua bagian tabel agar terbaca oleh sistem ekspor."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil_teks = response.text
                    
                    st.markdown("### 📋 Pratinjau Dokumen")
                    st.markdown(hasil_teks)
                    
                    st.divider()
                    st.download_button(
                        "📥 Download Perangkat Word (Format Lengkap)",
                        data=export_to_word(hasil_teks, "SMP NEGERI 2 KALIPARE", mapel_name),
                        file_name=f"Administrasi_{mapel_name}.docx",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Gagal: {e}")
        else:
            st.warning("Pilih materi dan minimal satu bentuk soal!")
