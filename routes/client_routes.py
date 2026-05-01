# ══════════════════════════════════════════════════════════
# Client Routes - Client Home, Submit Case, AI Chat, Profile & Admin Chat
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db
from config.settings import SAUDI_LAWS_MAP
from services.ai_service import ask_ai_stream
from firebase_admin import firestore
import datetime

bp = Blueprint('client', __name__)

@bp.route('/client_home')
@login_required
def client_home():
    """
    الصفحة الرئيسية للعميل - تشمل الطلبات، الجلسات النشطة، والأرشيف
    """
    # ─── الحماية الذكية (توجيه المحامي النشط والأدمن لخارج صفحة العميل) ───
    role = session.get('role')
    status = session.get('status')
    
    if role == 'Admin':
        return redirect(url_for('admin.admin_panel'))
    elif role == 'Lawyer' and status == 'active':
        return redirect(url_for('lawyer.lawyer_dashboard'))
    # ───────────────────────────────────────────────────────────

    db = get_db()
    uid = session['user_id']
    
    # 1. جلب طلبات العميل (المعلقة والمقبولة التي لم تنتهِ بعد)
    requests_docs = db.collection('Requests')\
        .where('clientID', '==', uid)\
        .where('status', 'in', ['Pending', 'Accepted'])\
        .stream()
    requests_list = [d.to_dict() | {'id': d.id} for d in requests_docs]
    
    # 2. جلب الجلسات النشطة فقط (المحادثات الجارية حالياً Active)
    # هذا يمنع تكرار الطلبات المنتهية في قائمة النشطة
    active_chats_docs = db.collection('ChatSessions')\
        .where('clientID', '==', uid)\
        .where('status', '==', 'Active')\
        .stream()
    active_chats = [d.to_dict() | {'id': d.id} for d in active_chats_docs]

    # 3. جلب الجلسات السابقة والمؤرشفة فقط (المغلقة Closed والمرفوضة Rejected)
    closed_chats_docs = db.collection('ChatSessions')\
        .where('clientID', '==', uid)\
        .where('status', 'in', ['Closed', 'Rejected'])\
        .stream()
    closed_chats = [d.to_dict() | {'id': d.id} for d in closed_chats_docs]
    
    # جلب الطلبات المرفوضة مباشرة من جدول Requests لعرضها في الأرشيف
    rejected_requests_docs = db.collection('Requests')\
        .where('clientID', '==', uid)\
        .where('status', '==', 'Rejected')\
        .stream()
    rejected_requests = [d.to_dict() | {'id': d.id} for d in rejected_requests_docs]

    # 4. المكتبة القانونية
    library = [
        {"titleAr": k, "fileURL": v} 
        for k, v in SAUDI_LAWS_MAP.items()
    ]
    
    return render_template(
        'client_home.html',
        requests=requests_list,
        active_chats=active_chats,
        closed_chats=closed_chats,
        rejected_requests=rejected_requests,
        library=library
    )

@bp.route('/submit_case', methods=['POST'])
@login_required
def submit_case():
    """
    إرسال طلب استشارة لمحامي
    """
    if session.get('role') == 'Lawyer':
        return jsonify({"success": False, "error": "لا يمكنك طلب استشارة بصفتك مقدم خدمة."}), 403

    db = get_db()
    data = request.get_json()
    
    case_type = data.get('caseType')
    if case_type == 'أخرى':
        case_type = data.get('otherType')
    
    db.collection('Requests').add({
        "clientID": session['user_id'],
        "clientName": session['name'],
        "lawyerID": data.get('lawyerId'),
        "caseType": case_type,
        "description": data.get('description'),
        "status": "Pending",
        "createdAt": firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({"success": True})

@bp.route('/api/get_lawyers')
@login_required
def get_lawyers():
    """
    الحصول على قائمة المحامين النشطين
    """
    db = get_db()
    lawyers_docs = db.collection('users')\
        .where('userType', '==', 'Lawyer')\
        .where('status', '==', 'active')\
        .stream()
    
    lawyers = [
        {"id": d.id, "name": d.to_dict().get('fullName')} 
        for d in lawyers_docs
    ]
    return jsonify(lawyers)

@bp.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    """
    الاستشارة الذكية مع AI (Streaming)
    """
    data = request.get_json()
    user_question = data.get("question", "")
    if not user_question:
        return jsonify({"error": "السؤال فارغ"}), 400
    
    return Response(
        stream_with_context(ask_ai_stream(user_question)),
        mimetype="text/event-stream"
    )

# ══════════════════════════════════════════════════════════
# الملف الشخصي الفعلي للعميل (Profile API)
# ══════════════════════════════════════════════════════════
@bp.route('/client_profile', methods=['GET'])
@login_required
def client_profile():
    """
    جلب بيانات الملف الشخصي الفعلية للمستخدم من قاعدة البيانات
    """
    db = get_db()
    uid = session.get('user_id')
    
    try:
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            return jsonify({"success": False, "msg": "المستخدم غير موجود"}), 404
            
        user_data = user_doc.to_dict()
        profile_info = {
            "fullName": user_data.get('fullName', session.get('name')),
            "email": user_data.get('email', ''),
            "phone": user_data.get('phone', 'غير متوفر'),
            "userType": user_data.get('userType', 'Client'),
            "createdAt": user_data.get('createdAt', 'غير متوفر'),
            "status": user_data.get('status', 'active')
        }
        return jsonify({"success": True, "profile": profile_info})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


# ══════════════════════════════════════════════════════════
# تواصل العميل مع الإدارة (الدردشة الإدارية للعميل)
# ══════════════════════════════════════════════════════════

@bp.route('/client/admin_chat/history', methods=['GET'])
@login_required
def client_admin_chat_history():
    """
    جلب سجل المحادثة بالكامل بين العميل والإدارة
    """
    db = get_db()
    uid = session.get('user_id')
    try:
        room_id = f"admin_{uid}"
        messages = []
        
        msg_docs = db.collection('admin_chats').document(room_id).collection('messages').order_by('timestamp').stream()
        for doc in msg_docs:
            messages.append(doc.to_dict() | {'id': doc.id})
            
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500


@bp.route('/client/admin_chat/send', methods=['POST'])
@login_required
def client_send_to_admin():
    """
    إرسال رسالة من العميل إلى الإدارة
    """
    db = get_db()
    uid = session.get('user_id')
    name = session.get('name', 'عميل')
    try:
        req_data = request.get_json() or {}
        message_text = req_data.get('message')
        
        if not message_text:
            return jsonify({"success": False, "msg": "الرسالة فارغة"}), 400
            
        room_id = f"admin_{uid}"
        
        message_data = {
            "sender_id": uid,
            "sender_name": name,
            "receiver_id": "Admin",
            "message": message_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # حفظ الرسالة
        db.collection('admin_chats').document(room_id).collection('messages').add(message_data)
        
        # تحديث بيانات الغرفة
        db.collection('admin_chats').document(room_id).set({
            "room_id": room_id,
            "user_id": uid,
            "user_name": name,
            "last_message": message_text,
            "last_update": datetime.datetime.utcnow().isoformat()
        }, merge=True)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500