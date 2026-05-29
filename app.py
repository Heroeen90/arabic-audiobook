import streamlit as st
import pypdf
import edge_tts
import asyncio
import os

st.set_page_config(page_title="قارئ الكتب الذكي", page_icon="📚", layout="centered")

st.title("📚 قارئ الكتب الصوتي الذكي")
st.write("قم برفع أي كتاب بصيغة PDF وسأقوم بقراءته لك بصوت أنثوي هادئ وباللغة العربية الفصحى.")

uploaded_file = st.file_uploader("اختر ملف الكتاب (PDF)", type=["pdf"])

voices = {
    "سلمى (نبرة مصرية هادئة ومميزة)": "ar-EG-SalmaNeural",
    "فاطمة (نبرة إماراتية واضحة وطبيعية)": "ar-AE-FatimaNeural",
    "أمينة (نبرة جزائرية وقورة)": "ar-DZ-AminaNeural"
}
selected_voice_label = st.selectbox("اختر نبرة الصوت الأنثوي المفضلة:", list(voices.keys()))
selected_voice = voices[selected_voice_label]

async def generate_speech(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    with st.spinner("جاري قراءة ملف PDF..."):
        reader = pypdf.PdfReader(uploaded_file)
        num_pages = len(reader.pages)
        st.success(f"تمت قراءة الكتاب! يحتوي على {num_pages} صفحة.")
        
        st.write("---")
        st.subheader("حدد نطاق الصفحات المراد قراءتها:")
        col1, col2 = st.columns(2)
        with col1:
            page_start = st.number_input("من الصفحة:", min_value=1, max_value=num_pages, value=1)
        with col2:
            page_end = st.number_input("إلى الصفحة:", min_value=page_start, max_value=num_pages, value=min(page_start + 2, num_pages))
        
        full_text = ""
        for i in range(page_start - 1, page_end):
            page_text = reader.pages[i].extract_text()
            if page_text:
                full_text += page_text + "\n"
    
    if full_text.strip():
        st.subheader("معاينة النص:")
        st.text_area("النص الحالي جاهز للقراءة:", full_text[:1500] + ("..." if len(full_text) > 1500 else ""), height=200)
        
        if st.button("ابدأ القراءة الصوتية 🎧"):
            with st.spinner("جاري توليد الصوت... يرجى الانتظار."):
                output_audio = "audiobook.mp3"
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_speech(full_text, selected_voice, output_audio))
                    
                    st.audio(output_audio, format="audio/mp3")
                    
                    with open(output_audio, "rb") as file:
                        st.download_button(label="تحميل الملف الصوتي MP3", data=file, file_name="arabic_audiobook.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء معالجة الصوت: {e}")
    else:
        st.error("لم نتمكن من استخراج نصوص مقروءة من هذه الصفحات.")
