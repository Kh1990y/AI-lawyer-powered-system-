# ══════════════════════════════════════════════════════════
# Law Content Scraper Service - Fixed SSL & Enhanced
#كود جاهز يعمل على الذهاب الى الموقع المحدد  ويستخرج النص المحدد بناء على سوال المستخدم ويرجع الالبيانات
# ══════════════════════════════════════════════════════════
import requests
from bs4 import BeautifulSoup
from config.settings import HEADERS, CACHE_TTL
import time
import urllib3

# إيقاف تحذيرات SSL غير الآمنة لكي لا تظهر في سجلات (Logs) النظام
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cache dictionary
_cache = {}

def fetch_law_content(url: str) -> str:
    """
    جلب محتوى النظام القانوني مع تجاوز مشاكل شهادات SSL
    """
    
    # 1. التحقق من الـ Cache
    if url in _cache:
        cached_data = _cache[url]
        if cached_data.get('timestamp') and \
           (time.time() - cached_data['timestamp']) < CACHE_TTL:
            return cached_data['content']
    
    try:
        # 2. جلب الصفحة مع وضع verify=False لتجاوز خطأ SSL
        # تم رفع الـ timeout لضمان استقرار الاتصال بالمواقع الحكومية
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
        resp.raise_for_status()
        
        # ضبط الترميز للغة العربية
        resp.encoding = resp.apparent_encoding if resp.apparent_encoding else "utf-8"
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 3. تنظيف الصفحة
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()

        # 4. البحث عن المحتوى
        content = soup.find("div", {"id": "lawContent"}) or \
                  soup.find("div", {"class": "content-detail"}) or \
                  soup.find("article") or \
                  soup.find("main") or \
                  soup.body

        if content:
            # استخراج النص وفصل الأسطر بذكاء
            lines = (line.strip() for line in content.get_text(separator="\n").splitlines())
            text_content = "\n".join(line for line in lines if line)[:15000]
            
            # 5. كشف الفشل التقني (إذا كان النص قصيراً جداً)
            if len(text_content) < 400:
                return "⚠️ تنبيه: تم الوصول للموقع ولكن المحتوى لم يظهر (ربما يحتاج JavaScript)."

            # حفظ في الـ Cache
            _cache[url] = {
                'content': text_content,
                'timestamp': time.time()
            }
            
            return text_content
        else:
            return "تعذر العثور على حاوية النص الرئيسية في الصفحة."
            
    except requests.exceptions.SSLError:
        return "خطأ حرج في شهادة SSL للموقع الرسمي، تعذر تأمين الاتصال."
    except requests.Timeout:
        return "انتهت مهلة الاتصال بالموقع (Timeout)."
    except requests.RequestException as e:
        return f"خطأ في الاتصال بالبوابة القانونية: {str(e)}"
    except Exception as e:
        return f"حدث خطأ غير متوقع أثناء سحب البيانات: {str(e)}"


def clear_cache():
    """ مسح الـ Cache """
    global _cache
    _cache.clear()
    return True