import streamlit as st
import pdfplumber
import edge_tts
import asyncio
import os
import tempfile
import re

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

st.title("🎙️ قارئ الكتب الذكي (النسخة الاحترافية المحدثة)")
st.info("تم إضافة نظام الفلترة الذكية لإصلاح النصوص العربية المعكوسة والمقلوبة تلقائياً.")

# دالة سحرية لإصلاح النصوص العربية المعكوسة الناتجة عن الـ PDF مع الحفاظ على الإنجليزي
def fix_reversed_arabic(text):
    lines = text.split('\n')
    corrected_lines = []
    for line in lines:
        # التحقق إذا كانت السلسلة تحتوي على حروف عربية
        if re.search(r'[\u0600-\u06FF]', line):
            # إذا كان السطر بالكامل عربي ومعكوس
            if not re.search(r'[a-zA-Z]', line):
                corrected_lines.append(line[::-1].strip())
            else:
                # إذا كان السطر مختلط (عربي وإنجليزي)، نعكس الكلمات العربية فقط ونحافظ على ترتيب الإنجليزي
                words = line.split()
                new_words = []
                for word in reversed(words):
                    if re.search(r'[\u0600-\u06FF]', word):
                        # معالجة الرموز الملتصقة بالكلمات المعكوسة مثل النقاط والأقواس
                        new_words.append(word[::-1])
                    else:
                        new_words.append(word)
                corrected_lines.append(" ".join(new_words))
        else:
            # سطر إنجليزي خالص يترك كما هو
            corrected_lines.append(line)
    return "\n".join(corrected_lines)

# رفع الملف
uploaded_file = st.file_uploader("ارفع كتابك (PDF)", type=["pdf"])

# خيارات التحكم في القائمة الجانبية
st.sidebar.header("⚙️ إعدادات التحكم والصوت")
voices = {
    "سلمى (مصر - هادئ وطبيعي)": "ar-EG-SalmaNeural",
    "فاطمة (الإمارات - واضح واحترافي)": "ar-AE-FatimaNeural",
    "حمد (السعودية - فصيح ووقور)": "ar-SA-HamedNeural"
}
selected_voice = st.sidebar.selectbox("اختر نبرة الصوت المفضل:", list(voices.keys()))
rate = st.sidebar.slider("سرعة القراءة", -50, 50, 0)

# زر تفعيل إصلاح النصوص المعكوسة (مفعل تلقائياً لحل مشكلتك)
fix_text_toggle = st.sidebar.checkbox("تفعيل تكنولوجيا إصلاح النصوص المعكوسة", value=True)

# دالة المعالجة المقسمة لمنع مشكلة الـ 15 ثانية ومهلة الاتصال
async def process_text_to_speech(full_text, voice, rate_str):
    # تقسيم النص إلى أجزاء صغيرة (كل جزء 2500 حرف) لضمان الاستقرار التام وعدم الانقطاع
    chunks = [full_text[i:i+2500] for i in range(0, len(full_text), 2500)]
    combined_audio = b""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, chunk in enumerate(chunks):
        status_text.text(f"جاري معالجة وقراءة الجزء {idx+1} من {len(chunks)}...")
        communicate = edge_tts.Communicate(chunk, voices[voice], rate=f"{rate_str:+}%")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            await communicate.save(tmp.name)
            with open(tmp.name, "rb") as f:
                combined_audio += f.read()
            os.remove(tmp.name)
            
        progress_bar.progress((idx + 1) / len(chunks))
        
    status_text.text("✅ تم الانتهاء من معالجة كافة الأجزاء بنجاح!")
    return combined_audio

if uploaded_file:
    with st.spinner("جاري تحليل محتوى الكتاب واستخراج النصوص..."):
        all_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            pages = pdf.pages
            st.sidebar.success(f"إجمالي صفحات الكتاب: {len(pages)}")
            
            # تحديد نطاق الصفحات
            start_p = st.sidebar.number_input("ابدأ من صفحة رقم:", 1, len(pages), 1)
            end_p = st.sidebar.number_input("إلى صفحة رقم:", start_p, len(pages), min(start_p+3, len(pages)))
            
            for i in range(start_p-1, end_p):
                page_content = pages[i].extract_text()
                if page_content:
                    all_text += page_content + "\n"

    if all_text.strip():
        # تطبيق الإصلاح الذكي إذا كان الخيار مفعلاً
        if fix_text_toggle:
            all_text = fix_visual_arabic(all_text)
            
        st.subheader("📝 النص الجاري تجهيزه للقراءة (بعد الإصلاح التلقائي):")
        st.text_area("معاينة النص المستخرج والمنقح:", all_text, height=250)
        
        if st.button("🔊 ابدأ توليد الكتاب الصوتي الآن"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_data = loop.run_until_complete(process_text_to_speech(all_text, selected_voice, rate))
                
                st.success("✅ تم توليد ملفك الصوتي بنجاح وبأعلى جودة!")
                st.audio(audio_data, format="audio/mp3")
                
                st.download_button("📥 تحميل الكتاب الصوتي الكامل (MP3)", audio_data, "my_audiobook.mp3", "audio/mp3")
            except Exception as e:
                st.error(f"حدث خطأ فني أثناء المعالجة: {str(e)}")
    else:
        st.error("لم نتمكن من استخراج أي نصوص. تأكد من أن ملف الـ PDF يحتوي على نصوص وليس صوراً ممسوحة ضوئيًا.")
