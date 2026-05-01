# ══════════════════════════════════════════════════════════
# Authentication Routes - Login, Register, Logout
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.firebase_config import get_db, get_auth
from firebase_admin import firestore

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    تسجيل مستخدم جديد (عميل أو محامي)
    """
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        role = request.form.get('role')
        phone = request.form.get('phone', '')
        
        try:
            auth = get_auth()
            db = get_db()
            
            # إنشاء المستخدم في Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=fullname
            )
            
            # تحديد الحالة (المحامون يحتاجون موافقة)
            status = "pending_approval" if role == "Lawyer" else "active"
            
            # حفظ البيانات في Firestore (مع حفظ الباسورد للتحقق منه وقت الدخول)
            db.collection('users').document(user.uid).set({
                "uid": user.uid,
                "fullName": fullname,
                "email": email,
                "phone": phone,
                "userType": role,
                "status": status,
                "password": password, # تمت الإضافة هنا
                "createdAt": firestore.SERVER_TIMESTAMP
            })
            
            # رسالة مخصصة بناءً على الدور
            if role == "Lawyer":
                flash("✅ تم إرسال طلبك بنجاح. يمكنك الآن الدخول باستخدام بريدك الإلكتروني وسيتم توجيهك مؤقتاً كعميل حتى تتم مراجعة طلبك.")
            else:
                flash("✅ تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن.")
                
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f"❌ خطأ في التسجيل: {str(e)}")
    
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    تسجيل الدخول باستخدام البريد الإلكتروني وكلمة المرور
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        
        # البحث عن المستخدم في Firestore بواسطة البريد الإلكتروني
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).get()
        
        if len(query) > 0:
            user_doc = query[0]
            user_data = user_doc.to_dict()
            
            # التحقق من صحة كلمة المرور
            if user_data.get('password') == password:
                
                # مسح الجلسة السابقة
                session.clear()
                
                # إنشاء جلسة جديدة ببيانات المستخدم
                session['user_id'] = user_data.get('uid')
                session['role'] = user_data.get('userType')
                session['name'] = user_data.get('fullName')
                
                # الأهم: حفظ حالة الحساب (نشط أم معلق) لتعمل ميزة "الحالة المزدوجة"
                session['status'] = user_data.get('status', 'active')
                
                # توجيه المستخدم للملف الرئيسي `app.py` وهو سيقوم بتوزيعه حسب دوره وحالته
                return redirect(url_for('index'))
            else:
                flash("❌ كلمة المرور غير صحيحة!")
        else:
            flash("❌ البريد الإلكتروني غير مسجل في النظام!")
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    """
    تسجيل الخروج
    """
    session.clear()
    flash("✅ تم تسجيل الخروج بنجاح")
    return redirect(url_for('auth.login'))