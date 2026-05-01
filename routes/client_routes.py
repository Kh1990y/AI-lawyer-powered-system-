# ══════════════════════════════════════════════════════════
# Client Routes - Client Home, Submit Case, AI Chat
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db
from config.settings import SAUDI_LAWS_MAP
from services.ai_service import ask_ai_stream
from firebase_admin import firestore

bp = Blueprint('client', __name__)

@bp.route('/client_home')
@login_required
# تم إزالة @role_required('Client') من هنا لكي نسمح للمحامي المعلق بالدخول
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
    
    # 1. جلب طلبات العميل (بانتظار قبول المحامي)
    requests_docs = db.collection('Requests')\
        .where('clientID', '==', uid)\
        .where('status', '==', 'Pending')\
        .stream()
    requests_list = [d.to_dict() | {'id': d.id} for d in requests_docs]
    
    # 2. جلب الجلسات النشطة (دردشة جارية)
    active_chats_docs = db.collection('ChatSessions')\
        .where('clientID', '==', uid)\
        .where('status', '==', 'Active')\
        .stream()
    active_chats = [d.to_dict() | {'id': d.id} for d in active_chats_docs]

    # 3. جلب الجلسات السابقة (المؤرشفة/المغلقة) - ميزة المراجعة
    closed_chats_docs = db.collection('ChatSessions')\
        .where('clientID', '==', uid)\
        .where('status', '==', 'Closed')\
        .stream()
    closed_chats = [d.to_dict() | {'id': d.id} for d in closed_chats_docs]
    
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
        library=library
    )

@bp.route('/submit_case', methods=['POST'])
@login_required
def submit_case():
    """
    إرسال طلب استشارة لمحامي
    """
    # منع المحامي المعلق من رفع طلب استشارة (حماية في الباك إند أيضاً)
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