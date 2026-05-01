# ══════════════════════════════════════════════════════════
# Firebase Configuration & Initialization
# ══════════════════════════════════════════════════════════

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# Global variables
db = None
bucket = None

def init_firebase():
    """
    تهيئة Firebase Admin SDK
    """
    global db, bucket
    
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        
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