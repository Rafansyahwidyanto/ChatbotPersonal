"""
Applikasi streamlit chatbot

Cara jalankan:
>>> streamlit run app.py
"""

import os
import streamlit as st
from langchain.messages import AIMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

st.set_page_config(page_title="Rafa Chatbot", page_icon="🤖")
st.title("Rafa Chatbot")
st.markdown("Hi! Saya Rafa. Silahkan chat dengan AI assistant saya ya...")

### ==================================================== ###
### 1. SISTEM LOGIN API KEY                              ###
### ==================================================== ###
if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.environ.get("GOOGLE_API_KEY", "")

# Jika API Key belum ada, tahan UI di sini
if not st.session_state["api_key"]:
    st.warning("⚠️ Silakan masukkan API Key Gemini Anda untuk memulai chatbot.")
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        api_input = st.text_input("API Key", type="password", label_visibility="collapsed", placeholder="Paste API Key Gemini di sini...")
    with col2:
        if st.button("Submit"):
            if api_input.strip():
                st.session_state["api_key"] = api_input.strip()
                os.environ["GOOGLE_API_KEY"] = api_input.strip()
                st.rerun()
            else:
                st.error("API Key tidak valid!")
    st.stop() # Hentikan eksekusi, jangan baca kode ke bawah

### ==================================================== ###
### 2. KONFIGURASI CHATBOT (SIDEBAR)                     ###
### ==================================================== ###
st.sidebar.header("⚙️ Konfigurasi Chatbot")

use_case = st.sidebar.selectbox(
    "Use Case",
    ["Personal Productivity Assistant", "Travel Assistant", "Education Bot", "Customer Service Bot"],
)

gaya_bahasa = st.sidebar.selectbox(
    "Gaya Bahasa",
    ["Santai", "Formal"],
)

domain_map = {
    "Personal Productivity Assistant": ["Umum", "Manajemen Waktu", "Produktivitas Kerja", "Kebiasaan & Habit"],
    "Travel Assistant": ["Umum", "Destinasi Domestik", "Destinasi Internasional", "Budget Travel"],
    "Education Bot": ["Umum", "Matematika", "Bahasa Inggris", "Sains", "Sejarah"],
    "Customer Service Bot": ["Umum", "Keluhan Produk", "Info Layanan", "Panduan Penggunaan"],
}
domain = st.sidebar.selectbox("Domain Pengetahuan", domain_map[use_case])

temperature = st.sidebar.slider("Kreativitas Jawaban (temperature)", 0.0, 1.0, 0.7)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Fitur Rekomendasi")
rekomendasi_map = {
    "Personal Productivity Assistant": [
        "Buatkan jadwal harian yang produktif",
        "Bagaimana cara mengatasi rasa malas?",
        "Tips fokus kerja 2 jam tanpa distraksi",
    ],
    "Travel Assistant": [
        "Rekomendasikan itinerary 3 hari di Bali",
        "Destinasi liburan hemat di Jawa Tengah",
        "Barang apa saja yang wajib dibawa saat traveling?",
    ],
    "Education Bot": [
        "Jelaskan konsep dasar aljabar",
        "Bagaimana cara belajar efektif untuk ujian?",
        "Berikan contoh soal fisika sederhana",
    ],
    "Customer Service Bot": [
        "Bagaimana cara komplain produk yang rusak?",
        "Berapa lama proses pengembalian dana?",
        "Cara menghubungi customer service 24 jam",
    ],
}
rekomendasi_terpilih = None
for saran in rekomendasi_map[use_case]:
    if st.sidebar.button(saran, key=saran):
        rekomendasi_terpilih = saran

st.sidebar.markdown("---")
reset_memory = st.sidebar.button("🔄 Reset Percakapan")

### ==================================================== ###
### 3. MANAJEMEN STATE HISTORY                           ###
### ==================================================== ###
gaya_text = "santai, ramah, boleh gunakan bahasa sehari-hari dan emoji sesekali" if gaya_bahasa == "Santai" else "formal, sopan, dan profesional"

system_prompt_text = (
    f"You are a helpful chatbot acting as a {use_case} with knowledge focus on {domain}. "
    f"Gunakan gaya bahasa {gaya_text}. "
    "Reply to user chat in short message, max 1 paragraph."
)

current_config = f"{use_case}-{gaya_bahasa}-{domain}"
config_changed = st.session_state.get("chat_config") != current_config

if "chat_history" not in st.session_state or config_changed or reset_memory:
    st.session_state["chat_config"] = current_config
    st.session_state["chat_history"] = [SystemMessage(system_prompt_text)]

# Render history ke layar
for chat in st.session_state["chat_history"]:
    if type(chat) is SystemMessage:
        continue
    role = "User" if type(chat) is HumanMessage else "AI"
    with st.chat_message(role):
        st.markdown(chat.text)

### ==================================================== ###
### 4. EKSEKUSI CHAT & LLM (LAZY INITIALIZATION)         ###
### ==================================================== ###
user_prompt = st.chat_input("Ask AI")
if rekomendasi_terpilih:
    user_prompt = rekomendasi_terpilih

if user_prompt:
    # 1. Simpan dan tampilkan chat user
    st.session_state["chat_history"].append(HumanMessage(user_prompt))
    with st.chat_message("User"):
        st.markdown(user_prompt)

    # 2. Panggil AI HANYA saat ada prompt masuk
    with st.chat_message("AI"):
        with st.spinner("Rafa sedang mengetik..."):
            try:
                # Mematuhi pesan error dari API, gunakan versi terbaru
                client = ChatGoogleGenerativeAI(
                    model="gemini-3.6-flash", 
                    temperature=temperature,
                    api_key=st.session_state["api_key"]
                )
                
                response = client.invoke(st.session_state["chat_history"])
                st.markdown(response.text)
                st.session_state["chat_history"].append(response)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memanggil AI: {str(e)}")