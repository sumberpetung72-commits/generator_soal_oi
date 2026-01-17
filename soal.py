import streamlit as st

# --- KUSTOMISASI CSS & JS ---
st.markdown("""
    <style>
    /* 1. CSS: Efek Glassmorphism pada Input */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 20px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 15px rgba(0, 123, 255, 0.2) !important;
    }

    /* 2. CSS: Animasi Berdenyut pada Tombol */
    div.stButton > button {
        background: linear-gradient(135deg, #007bff, #00c6ff);
        color: white !important;
        border-radius: 50px !important;
        border: none !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: transform 0.2s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0, 123, 255, 0.3);
    }

    /* 3. CSS: Styling Hasil AI agar Seperti Kertas Ujian */
    .exam-paper {
        background-color: white;
        padding: 40px;
        border-left: 5px solid #007bff;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        font-family: 'Inter', sans-serif;
    }
    </style>

    <script>
    const scrollResult = () => {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    };
    </script>
    """, unsafe_allow_html=True)
