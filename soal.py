import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os

# --- 1. KONFIGURASI API (AUTO-DETECT) ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan!")
        st.stop()
    genai.configure(api_key=api_key)
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
    title = doc.add_heading('PERANGKAT PENILAIAN HOTS - SMPN 2 KALIPARE', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}\nMata Pelajaran: {mapel}\nKelas / Fase: VII / Fase D\n" + "-"*40)
    
    table_data = []
    in_table = False
    for line in text.split('\n'):
        clean = line.strip()
        if '|' in clean:
            if all(c in '|- : ' for c in clean) and clean != "": continue
            cells = [c.strip() for c in clean.split('|') if c.strip()]
            if cells: table_data.append(cells); in_table = True
        else:
            if in_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=max(len(r) for r in table_data))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < len(table.columns): table.cell(r, c).text = val
                except: pass
                doc.add_paragraph(""); table_data = []; in_table = False
            if clean:
                if clean.startswith('###'): doc.add_heading(clean.replace('###', ''), level=1)
                else: doc.add_paragraph(clean)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")
st.markdown('<style>.header { background: #1e3c72; color: white; padding: 20px; border-radius: 10px; text-align: center; }</style>', unsafe_allow_html=True)
st.markdown('<div class="header"><h1>SMP NEGERI 2 KALIPARE</h1><p>Generator Soal HOTS dengan Pengaturan Jumlah Detail</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    source = st.radio("Input Materi:", ["Teks Manual", "Upload PDF"])
    materi_text = ""
    if source == "Teks Manual":
        materi_text = st.text_area("Tempelkan Materi Pelajaran:", height=350)
    else:
        f = st.file_uploader("Pilih PDF Materi", type=["pdf"])
        if f:
            pdf = PdfReader(f)
            for p in pdf.pages: materi_text += p.extract_text()

with col2:
    st.write("⚙️ **Pengaturan Soal**")
    mapel_name = st.text_input("Mata Pelajaran", "Seni Rupa")
    
    # 1. Pilih Bentuk Soal
    bentuk_list = st.multiselect(
        "Pilih Bentuk Soal:", 
        ["Pilihan Ganda", "PG Kompleks", "Menjodohkan", "Isian Singkat", "Uraian"],
        default=["Pilihan Ganda"]
    )
    
    # 2. Atur Jumlah per Bentuk Soal
    dict_jumlah = {}
    if bentuk_list:
        st.write("---")
        st.write("🔢 **Jumlah per Bentuk:**")
        for b in bentuk_list:
            dict_jumlah[b] = st.number_input(f"Jumlah {b}:", min_value=0, max_value=20, value=1)
    
    total_soal = sum(dict_jumlah.values())
    st.info(f"Total Soal: {total_soal}")

    if st.button("Generate Soal & Kartu Soal ✨"):
        if materi_text and total_soal > 0:
            with st.spinner("Menyusun soal sesuai komposisi..."):
                try:
                    # Menyusun rincian untuk prompt
                    rincian_soal = ", ".join([f"{v} soal {k}" for k, v in dict_jumlah.items() if v > 0])
                    
                    prompt = (
                        f"Instansi: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_text[:2500]}.\n"
                        f"Buatlah total {total_soal} soal HOTS (Level L3) dengan rincian: {rincian_soal}.\n\n"
                        f"OUTPUT WAJIB:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No|TP|Materi|Indikator|Level|No Soal)\n"
                        f"2. ### KARTU SOAL (Wajib tabel per nomor. Baris: CP, TP, Materi Utama, Buku Sumber, Indikator, Level (L3), Bentuk, No/Kunci/Skor, Stimulus, Soal, Pilihan Jawaban/Opsi).\n"
                        f"3. ### NASKAH SOAL (Disusun rapi per kategori soal).\n"
                        f"4. ### KUNCI JAWABAN.\n\n"
                        f"Gunakan simbol '|' untuk semua tabel."
                    )
                    
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
                    st.download_button("📥 Download Word", export_to_word(res.text, "SMP NEGERI 2 KALIPARE", mapel_name), f"Soal_{mapel_name}.docx")
                except Exception as e:
                    if "429" in str(e): st.error("⚠️ Kuota API habis. Tunggu 60 detik atau gunakan API Key lain.")
                    else: st.error(f"Kesalahan: {e}")
