import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI API (ANTI-LIMIT) ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan!")
        st.stop()
    
    genai.configure(api_key=api_key)
    # Gunakan 1.5-flash untuk kecepatan dan efisiensi kuota
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_api()

# --- 2. FUNGSI EKSPOR WORD ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Judul & Identitas
    title = doc.add_heading('DOKUMEN PERANGKAT PENILAIAN', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}")
    doc.add_paragraph(f"Mata Pelajaran: {mapel}")
    doc.add_paragraph("Kelas / Fase: VII / Fase D")
    doc.add_paragraph("Kurikulum: Kurikulum Merdeka")
    doc.add_paragraph("-" * 40)
    
    lines = text.split('\n')
    table_data = []
    in_table = False

    for line in lines:
        clean_line = line.strip()
        if '|' in clean_line:
            # Lewati baris pemisah markdown ---|---
            if all(c in '|- : ' for c in clean_line) and clean_line != "":
                continue
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                in_table = True
        else:
            if in_table and table_data:
                try:
                    num_cols = max(len(row) for row in table_data)
                    table = doc.add_table(rows=len(table_data), cols=num_cols)
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < num_cols:
                                table.cell(r, c).text = val
                except:
                    pass
                doc.add_paragraph("")
                table_data = []
                in_table = False
            
            if clean_line:
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

# --- 3. UI STREAMLIT ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: #1e3c72; color: white; padding: 20px; border-radius: 10px; text-align: center; }
    .main-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    th, td { border: 1px solid #ddd !important; padding: 8px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Kisi-kisi & Kartu Soal Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    source = st.radio("Metode Input:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if source == "Teks Manual":
        materi_final = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        f = st.file_uploader("Pilih PDF Materi", type=["pdf"])
        if f:
            pdf = PdfReader(f)
            for p in pdf.pages: materi_final += p.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan**")
    mapel_name = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Dokumen ✨"):
        if materi_final:
            with st.spinner("Menyusun Kisi-kisi dan Kartu Soal..."):
                try:
                    prompt = (
                        f"Instansi: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_final[:3000]}.\n"
                        f"Buatlah {jumlah} soal {', '.join(bentuk)}.\n\n"
                        f"WAJIB IKUTI STRUKTUR INI:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No | TP | Materi | Indikator | Level | No Soal)\n"
                        f"2. ### KARTU SOAL (Buat tabel Markdown per nomor soal dengan baris: Capaian Pembelajaran, Tujuan Pembelajaran, Materi Utama, Buku Sumber, Indikator Soal, Level Kognitif, Bentuk Soal, No Soal|Kunci|Skor, Stimulus, Rumusan Soal, Pilihan Jawaban).\n"
                        f"3. ### NASKAH SOAL & KUNCI JAWABAN.\n\n"
                        f"Pastikan tabel menggunakan pembatas '|' yang rapi."
                    )
                    
                    response = model.generate_content(prompt)
                    output_text = response.text
                    
                    st.markdown(output_text)
                    st.divider()
                    st.download_button(
                        "📥 Download Word (Format Rapi)",
                        data=export_to_word(output_text, "SMP NEGERI 2 KALIPARE", mapel_name),
                        file_name=f"Perangkat_Soal_{mapel_name}.docx",
                        use_container_width=True
                    )
                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ Kuota API habis (Error 429). Mohon tunggu sejenak atau ganti materi.")
                    else:
                        st.error(f"Terjadi kesalahan: {e}")
