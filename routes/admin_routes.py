# ══════════════════════════════════════════════════════════
# Admin Routes - Admin Panel, User Management
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, jsonify
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db, get_auth
from config.settings import SAUDI_LAWS_MAP

bp = Blueprint('admin', __name__)

@bp.route('/admin_panel')
@login_required
@role_required('Admin')
def admin_panel():
    """
    لوحة الإدارة 
    """
    db = get_db()
    
    # جلب جميع المستخدمين
    all_users = [u.to_dict() for u in db.collection('users').stream()]
    
    # جلب جميع القضايا
    all_cases = [c.to_dict() | {'id': c.id} for c in db.collection('Requests').stream()]
    
    # إحصائيات
    stats = {
        'total_users': len(all_users),
        'pending_lawyers': len([u for u in all_users if u.get('userType') == 'Lawyer' and u.get('status') == 'pending_approval']),
    }
    
    # المكتبة
    library = [
        {"name": k, "url": v} 
        for k, v in SAUDI_LAWS_MAP.items()
    ]
    
    return render_template(
        'admin_panel.html',
        all_users=all_users,
        all_cases=all_cases,
        stats=stats,
        library=library
    )


@bp.route('/admin/approve_lawyer/<uid>', methods=['POST'])
@login_required
@role_required('Admin')
def approve_lawyer(uid):
    """
    الموافقة على طلب محامي
    """
    db = get_db()
    
    try:
        db.collection('users').document(uid).update({
            "status": "active"
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/admin/reject_lawyer/<uid>', methods=['POST'])
@login_required
@role_required('Admin')
def reject_lawyer(uid):
    """
    رفض طلب محامي
    """
    db = get_db()
    
    try:
        db.collection('users').document(uid).update({
            "status": "rejected"
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/delete_user/<uid>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_user(uid):
    """
    حذف مستخدم نهائياً
    """
    db = get_db()
    auth = get_auth()
    
    try:
        # حذف من Firebase Auth
        auth.delete_user(uid)
        
        # حذف من Firestore
        db.collection('users').document(uid).delete()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

# لازم نسوي خاصية التواصل بين الادارة وباقي المستخدمين