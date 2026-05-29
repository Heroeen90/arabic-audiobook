import streamlit as st
import pdfplumber
import edge_tts
import asyncio
import os
import tempfile

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="AudioBook Pro AI", page_icon="🎙️", layout="wide")

# تصميم الواجهة بألوان متناسقة لتسهيل القراءة من الهاتف
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #38bdf8; color: black; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #38bdf8; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎙️ قارئ الكتب الذكي (النسخة الاحترافية)")
st.info("هذه النسخة تدعم الكتب الطويلة وتستخدم محرك معالجة متقدم لضمان عدم انقطاع الصوت.")

# رفع الملف
uploaded_file = st.file_uploader("ارفع كتابك (PDF)", type=["pdf"])

# خيارات الصوت في القائمة الجانبية
voices = {
    "سلمى (مصر - هادئ وطبيعي)": "ar-EG-SalmaNeural",
    "فاطمة (الإمارات - واضح واحترافي)": "ar-AE-FatimaNeural",
    "حمد (السعودية - فصيح ووقور)": "ar-SA-HamedNeural"
}
selected_voice = st.sidebar.selectbox("اختر نبرة الصوت المفضل:", list(voices.keys()))
rate = st.sidebar.slider("سرعة القراءة", -50, 50, 0)

# دالة المعالجة المقسمة لمنع مشكلة الـ 15 ثانية ومهلة الاتصال
async def process_text_to_speech(full_text, voice, rate_str):
    # تقسيم النص إلى أجزاء (كل جزء 3000 حرف تقريباً) لضمان الاستقرار الكامل
    chunks = [full_text[i:i+3000] for i in range(0, len(full_text), 3000)]
    combined_audio = b""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, chunk in enumerate(chunks):
        status_text.text(f"جاري معالجة وقراءة الجزء {idx+1} من {len(chunks)}...")
        communicate = edge_tts.Communicate(chunk, voices[voice], rate=f"{rate_str:+}%")
        
        # استخدام ملف مؤقت بشكل آمن لكل جزء صفتي
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            await communicate.save(tmp.name)
            with open(tmp.name, "rb") as f:
                combined_audio += f.read()
            os.remove(tmp.name)
            
        progress_bar.progress((idx + 1) / len(chunks))
        
    status_text.text("✅ تم الانتهاء من معالجة كافة الأجزاء!")
    return combined_audio

if uploaded_file:
    with st.spinner("جاري تحليل محتوى الكتاب واستخراج النصوص العربية بدقة..."):
        all_text = ""
        # استخدام pdfplumber للحصول على أفضل دقة قراءة للغة العربية والتشكيل
        with pdfplumber.open(uploaded_file) as pdf:
            pages = pdf.pages
            st.sidebar.success(f"إجمالي صفحات الكتاب: {len(pages)}")
            
            # تحديد نطاق الصفحات المراد قراءتها لتوفير الموارد
            start_p = st.sidebar.number_input("ابدأ من صفحة رقم:", 1, len(pages), 1)
            end_p = st.sidebar.number_input("إلى صفحة رقم:", start_p, len(pages), min(start_p+5, len(pages)))
            
            for i in range(start_p-1, end_p):
                page_content = pages[i].extract_text()
                if page_content:
                    all_text += page_content + "\n"

    if all_text.strip():
        st.subheader("📝 النص الجاري تجهيزه للقراءة:")
        st.text_area("معاينة النص المستخرج:", all_text, height=250)
        
        if st.button("🔊 ابدأ توليد الكتاب الصوتي الآن"):
            try:
                # إدارة حلقة الأحداث (Event Loop) لـ asyncio بأمان داخل سحاب Streamlit
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_data = loop.run_until_complete(process_text_to_speech(all_text, selected_voice, rate))
                
                st.success("✅ تم توليد ملفك الصوتي بنجاح وبأعلى جودة!")
                st.audio(audio_data, format="audio/mp3")
                
                st.download_button("📥 تحميل الكتاب الصوتي الكامل (MP3)", audio_data, "my_audiobook.mp3", "audio/mp3")
            except Exception as e:
                st.error(f"حدث خطأ فني أثناء المعالجة: {str(e)}")
    else:
        st.error("لم نتمكن من استخراج أي نصوص من الصفحات المحددة. تأكد من أن ملف الـ PDF يحتوي على نصوص رقمية وليس مجرد صور ممسوحة ضوئيًا (Scanner).")
