# ══════════════════════════════════════════════════════════
# AI Service - Claude 4.6 Integration with Firestore Archiving
# ══════════════════════════════════════════════════════════

import os
import json
import anthropic
from flask import session
from firebase_admin import firestore
from config.settings import SAUDI_LAWS_MAP
from config.firebase_config import get_db
from services.law_scraper import fetch_law_content

# تهيئة Anthropic Client
client_claude = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# استخدام الإصدار الأحدث المتوفر في عام 2026
CURRENT_MODEL = "claude-sonnet-4-6"

def save_consultation(question, answer, sources, user_id, username, user_type):
    """
    حفظ الاستشارة في قاعدة البيانات داخل مجموعة consultations
    """
    try:
        db = get_db()
        if not db:
            print("❌ فشل الاتصال بقاعدة البيانات لحفظ الاستشارة")
            return

        consultation_data = {
            "userId": user_id,
            "username": username,
            "usertype": user_type,
            "question": question,
            "answer": answer,
            "sources": sources,  # مصفوفة تحتوي على الأنظمة والروابط المستخدمة
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        db.collection('consultations').add(consultation_data)
        print(f"✅ تم أرشفة الاستشارة بنجاح للمستخدم: {username}")
        
    except Exception as e:
        print(f"❌ خطأ أثناء حفظ الاستشارة في Firestore: {e}")

def select_relevant_law(user_question: str) -> tuple:
    """
    اختيار النظام القانوني الأنسب للسؤال من بين الـ 56 نظاماً
    """
    law_titles = list(SAUDI_LAWS_MAP.keys())
    
    selection_prompt = (
        f"من بين قائمة الأنظمة التجارية السعودية التالية: {law_titles}، "
        f"اختر النظام الأنسب للإجابة على: '{user_question}'. "
        f"أجب باسم النظام المختار فقط. إذا كان السؤال خارج النطاق القانوني، أجب بكلمة 'خارج النطاق'."
    )
    
    try:
        selection_res = client_claude.messages.create(
            model=CURRENT_MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": selection_prompt}]
        )
        
        selected_law_name = selection_res.content[0].text.strip()
        
        if "خارج النطاق" in selected_law_name:
            return None, None
            
        url = SAUDI_LAWS_MAP.get(selected_law_name, None)
        return selected_law_name, url
        
    except Exception as e:
        print(f"خطأ في اختيار النظام: {e}")
        return None, None


def ask_ai_stream(user_question: str):
    """
    الاستشارة الذكية مع Streaming Response والحفظ التلقائي - متخصص في القانون التجاري
    """
    selected_law_name, url = select_relevant_law(user_question)
    
    # رسالة النظام الصارمة
    system_msg = (
        "أنت مستشار قانوني سعودي متخصص في الأنظمة التجارية فقط. "
        "مهامك وقواعدك:\n"
        "1. الرد يجب أن يكون مباشراً وصريحاً وواضحاً جداً.\n"
        "2. إذا كان السؤال خارج المجال القانوني السعودي، اعتذر عن الإجابة بلباقة.\n"
        "3. اعتمد بشكل أساسي على نص النظام المرفق لك (من الـ 56 رابط).\n"
        "4. إذا لم تجد المعلومة في النص المرفق، ابحث في معرفتك بالأنظمة السعودية الأخرى وأجب باختصار شديد جداً، "
        "مع ذكر عبارة: (هذه المعلومة من خارج البيانات الملقنة لي).\n"
        "5. إذا لم تعرف الرد نهائياً، قل بوضوح: 'لم أعرف الرد'.\n"
        "6. في نهاية كل رسالة، يجب أن تذكر نصاً: 'أنا بوت ذكاء اصطناعي ومعرض للخطأ'.\n"
        "7. اذكر المصادر (اسم النظام والرابط) في نهاية الرد بشكل منظم."
    )

    if not selected_law_name:
        context = "لا يوجد نظام محدد لهذه الاستشارة."
        selected_law_name = "بحث عام في الأنظمة السعودية"
        url = "غير محدد"
    else:
        yield f"data: {json.dumps({'text': f'🔍 جاري تحليل النظام التجاري: {selected_law_name}... ', 'type': 'text'})}\n\n"
        context = fetch_law_content(url)
    
    full_query = (
        f"السؤال: {user_question}\n\n"
        f"النظام المختار: {selected_law_name}\n"
        f"الرابط: {url}\n\n"
        f"نص النظام المتاح من الروابط الـ 56:\n{context}"
    )
    
    full_answer_text = ""
    
    try:
        with client_claude.messages.stream(
            model=CURRENT_MODEL,
            max_tokens=3000,
            system=system_msg,
            messages=[{"role": "user", "content": full_query}]
        ) as stream:
            for text in stream.text_stream:
                full_answer_text += text
                yield f"data: {json.dumps({'text': text, 'type': 'text'})}\n\n"
        
        # حفظ الاستشارة بعد اكتمال الـ Streaming
        save_consultation(
            question=user_question,
            answer=full_answer_text,
            sources=[selected_law_name, url],
            user_id=session.get('user_id'),
            username=session.get('name'),
            user_type=session.get('role')
        )
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        error_msg = f"❌ حدث خطأ في الاتصال : {str(e)}"
        yield f"data: {json.dumps({'text': error_msg, 'type': 'error'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"


def ask_ai_simple(user_question: str) -> str:
    """
    استشارة بسيطة بدون streaming مع الحفظ في قاعدة البيانات - متخصص في القانون التجاري
    """
    selected_law_name, url = select_relevant_law(user_question)
    
    system_msg = (
        "أنت مستشار قانوني سعودي متخصص في الأنظمة التجارية فقط. "
        "ردك مباشر وصريح. إذا لم تجد المعلومة في النص المرفق، أجب باختصار من مصادرك الخارجية مع ذكر (هذه المعلومة من خارج البيانات الملقنة لي). "
        "إذا لم تعرف الرد قل: 'لم أعرف الرد'. "
        "في النهاية اذكر: 'أنا بوت ذكاء اصطناعي ومعرض للخطأ' واذكر المصادر المستخدمة."
    )
    
    if selected_law_name:
        context = fetch_law_content(url)
    else:
        context = "بحث خارج النطاق المباشر"
        selected_law_name = "عام"
        url = "غير متوفر"

    full_query = (
        f"السؤال: {user_question}\n\n"
        f"النظام: {selected_law_name}\n"
        f"المحتوى:\n{context}"
    )
    
    try:
        response = client_claude.messages.create(
            model=CURRENT_MODEL,
            max_tokens=2000,
            system=system_msg,
            messages=[{"role": "user", "content": full_query}]
        )
        
        answer_text = response.content[0].text
        
        # حفظ الاستشارة
        save_consultation(
            question=user_question,
            answer=answer_text,
            sources=[selected_law_name, url],
            user_id=session.get('user_id'),
            username=session.get('name'),
            user_type=session.get('role')
        )
        
        return answer_text
        
    except Exception as e:
        return f"خطأ: {str(e)}"