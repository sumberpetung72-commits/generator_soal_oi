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
        
        # Mengambil daftar model yang tersedia untuk akun ini
        with st.spinner("Mengecek ketersediaan model..."):
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Prioritas: 1. Flash (Cepat), 2. Pro (Stabil), 3. Apa saja yang ada
            if 'models/gemini-1.5-flash' in available_models:
                target_model = 'models/gemini-1.5-flash'
            elif 'models/gemini-1.0-pro' in available_models:
                target_model = 'models/gemini-1.0-pro'
            elif available_models:
                target_model = available_models[0]
            else:
                st.error("Tidak ada model Gemini yang tersedia.")
                st.stop()
                
            return genai.GenerativeModel(target_model)
    except Exception as e:
        st.error(f"Kesalahan Inisialisasi: {e}")
        st.stop()

model = init_api()

# --- 2. FUNGSI EKSPOR WORD (TABEL NATIVE) ---
def export_to_word(text, school_name):
    doc = Document()
    header = doc.add_heading(school_name, 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    lines = text.split('\n')
    table_data = []
    is_table = False

    for line in lines:
        if '|' in line and '---' not in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                is_table = True
        else:
            if is_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for r, row in enumerate(table_data):
                        for c, val in enumerate(row):
                            if c < len(table_data[0]):
                                table.cell(r, c).text = val
                except:
                    pass
                doc.add_paragraph("")
                table_data = []
                is_table = False
            
            if line.strip() and not is_table:
                if line.startswith('###'):
                    doc.add_heading(line.replace('###', ''), level=1)
                else:
                    doc.add_paragraph(line)

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
        clean_line = line.replace('|', '  ').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_line)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. TAMPILAN DASHBOARD ---
st.set_page_config(page_title="GuruAI - SMPN 2 Kalipare", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 25px; border-radius: 15px; text-align: center; }
    .main-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>SMP NEGERI 2 KALIPARE</h1><p>Sistem Generator Perangkat Ujian Otomatis</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    input_choice = st.radio("Pilih Sumber Materi:", ["Teks Manual", "Upload PDF"])
    materi_final = ""
    if input_choice == "Teks Manual":
        materi_final = st.text_area("Tempelkan Materi Pelajaran:", height=300)
    else:
        file_pdf = st.file_uploader("Unggah File PDF", type=["pdf"])
        if file_pdf:
            reader = PdfReader(file_pdf)
            for page in reader.pages: materi_final += page.extract_text()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.write("⚙️ **Parameter Dokumen**")
    mapel = st.text_input("Mata Pelajaran", "Seni Rupa")
    bentuk = st.multiselect(
        "Pilih Bentuk Soal:", 
        ["PG", "PG Kompleks", "Benar/Salah", "Menjodohkan", "Uraian"], 
        default=["PG"]
    )
    jumlah = st.slider("Total Soal", 1, 40, 5)
    
    if st.button("Generate Perangkat Lengkap ✨"):
        if materi_final:
            with st.spinner("AI sedang menyusun kisi-kisi, kartu soal, dan naskah..."):
                try:
                    prompt = (
                        f"Sekolah: SMP NEGERI 2 KALIPARE. Mapel: {mapel}. Materi: {materi_final[:3500]}.\n"
                        f"Buat {jumlah} soal dengan bentuk {', '.join(bentuk)}.\n\n"
                        f"FORMAT WAJIB:\n"
                        f"1. TABEL KISI-KISI: (No | TP | Materi | Indikator | Level | No Soal).\n"
                        f"2. TABEL KARTU SOAL: Per nomor soal (No | Materi | Indikator | Level | Kunci | Rumusan Soal).\n"
                        f"3. NASKAH SOAL: Stimulus HOTS, soal, dan pilihan jawaban.\n"
                        f"4. KUNCI JAWABAN & PEMBAHASAN.\n\n"
                        f"Gunakan tabel Markdown '|' secara konsisten."
                    )
                    
                    response = model.generate_content(prompt)
                    hasil = response.text
                    
                    st.markdown("---")
                    st.markdown(hasil)
                    
                    st.divider()
                    st.write("📥 **Unduh Dokumen:**")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button("Word (Tabel Rapi)", data=export_to_word(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Perangkat_{mapel}.docx", use_container_width=True)
                    with c2:
                        st.download_button("PDF (Teks)", data=export_to_pdf(hasil, "SMP NEGERI 2 KALIPARE"), file_name=f"Perangkat_{mapel}.pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal memproses: {e}")
        else:
            st.warning("Silakan masukkan materi terlebih dahulu.")
