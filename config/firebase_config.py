# ══════════════════════════════════════════════════════════
# Firebase Configuration & Initialization
# ══════════════════════════════════════════════════════════

import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# Global variables
db = None
bucket = None

def init_firebase():
    """
    تهيئة Firebase Admin SDK مع دعم متغيرات البيئة للاستضافة
    """
    global db, bucket
    
    try:
        # ── الجزء الجديد: دعم Render + الجهاز المحلي ──────────────
        firebase_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')

        if firebase_json:
            # إذا كنا على Render (سيقرأ من الـ Environment Variables)
            service_account_info = json.loads(firebase_json)
            cred = credentials.Certificate(service_account_info)
        else:
            # إذا كنا على جهازك المحلي (سيقرأ من ملف الـ JSON مباشرة)
            # تم ترك الجزء القديم هنا ليعمل في جهازك فقط
            cred = credentials.Certificate("ai-lawyer-system-23a63-firebase-adminsdk-fbsvc-6bd1d2ea1b.json")
        # ────────────────────────────────────────────────────────

        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                cred, 
                {'storageBucket': 'ai-lawyer-system-23a63.appspot.com'}
            )
        
        db = firestore.client()
        bucket = storage.bucket()
        
        print("✅ Firebase initialized successfully")
        return db, bucket
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        db = None
        bucket = None
        return None, None

def get_db():
    """الحصول على Firestore client"""
    return db

def get_bucket():
    """الحصول على Storage bucket"""
    return bucket

def get_auth():
    """الحصول على Auth module"""
    return auth