import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# --- 2. FUNGSI EKSPOR WORD ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Judul & Identitas (Sesuai Format Kartu Soal.docx)
    title = doc.add_heading('DOKUMEN ADMINISTRASI PENILAIAN', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}")
    doc.add_paragraph(f"Mata Pelajaran: {mapel}")
    doc.add_paragraph("Kelas / Fase: VII / Fase D")
    doc.add_paragraph("Kurikulum: Kurikulum Merdeka")
    doc.add_paragraph("Penyusun: [Nama Guru]")
    doc.add_paragraph("-" * 40)
    
    lines = text.split('\n')
    table_data = []
    in_table = False

    for line in lines:
        clean_line = line.strip()
        if '|' in clean_line:
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
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #ddd; }
    th, td { border: 1px solid #ddd !important; padding: 10px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Penghasil Kartu Soal & Administrasi Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    source = st.radio("Input Materi:", ["Teks Manual", "Upload PDF"])
    materi_text = ""
    if source == "Teks Manual":
        materi_text = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        f = st.file_uploader("Pilih PDF", type=["pdf"])
        if f:
            pdf = PdfReader(f)
            for p in pdf.pages: materi_text += p.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter**")
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah = st.slider("Jumlah Soal", 1, 25, 5)
    
    if st.button("Generate Dokumen Lengkap ✨"):
        if materi_text:
            with st.spinner("Menyusun Administrasi & Kartu Soal..."):
                try:
                    prompt = (
                        f"Instansi: SMP NEGERI 2 KALIPARE. Mapel: {mapel}. Materi: {materi_text[:3000]}.\n"
                        f"Buat {jumlah} soal {', '.join(bentuk)}.\n\n"
                        f"STRUKTUR OUTPUT:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No | TP | Materi | Indikator | Level | No Soal)\n"
                        f"2. ### KARTU SOAL (Wajib menggunakan tabel Markdown untuk setiap nomor dengan baris):\n"
                        f"   | Komponen | Keterangan |\n"
                        f"   | :--- | :--- |\n"
                        f"   | Capaian Pembelajaran | [Isi CP] |\n"
                        f"   | Tujuan Pembelajaran | [Isi TP] |\n"
                        f"   | Materi Utama | [Isi Materi] |\n"
                        f"   | Buku Sumber | [Tuliskan Judul Buku yang Relevan] |\n"
                        f"   | Indikator Soal | [Isi Indikator] |\n"
                        f"   | Level Kognitif | [Isi Level] |\n"
                        f"   | Bentuk Soal | [Isi Bentuk] |\n"
                        f"   | No Soal, Kunci, Skor | [Isi Detail] |\n"
                        f"   | Stimulus | [Isi Stimulus] |\n"
                        f"   | Rumusan Soal | [Isi Soal] |\n"
                        f"   | Pilihan Jawaban | [Isi Opsi] |\n\n"
                        f"3. ### NASKAH SOAL & KUNCI JAWABAN."
                    )
                    
                    res = model.generate_content(prompt)
                    output = res.text
                    
                    st.markdown("### 📋 Pratinjau")
                    st.markdown(output)
                    
                    st.divider()
                    st.download_button(
                        "📥 Download Word (Tabel & Buku Sumber)",
                        data=export_to_word(output, "SMP NEGERI 2 KALIPARE", mapel),
                        file_name=f"Administrasi_{mapel}.docx",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Gagal: {e}")
