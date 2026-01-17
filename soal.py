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
            st.error("⚠️ API Key tidak ditemukan di Secrets!")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        # Mengecek model yang tersedia
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if 'models/gemini-1.5-flash' in available_models:
            target = 'models/gemini-1.5-flash'
        elif 'models/gemini-1.0-pro' in available_models:
            target = 'models/gemini-1.0-pro'
        else:
            target = available_models[0]
            
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"Kesalahan Inisialisasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (LOGIKA TABEL DIPERKUAT) ---
def export_to_word(text, school_name):
    doc = Document()
    header = doc.add_heading(school_name, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    lines = text.split('\n')
    table_data = []

    for line in lines:
        clean_line = line.strip()
        # Mendeteksi baris tabel (mengandung |) tapi bukan baris pemisah |---|
        if '|' in clean_line and not all(c in '|- ' for c in clean_line):
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
        else:
            # Jika ada data tabel yang terkumpul, gambar ke Word
            if table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < len(table_data[0]):
                                table.cell(r, c).text = val
                except:
                    pass
                doc.add_paragraph("") # Spasi antar tabel
                table_data = [] # Reset data tabel
            
            # Tambahkan teks biasa (Judul atau Soal)
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

# --- 3. FUNGSI EKSPOR PDF ---
def export_to_pdf(text, school_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, school_name, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    
    lines = text.split('\n')
    for line in lines:
        # Menghapus simbol markdown agar PDF bersih
        clean_line = line.replace('|', '  ').replace('**', '').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_line)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. TAMPILAN DASHBOARD ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    /* Memaksa tampilan tabel di layar agar bergaris */
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #ddd !important; padding: 10px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Administrasi Penilaian Otomatis (Rapi & Cepat)</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Metode Input:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        file_pdf = st.file_uploader("Pilih PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Pengaturan**")
    mapel = st.text_input("Mata Pelajaran", "Umum")
    bentuk = st.multiselect("Bentuk Soal:", ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], default=["PG"])
    jumlah = st.slider("Jumlah Soal", 1, 30, 5)
    
    if st.button("Generate Dokumen Rapi ✨"):
        if materi_final:
            with st.spinner("Menyusun tabel Kisi-kisi, Kartu Soal, dan Naskah..."):
                try:
                    # PROMPT DIPERKETAT AGAR TABEL TIDAK GAGAL
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel}. Materi: {materi_final[:3000]}.\n"
                        f"Tugas: Buat {jumlah} soal {', '.join(bentuk)}.\n\n"
                        f"WAJIB IKUTI URUTAN INI:\n"
                        f"1. ### KISI-KISI SOAL\n"
                        f"Buat satu tabel Markdown dengan kolom: No | Materi | Indikator | Level | No Soal.\n\n"
                        f"2. ### KARTU SOAL\n"
                        f"Buat tabel Markdown terpisah untuk setiap soal dengan kolom: No | TP | Materi | Kunci | Rumusan Soal.\n\n"
                        f"3. ### NASKAH SOAL\n"
                        f"Tuliskan soal secara lengkap dan rapi.\n\n"
                        f"4. ### KUNCI JAWABAN\n\n"
                        f"PENTING: Gunakan pembatas '|' yang jelas untuk setiap baris tabel."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil_ai = response.text
                    
                    st.markdown("### 📄 Hasil Pratinjau")
                    st.markdown(hasil_ai)
                    
                    st.divider()
                    st.write("📥 **Unduh File:**")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button("Word (Tabel Terdeteksi)", data=export_to_word(hasil_ai, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.docx", use_container_width=True)
                    with c2:
                        st.download_button("PDF (Format Teks)", data=export_to_pdf(hasil_ai, "SMP NEGERI 2 KALIPARE"), file_name=f"Soal_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        else:
            st.warning("Materi tidak boleh kosong!")
