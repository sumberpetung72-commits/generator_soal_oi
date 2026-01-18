import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI API ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan! Masukkan di Streamlit Secrets.")
        st.stop()
    genai.configure(api_key=api_key)
    # Mencari model yang tersedia secara dinamis
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if "1.5-flash" in m), models[0])
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = init_api()

# --- 2. FUNGSI EKSPOR WORD ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Header Dokumen
    title = doc.add_heading('PERANGKAT PENILAIAN HOTS - KURIKULUM MERDEKA', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}\nMata Pelajaran: {mapel}\nFase/Kelas: D / VII\n" + "-"*40)
    
    table_data = []
    in_table = False

    for line in text.split('\n'):
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
st.set_page_config(page_title="GuruAI - HOTS Edition", layout="wide")

st.markdown("""
    <style>
    .header-box { background: #1e3c72; color: white; padding: 20px; border-radius: 10px; text-align: center; }
    .main-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Soal HOTS & Kartu Soal Standar</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    source = st.radio("Input Materi:", ["Teks Manual", "Upload PDF"])
    materi_text = ""
    if source == "Teks Manual":
        materi_text = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        f = st.file_uploader("Pilih PDF Materi", type=["pdf"])
        if f:
            pdf = PdfReader(f)
            for p in pdf.pages: materi_text += p.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter Soal HOTS**")
    mapel_name = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG", "PG Kompleks"])
    jumlah = st.slider("Jumlah Soal", 1, 15, 5)
    
    if st.button("Generate Soal HOTS ✨"):
        if materi_text:
            with st.spinner("Menyusun soal HOTS (Level L3: Analisis/Evaluasi)..."):
                try:
                    prompt = (
                        f"Instansi: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_text[:2500]}.\n"
                        f"Buatlah {jumlah} soal HOTS (Level L3) dengan bentuk: {', '.join(bentuk)}.\n\n"
                        f"KETENTUAN OUTPUT:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No|TP|Materi|Indikator|Level|No Soal)\n"
                        f"2. ### KARTU SOAL (Wajib menggunakan tabel Markdown per nomor soal. Harus ada baris 'Buku Sumber').\n"
                        f"   Isi baris: CP, TP, Materi Utama, Buku Sumber, Indikator, Level (L3), Bentuk, No/Kunci/Skor, Stimulus, Soal, Opsi.\n"
                        f"3. ### NASKAH SOAL (Tampilkan naskah soal lengkap sesuai bentuk yang dipilih).\n"
                        f"4. ### KUNCI JAWABAN & PEMBAHASAN.\n\n"
                        f"Gunakan simbol '|' untuk semua tabel agar terbaca oleh sistem ekspor."
                    )
                    
                    response = model.generate_content(prompt)
                    output = response.text
                    
                    st.markdown(output)
                    st.download_button(
                        "📥 Download Dokumen Word",
                        data=export_to_word(output, "SMP NEGERI 2 KALIPARE", mapel_name),
                        file_name=f"Soal_HOTS_{mapel_name}.docx"
                    )
                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ Kuota API habis. Silakan coba lagi dalam 1 menit atau gunakan API Key lain.")
                    else:
                        st.error(f"Terjadi kesalahan: {e}")
