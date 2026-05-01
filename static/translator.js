// 1. إنشاء العنصر المخفي الخاص بجوجل
const googleDiv = document.createElement('div');
googleDiv.id = 'google_translate_element';
document.body.appendChild(googleDiv);

// 2. دالة التهيئة (تم تحديد اللغات الأربع فقط لتسريع الترجمة)
window.googleTranslateElementInit = function() {
    new google.translate.TranslateElement({
        pageLanguage: 'ar',
        includedLanguages: 'ar,en,es,fr', // حصر اللغات هنا يسرع الأداء
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
    }, 'google_translate_element');
};

// 3. استدعاء سكريبت جوجل
const googleScript = document.createElement('script');
googleScript.type = 'text/javascript';
googleScript.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
document.head.appendChild(googleScript);

// 4. الدالة المسؤولة عن تغيير اللغة (محدثة لتعمل على جميع المتصفحات)
window.translatePage = function(languageCode) {
    var googleSelect = document.querySelector('select.goog-te-combo');

    if (googleSelect) {
        googleSelect.value = languageCode;
        // خاصية bubbles: true تضمن أن جوجل يلتقط أمر التغيير
        googleSelect.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
        // في حال ضغط المستخدم بسرعة قبل أن تحمل أداة جوجل في الخلفية
        console.warn("أداة الترجمة لا تزال قيد التحميل...");
        setTimeout(() => { translatePage(languageCode); }, 500); // إعادة المحاولة بعد نصف ثانية
    }
};