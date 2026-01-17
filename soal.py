import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI API (UPDATE: AUTO-DETECT MODEL) ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan!")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    try:
        # Mencari model yang tersedia secara dinamis
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Cari flash dulu, jika tidak ada pakai yang tersedia
        target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
        return genai.GenerativeModel(target_model)
    except Exception as e:
        # Fallback jika list_models gagal
        return genai.GenerativeModel('gemini-1.5-flash')

model = init_api()

# --- 2. FUNGSI EKSPOR WORD ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    title = doc.add_heading('PERANGKAT PENILAIAN KURIKULUM MERDEKA', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}\nMata Pelajaran: {mapel}\nKelas / Fase: VII / Fase D\n" + "-"*40)
    
    lines = text.split('\n')
    table_data = []
    in_table = False

    for line in lines:
        clean_line = line.strip()
        if '|' in clean_line:
            if all(c in '|- : ' for c in clean_line) and clean_line != "": continue
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                in_table = True
        else:
            if in_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=max(len(r) for r in table_data))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < len(table.columns): table.cell(r, c).text = val
                except: pass
                doc.add_paragraph("")
                table_data = []
                in_table = False
            
            if clean_line:
                if clean_line.startswith('###'): doc.add_heading(clean_line.replace('###', ''), level=1)
                elif clean_line.startswith('**'):
                    p = doc.add_paragraph()
                    p.add_run(clean_line.replace('**', '')).bold = True
                else: doc.add_paragraph(clean_line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. UI STREAMLIT ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")
st.markdown('<style>.header { background: #1e3c72; color: white; padding: 20px; border-radius: 10px; text-align: center; }</style>', unsafe_allow_html=True)
st.markdown('<div class="header"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Kisi-kisi & Kartu Soal Berbasis Materi</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    source = st.radio("Input:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if source == "Teks Manual":
        materi_final = st.text_area("Tempel Materi:", height=300)
    else:
        f = st.file_uploader("Upload PDF", type=["pdf"])
        if f:
            pdf = PdfReader(f)
            for p in pdf.pages: materi_final += p.extract_text()

with col2:
    st.write("⚙️ **Opsi**")
    mapel_name = st.text_input("Mapel", "Seni Rupa")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)
    
    if st.button("Generate Dokumen ✨"):
        if materi_final:
            with st.spinner("Sedang memproses..."):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_final[:3000]}.\n"
                        f"Buat {jumlah} soal {', '.join(bentuk)}.\n\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No|TP|Materi|Indikator|Level|No Soal)\n"
                        f"2. ### KARTU SOAL (Tabel Markdown per nomor: CP, TP, Materi Utama, Buku Sumber, Indikator, Level, Bentuk, No/Kunci/Skor, Stimulus, Soal, Pilihan Jawaban)\n"
                        f"3. ### NASKAH SOAL & KUNCI JAWABAN."
                    )
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
                    st.download_button("📥 Download Word", export_to_word(res.text, "SMP NEGERI 2 KALIPARE", mapel_name), f"Perangkat_{mapel_name}.docx")
                except Exception as e:
                    st.error(f"Kesalahan: {e}")
