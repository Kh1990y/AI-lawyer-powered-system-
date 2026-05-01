# ══════════════════════════════════════════════════════════
# نظام المحامي الذكي - الملف الرئيسي
# AI Lawyer System - Main Application
# ══════════════════════════════════════════════════════════

from flask import Flask, redirect, url_for, session
from config.settings import SECRET_KEY
from config.firebase_config import init_firebase

# ── تهيئة Flask ────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── تهيئة Firebase ────────────────────────────────────────
init_firebase()

# ── تسجيل Blueprints ──────────────────────────────────────
from routes import auth_routes, client_routes, lawyer_routes, admin_routes, chat_routes

app.register_blueprint(auth_routes.bp)
app.register_blueprint(client_routes.bp)
app.register_blueprint(lawyer_routes.bp)
app.register_blueprint(admin_routes.bp)
app.register_blueprint(chat_routes.bp)

# ══════════════════════════════════════════════════════════
# الصفحة الرئيسية - إعادة توجيه حسب الدور
# ══════════════════════════════════════════════════════════

@app.route('/')
def index():
    """
    إعادة توجيه المستخدم حسب دوره وحالته
    """
    if 'user_id' in session:
        role = session.get('role')
        status = session.get('status', 'active') # جلب الحالة، وافتراض أنها نشطة إن لم تكن موجودة
        
        if role == 'Admin':
            return redirect(url_for('admin.admin_panel'))
        
        # توجيه المحامي إلى لوحته فقط إذا كان حسابه مفعلاً
        elif role == 'Lawyer' and status == 'active':
            return redirect(url_for('lawyer.lawyer_dashboard'))
        
        # توجيه العميل، وأيضاً المحامي المعلق (pending_approval) إلى لوحة العميل
        else:
            return redirect(url_for('client.client_home'))
    
    return redirect(url_for('auth.login'))


# ══════════════════════════════════════════════════════════
# تشغيل التطبيق
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 تشغيل نظام المحامي الذكي")
    print("=" * 60)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )