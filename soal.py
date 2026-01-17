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

# --- 2. FUNGSI EKSPOR WORD (LOGIKA PARSING TABEL TERKUAT) ---
def export_to_word(text, school_name, mapel):
    doc = Document()
    
    # Judul Dokumen
    title = doc.add_heading('DOKUMEN ADMINISTRASI PENILAIAN', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Header Identitas
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
        
        # Deteksi Baris Tabel (mengandung karakter |)
        if '|' in clean_line:
            # Mengabaikan baris pemisah markdown seperti |---|---|
            if all(c in '|- : ' for c in clean_line) and clean_line != "":
                continue
            
            # Mengambil data sel
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                in_table = True
        else:
            # Jika keluar dari baris tabel, buat tabel di Word
            if in_table and table_data:
                try:
                    # Tentukan jumlah kolom maksimal agar tidak error
                    num_cols = max(len(row) for row in table_data)
                    table = doc.add_table(rows=len(table_data), cols=num_cols)
                    table.style = 'Table Grid'
                    
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < num_cols:
                                table.cell(r, c).text = val
                except Exception as e:
                    doc.add_paragraph(f"[Gagal membuat tabel: {str(e)}]")
                
                doc.add_paragraph("") # Spasi setelah tabel
                table_data = []
                in_table = False
            
            # Tambahkan teks biasa (Judul atau Soal)
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

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Penilaian Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_source = st.radio("Metode Input Materi:", ["Teks Manual", "Upload PDF"])
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
    st.write("⚙️ **Parameter Administrasi**")
    mapel_name = st.text_input("Mata Pelajaran", "Umum")
    bentuk_soal = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah_soal = st.slider("Jumlah Soal", 1, 30, 5)
    
    if st.button("Generate Dokumen ✨"):
        if materi_final:
            with st.spinner("Menyusun Kisi-kisi dan Kartu Soal..."):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel_name}. Materi: {materi_final[:3500]}.\n"
                        f"Buat {jumlah_soal} soal {', '.join(bentuk_soal)}.\n\n"
                        f"FORMAT WAJIB:\n"
                        f"1. ### KISI-KISI SOAL: Buat tabel (No | TP | Materi | Indikator | Level | No Soal).\n"
                        f"2. ### KARTU SOAL: Setiap nomor soal wajib dibuat dalam satu tabel Markdown yang berisi baris: "
                        f"Capaian Pembelajaran, Tujuan Pembelajaran, Materi Utama, Indikator Soal, Level Kognitif, Bentuk Soal, No Soal|Kunci|Skor, Stimulus, Rumusan Soal, Pilihan Jawaban.\n"
                        f"3. ### NASKAH SOAL: List soal secara rapi.\n\n"
                        f"PASTIKAN semua tabel menggunakan karakter '|' sebagai pemisah kolom."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil_teks = response.text
                    
                    st.markdown("### 📋 Pratinjau")
                    st.markdown(hasil_teks)
                    
                    st.divider()
                    st.download_button(
                        "📥 Download Word (Format Tabel Rapi)",
                        data=export_to_word(hasil_teks, "SMP NEGERI 2 KALIPARE", mapel_name),
                        file_name=f"Administrasi_{mapel_name}.docx",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Gagal: {e}")
