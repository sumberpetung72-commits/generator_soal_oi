import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI API (AUTO-DETECT & STABILIZER) ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan!")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    try:
        # Mencari model yang tersedia secara dinamis untuk menghindari Error 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prioritas model 1.5-flash yang lebih hemat kuota
        target = next((m for m in available_models if "1.5-flash" in m), available_models[0])
        return genai.GenerativeModel(target)
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (TABEL KARTU SOAL DENGAN BUKU SUMBER) ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Judul Identitas
    title = doc.add_heading('DOKUMEN ADMINISTRASI PENILAIAN', 0)
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
    .header-box { background: #1e3c72; color: white; padding: 20px; border-radius: 10px; text-align: center; }
    .main-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    th, td { border: 1px solid #ddd !important; padding: 10px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Kisi-kisi & Kartu Soal Standar</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    source = st.radio("Metode Input Materi:", ["Teks Manual", "Upload PDF"])
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
    st.write("⚙️ **Opsi Perangkat**")
    mapel_name = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk_soal = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah_soal = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Dokumen ✨"):
        if materi_text:
            with st.spinner("Menyusun perangkat (Pastikan kuota API tersedia)..."):
                try:
                    prompt = (
                        f"Instansi: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_text[:3000]}.\n"
                        f"Buatlah {jumlah_soal} soal dengan variasi: {', '.join(bentuk_soal)}.\n\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No | TP | Materi | Indikator | Level | No Soal)\n"
                        f"2. ### KARTU SOAL (Wajib menggunakan tabel Markdown per nomor soal dengan baris: "
                        f"Capaian Pembelajaran, Tujuan Pembelajaran, Materi Utama, Buku Sumber, Indikator Soal, Level Kognitif, Bentuk Soal, No Soal|Kunci|Skor, Stimulus, Rumusan Soal, Pilihan Jawaban).\n"
                        f"3. ### NASKAH SOAL & KUNCI JAWABAN."
                    )
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    st.divider()
                    st.download_button(
                        "📥 Download Word",
                        data=export_to_word(response.text, "SMP NEGERI 2 KALIPARE", mapel_name),
                        file_name=f"Perangkat_Ujian_{mapel_name}.docx",
                        use_container_width=True
                    )
                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ Kuota API habis (Error 429). Silakan coba lagi besok atau gunakan API Key dari akun Google yang berbeda.")
                    else:
                        st.error(f"Kesalahan: {e}")
