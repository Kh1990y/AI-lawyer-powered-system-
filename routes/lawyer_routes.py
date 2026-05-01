# ══════════════════════════════════════════════════════════
# Lawyer Routes - Dashboard, Accept Cases, Archived Cases
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, jsonify, session, request
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db
from firebase_admin import firestore

bp = Blueprint('lawyer', __name__)

@bp.route('/lawyer_dashboard')
@login_required
@role_required('Lawyer')
def lawyer_dashboard():
    """
    لوحة تحكم المحامي - تشمل الطلبات، الجلسات النشطة، والسجلات السابقة
    """
    db = get_db()
    uid = session['user_id']
    
    # 1. الطلبات المعلقة الجديدة
    pending_docs = db.collection('Requests')\
        .where('lawyerID', '==', uid)\
        .where('status', '==', 'Pending')\
        .stream()
    pending = [d.to_dict() | {'id': d.id} for d in pending_docs]
    
    # 2. الجلسات النشطة (محادثات جارية)
    active_docs = db.collection('ChatSessions')\
        .where('lawyerID', '==', uid)\
        .where('status', '==', 'Active')\
        .stream()
    active = [d.to_dict() | {'id': d.id} for d in active_docs]

    # 3. الجلسات السابقة (أرشيف الاستشارات المنتهية) - ميزة المراجعة
    closed_docs = db.collection('ChatSessions')\
        .where('lawyerID', '==', uid)\
        .where('status', '==', 'Closed')\
        .stream()
    closed_archived = [d.to_dict() | {'id': d.id} for d in closed_docs]
    
    return render_template(
        'lawyer_dashboard.html',
        pending=pending,
        active=active,
        closed_archived=closed_archived
    )

@bp.route('/accept_case/<request_id>', methods=['POST'])
@login_required
@role_required('Lawyer')
def accept_case(request_id):
    """
    قبول طلب استشارة وفتح جلسة دردشة فورية
    """
    db = get_db()
    
    # الحصول على بيانات الطلب
    req_ref = db.collection('Requests').document(request_id)
    req_doc = req_ref.get()
    
    if not req_doc.exists:
        return jsonify({"success": False, "msg": "الطلب غير موجود"}), 404
    
    req_data = req_doc.to_dict()
    
    # تحديث حالة الطلب إلى مقبول
    req_ref.update({"status": "Accepted"})
    
    # إنشاء جلسة دردشة جديدة وربطها بالطلب
    session_data = {
        "clientID": req_data['clientID'],
        "clientName": req_data['clientName'],
        "lawyerID": session['user_id'],
        "lawyerName": session['name'],
        "caseType": req_data['caseType'],
        "status": "Active",
        "createdAt": firestore.SERVER_TIMESTAMP,
        "requestID": request_id
    }
    
    _, session_ref = db.collection('ChatSessions').add(session_data)
    
    return jsonify({
        "success": True,
        "sessionID": session_ref.id
    })