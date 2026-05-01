# ══════════════════════════════════════════════════════════
# Authentication & Authorization Middleware
# ══════════════════════════════════════════════════════════

import functools
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Decorator للتأكد من تسجيل دخول المستخدم
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("⚠️ يرجى تسجيل الدخول أولاً")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """
    Decorator للتحقق من صلاحية المستخدم
    
    Args:
        role (str): الدور المطلوب (Admin, Lawyer, Client)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash(f"🚫 لا تملك صلاحية الدخول لهذه الصفحة (مطلوب: {role})")
                
                # إعادة توجيه حسب الدور الحالي
                current_role = session.get('role')
                if current_role == 'Admin':
                    return redirect(url_for('admin.admin_panel'))
                elif current_role == 'Lawyer':
                    return redirect(url_for('lawyer.lawyer_dashboard'))
                else:
                    return redirect(url_for('client.client_home'))
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator