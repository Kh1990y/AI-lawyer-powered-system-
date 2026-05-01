# ══════════════════════════════════════════════════════════
# Admin Routes - Admin Panel, User Management & Admin Chat
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, jsonify, request
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db, get_auth
from config.settings import SAUDI_LAWS_MAP
from datetime import datetime

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
    all_users = [u.to_dict() | {'id': u.id} for u in db.collection('users').stream()]
    
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
            "status": "active",
            "updatedAt": datetime.utcnow().isoformat()
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
            "status": "rejected",
            "updatedAt": datetime.utcnow().isoformat()
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/delete_user/<uid>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_user(uid):
    """
    حذف مستخدم نهائياً وتعليق حسابه لحظياً
    """
    db = get_db()
    auth = get_auth()
    
    try:
        # نقوم أولاً بتحديث حالته في الداتا بيز إلى deleted ليتم إخراجه فوراً بالريفريش الذكي
        db.collection('users').document(uid).update({
            "status": "deleted",
            "deletedAt": datetime.utcnow().isoformat()
        })
        
        # حذف من Firebase Auth
        auth.delete_user(uid)
        
        # حذف من Firestore نهائياً
        db.collection('users').document(uid).delete()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


# ══════════════════════════════════════════════════════════
# التحديث الذكي: مسار تعليق المستخدم (Suspend User)
# ══════════════════════════════════════════════════════════
@bp.route('/admin/suspend_user/<uid>', methods=['POST'])
@login_required
@role_required('Admin')
def suspend_user(uid):
    """
    تعليق حساب مستخدم مؤقتاً
    """
    db = get_db()
    try:
        db.collection('users').document(uid).update({
            "status": "suspended",
            "updatedAt": datetime.utcnow().isoformat()
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


# ══════════════════════════════════════════════════════════
# الدردشة الإدارية: إدارة المراسلات مع العملاء والمحامين
# ══════════════════════════════════════════════════════════

@bp.route('/admin/chat/list_rooms', methods=['GET'])
@login_required
@role_required('Admin')
def list_admin_chat_rooms():
    """
    جلب غرف المحادثة الخاصة بالإدارة مع المستخدمين
    """
    db = get_db()
    try:
        rooms = []
        # جلب غرف الدردشة التي تحتوي على الإدارة كطرف أساسي
        chat_docs = db.collection('admin_chats').stream()
        for doc in chat_docs:
            data = doc.to_dict()
            rooms.append(data | {'id': doc.id})
        return jsonify({"success": True, "rooms": rooms})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/admin/chat/send', methods=['POST'])
@login_required
@role_required('Admin')
def admin_send_message():
    """
    إرسال رسالة من الإدارة إلى العميل أو المحامي
    """
    db = get_db()
    try:
        req_data = request.get_json() or {}
        receiver_id = req_data.get('receiver_id')
        message_text = req_data.get('message')
        
        if not receiver_id or not message_text:
            return jsonify({"success": False, "msg": "Missing receiver_id or message"}), 400
            
        # تحديد اسم الغرفة الفريد
        room_id = f"admin_{receiver_id}"
        
        # رسالة جديدة
        message_data = {
            "sender_id": "Admin",
            "sender_name": "الإدارة",
            "receiver_id": receiver_id,
            "message": message_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # إضافة الرسالة في الـ Sub-collection
        db.collection('admin_chats').document(room_id).collection('messages').add(message_data)
        
        # تحديث بيانات الغرفة العامة للترتيب والمتابعة
        db.collection('admin_chats').document(room_id).set({
            "room_id": room_id,
            "user_id": receiver_id,
            "last_message": message_text,
            "last_update": datetime.utcnow().isoformat()
        }, merge=True)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/admin/chat/history/<user_id>', methods=['GET'])
@login_required
@role_required('Admin')
def admin_chat_history(user_id):
    """
    جلب سجل المحادثة الكامل بين الإدارة ومستخدم معين
    """
    db = get_db()
    try:
        room_id = f"admin_{user_id}"
        messages = []
        
        msg_docs = db.collection('admin_chats').document(room_id).collection('messages').order_by('timestamp').stream()
        for doc in msg_docs:
            messages.append(doc.to_dict() | {'id': doc.id})
            
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500