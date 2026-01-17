import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import os
import time

# --- 1. KONFIGURASI API DENGAN FALLBACK & RETRY ---
def init_api():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ API Key tidak ditemukan!")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # Mencoba daftar model yang tersedia
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prioritas Flash, jika gagal nanti akan ada penanganan error
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        return genai.GenerativeModel(target)
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash') # Default fallback

model = init_api()

# --- 2. FUNGSI EKSPOR WORD ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    title = doc.add_heading('ADMINISTRASI PENILAIAN TERPADU', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Satuan Pendidikan: {school_name}\nMata Pelajaran: {mapel}\nKurikulum: Kurikulum Merdeka\n" + "-"*40)
    
    table_data = []
    for line in text.split('\n'):
        clean = line.strip()
        if '|' in clean:
            if all(c in '|- : ' for c in clean) and clean != "": continue
            cells = [c.strip() for c in clean.split('|') if c.strip()]
            if cells: table_data.append(cells)
        else:
            if table_data:
                table = doc.add_table(rows=len(table_data), cols=max(len(r) for r in table_data))
                table.style = 'Table Grid'
                for r, row in enumerate(table_data):
                    for c, val in enumerate(row):
                        if c < len(table.columns): table.cell(r, c).text = val
                doc.add_paragraph("")
                table_data = []
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
st.markdown('<div class="header"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Penilaian Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    source = st.radio("Materi:", ["Teks", "PDF"])
    materi = ""
    if source == "Teks": materi = st.text_area("Input Materi:", height=250)
    else:
        f = st.file_uploader("Upload PDF", type=["pdf"])
        if f:
            reader = PdfReader(f)
            for p in reader.pages: materi += p.extract_text()

with col2:
    mapel = st.text_input("Mapel", "Seni Rupa")
    pilihan = st.multiselect("Komponen:", ["Kisi-kisi", "Kartu Soal", "Analisis UH", "Daftar Nilai"], default=["Kisi-kisi", "Kartu Soal"])
    jumlah = st.slider("Jumlah Soal", 1, 20, 5)

    if st.button("Generate Dokumen ✨"):
        if materi:
            with st.spinner("Proses AI... (Mohon tunggu jika antrean padat)"):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel}. Materi: {materi[:2500]}.\n"
                        f"Buatlah komponen berikut secara TERPISAH dan BERURUTAN:\n"
                        f"1. ### KISI-KISI SOAL (Tabel: No|TP|Materi|Indikator|Level|No Soal)\n"
                        f"2. ### KARTU SOAL (Tabel per nomor soal: CP|TP|Materi|Buku Sumber|Indikator|Level|Bentuk|No-Kunci-Skor|Stimulus|Soal|Opsi)\n"
                        f"3. ### ANALISIS ULANGAN HARIAN (Tabel TERPISAH: No Soal|Indikator Diuji|Tingkat Kesukaran|Daya Pembeda|Rekomendasi)\n"
                        f"4. ### DAFTAR NILAI SISWA (Tabel TERPISAH: No|Nama Siswa|Skor|Nilai Akhir|Ketuntasan)\n"
                        f"Gunakan format tabel Markdown '|' untuk semua tabel."
                    )
                    # Handle Quota Limit 429
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    st.download_button("📥 Download Word", export_to_word(response.text, "SMP NEGERI 2 KALIPARE", mapel), f"Admin_{mapel}.docx")
                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ Kuota API habis (Error 429). Silakan tunggu 60 detik atau gunakan API Key lain.")
                    else:
                        st.error(f"Terjadi kesalahan: {e}")
