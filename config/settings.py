# ══════════════════════════════════════════════════════════
# إعدادات النظام العامة
# ══════════════════════════════════════════════════════════

import os
from dotenv import load_dotenv

load_dotenv()

# ── Flask Configuration ───────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "lawyer_ultra_secret_2026")

# ── Cache Configuration ───────────────────────────────────
CACHE_TTL = 3600 * 6  # 6 hours

# ── Web Scraping Headers ──────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ar"
}

# ══════════════════════════════════════════════════════════
# قائمة الأنظمة السعودية الـ 56 المحدثة
# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# خارطة الأنظمة السعودية المحدثة - (تحديث أبريل 2026)

#لازم نعيد التاكد من صحة الروابط مع المسمى الامامي لها 
# ══════════════════════════════════════════════════════════


SAUDI_LAWS_MAP = {
    # --- الأنظمة التجارية والاستثمارية ---
    "نظام الوكالات التجارية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b19a8aa6-7b50-43f0-ab8c-a9a700f1a446/1",
    "نظام صندوق الاستثمارات العامة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/2541255e-9e5b-4393-a8b0-a9a700f1a596/1",
    "نظام محلات بيع المركبات الملغى تسجيلها": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/cf510039-d022-42                                                              1f-9901-a9a700f1a8a0/1",
    "نظام البيانات التجارية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/95a6369d-d712-4028-842e-a9a700f1a957/1",
    "نظام العلامات التجارية ": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/3ec4414f-2ec5-48b1-bcb4-a9a700f1aa2b/1",
    "نظام الهيئة السعودية للمهندسين": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/3e1de77d-3cd1-44d8-b174                                                                                                                                                                                                                                             -a9a700f1ab06/1",
    "نظام السوق المالية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/50924f95-f74e-430e-820c-a9a700f1abfa/1",
    "نظام مراقبة شركات التأمين التعاوني": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/3e3c6fc3-9a45-4a0e-b28e-a9a700f1ad14/1",
    "نظام الرهن التجاري": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/7b6436fd-e7c0-4a51-afcc-a9a700f1ae15/1",
    "نظام المنافسة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/6b615a05-f637-41cf-8419-a9a700f1afd7/1",
    "نظام المشاركة بالوقت فى الوحدات العقارية السياحية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/3ab82e3c-de46-4463-a939-a9a700f1b2af/1",
    "نظام الأوراق التجارية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/4763eb94-047b-46f1-9697-a9a700f1b7ed/1",
    "نظام الصندوق السعودي للتنمية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/7017dc70-15bb-4137-b87d-a9a700f1b950/1",

    # --- الأنظمة القضائية والعدلية ---
    "نظام الدفاتر التجارية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/05690bd6-2c75-4b65-a148-a9a700f1bccf/1",
    "نظام المحاسبين القانونيين": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/56195fdf-46c2-44f0-88e5-a9a700f1be50/1",
    "النظام الأساسي لهيئة المحاسبة والمراجعة لدول مجلس التعاون": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/109578cc-5c5c-42a9-9bae-a9a700f1c2a8/1",
    "نظام براءات الاختراع لدول مجلس التعاون لدول الخليج العربية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/f95138ff-0892-49b0-921c-a9a700f1c37f/1",
    "نظام براءات الاختراع والتصميمات التخطيطية للدارات المتكاملة والأصناف النباتية والنماذج الصناعية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/6cfde53b-e803-49be-b2c6-a9a700f1c434/1",
    "النظام الأساسي لهيئة التقييس لدول مجلس التعاون لدول الخليج العربية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/746f3ff2-0c3a-4b60-aac2-a9a700f1c4e8/1",
    "القانون النظام الموحد لمكافحة الإغراق والتدابير التعويضية والوقائية لدول مجلس التعاون لدول الخليج العربية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/0da0543b-72bf-4405-98f3-a9a700f1c593/1",
    "نظام استيراد المواد الكيميائية وإدارتها ( نظام إدارة المواد الكيميائية )": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/64aee787-4618-4979-b4d8-a9a700f1c647/1",
    "النظام التجاري ( نظام المحكمة التجارية)": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/c58ba10c-4e89-4c06-98d7-a9a700f1c706/1",

    # --- أنظمة العمل والضمان ---
    "نظام المقيمين المعتمدين": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/cad66e4d-38d3-4baa-8049-a9a700f1e7a8/1",
    "النظام الأساسي للمركز الإحصائي لدول مجلس التعاون لدول الخليج العربية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/d93b5ced-1adb-494d-85fd-a9a700f1e817/1",
    "قانون (نظام) العلامات التجارية لدول مجلس التعاون لدول الخليج العربية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b2d0decd-a691-45b9-9af0-a9a700f1e86f/1",
    "نظام مزاولة المهن الهندسية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/ebb751a1-6f0b-4595-9736-a9a700f1f47b/1",
    "نظام ضريبة القيمة المضافة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/f98f4238-0289-4891-8a22-a9a700f1f538/1",

    # --- الأنظمة الضريبية والزكوية ---
    "نظام جباية الزكاة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/737705df-17ad-42b0-9094-a9a700f1bb61/1",
    "نظام الإفلاس": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/68204119-84f1-4789-8fad-a9ec014c3788/1",
    "نظام صندوق الاستثمارات العامة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/52da052e-9de3-4ead-abbf-aa3f00ef5083/1",
    "نظام المنافسة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/e3605c0d-ef87-4cff-b5da-aa3f0102bbb4/1",

    # --- الأنظمة العقارية ---
    "نظام التجارة الإلكترونية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/360de590-0286-4fa5-a243-aa9100c31979/1",
    "نظام المنافسات و المشتريات الحكومية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/24c563f9-7292-49c8-b0fb-aa9800b999f1/1",
    "نظام الرهن التجاري": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/e7bd6fcc-c29c-4696-8032-aae9009b113a/1",
    "نظام الامتياز التجاري": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/af2a6b93-51dd-4f16-b781-aafd00d9fbbc/1",
    "نظام ضمان الحقوق بالأموال المنقولة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/e2c00ba7-2af3-41fa-a1ab-ab9f00af1dec/1",

    # --- التقنية والبيانات والملكية الفكرية ---
    "نظام مكافحة التستر": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/bf9e0aae-6df6-4785-a305-ac2300bd0856/1",
    "نظام مكافحة الغش التجاري": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/85eb2897-bec6-4c0c-b1d7-ac7c008ec09c/1",
    "نظام الغرف التجارية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/fb3e69e4-84a6-45b4-85d6-ac8c00cb3d67/1",
    "نظام معالجة المنشآت المالية المهمة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/82b804f6-0075-47c2-a772-acc4002f8b3e/1",
    "نظام مهنة المحاسبة والمراجعة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/6435e205-a7ae-4a8c-9580-ad0000b6bef2/1",
    "نظام التخصيص": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/8af67ec1-6776-4f67-abb4-ad0900eadf2f/1",

    # --- البيئة، الطاقة، والموارد ---
    "نظام المعالجات التجارية في التجارة الدولية": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/319fe343-cafd-4638-bc7d-af5e00b16b6b/1",
    "نظام سلامة المنتجات": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/7f147afb-5a81-4744-a4bf-b1cd00b831ea/1",
    "نظام الاستثمار": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/eda86cc3-3a00-4b90-900d-b1d000c8a863/1",
    "نظام السجل التجاري": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/98ee4b51-d398-4323-ae69-b2b8009f3156/1",
    "نظام الإحصاء": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b4edc050-18f3-4b23-aabc-b35b00ddaab7/1",

    # --- أنظمة عامة ---
    "نظام صندوق الاستثمارات العامة": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b6c66cda-7f2c-408d-94b7-b3d300dbffe8/1",
    "نظام الشركات": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/a8376aea-1bc3-49d4-9027-aed900b555af/1",
    "نظام تصنيف المقاولين": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/66eccea3-fc1c-471f-bcfa-ad9d009a7ec0/1",
}