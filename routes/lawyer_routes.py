# ══════════════════════════════════════════════════════════
# Lawyer Routes - Dashboard, Accept Cases, Archived Cases
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, jsonify, session, request
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db
from firebase_admin import firestore
from config.settings import SAUDI_LAWS_MAP  # إضافة استدعاء المكتبة القانونية

bp = Blueprint('lawyer', __name__)

@bp.route('/lawyer_dashboard')
@login_required
@role_required('Lawyer')
def lawyer_dashboard():
    """
    لوحة تحكم المحامي - تشمل الطلبات، الجلسات النشطة، والسجلات السابقة والمكتبة
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

    # 3. الجلسات السابقة (أرشيف الاستشارات المنتهية)
    closed_docs = db.collection('ChatSessions')\
        .where('lawyerID', '==', uid)\
        .where('status', '==', 'Closed')\
        .stream()
    closed_archived = [d.to_dict() | {'id': d.id} for d in closed_docs]

    # جلب الطلبات المرفوضة والمؤرشفة لعرضها في الأرشيف
    rejected_docs = db.collection('Requests')\
        .where('lawyerID', '==', uid)\
        .where('status', '==', 'Rejected')\
        .stream()
    rejected_requests = [d.to_dict() | {'id': d.id} for d in rejected_docs]
    
    # 4. جلب المكتبة القانونية وتمريرها للواجهة (الـ 56 نظام)
    library = [
        {"titleAr": k, "fileURL": v} 
        for k, v in SAUDI_LAWS_MAP.items()
    ]
    
    return render_template(
        'lawyer_dashboard.html',
        pending=pending,
        active=active,
        closed_archived=closed_archived,
        rejected_requests=rejected_requests,
        library=library
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
        "description": req_data.get('description', ''),
        "status": "Active",
        "createdAt": firestore.SERVER_TIMESTAMP,
        "requestID": request_id
    }
    
    _, session_ref = db.collection('ChatSessions').add(session_data)
    
    return jsonify({
        "success": True,
        "sessionID": session_ref.id
    })

@bp.route('/reject_case/<request_id>', methods=['POST'])
@login_required
@role_required('Lawyer')
def reject_case(request_id):
    """
    رفض طلب الاستشارة ونقله للأرشيف مباشرة
    """
    db = get_db()
    
    try:
        req_ref = db.collection('Requests').document(request_id)
        req_doc = req_ref.get()
        
        if not req_doc.exists:
            return jsonify({"success": False, "msg": "الطلب غير موجود"}), 404
            
        # تحديث الحالة إلى Rejected لنقله فوراً للأرشيف
        req_ref.update({
            "status": "Rejected",
            "rejectedAt": firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@bp.route('/save_lawyer_notes/<request_id>', methods=['POST'])
@login_required
@role_required('Lawyer')
def save_lawyer_notes(request_id):
    """
    إضافة وتعديل الملاحظات الشخصية للمحامي على الطلبات
    """
    db = get_db()
    
    try:
        req_data = request.get_json() or {}
        lawyer_notes = req_data.get('lawyer_notes', '')
        
        req_ref = db.collection('Requests').document(request_id)
        req_doc = req_ref.get()
        
        if not req_doc.exists:
            return jsonify({"success": False, "msg": "الطلب غير موجود"}), 404
            
        req_ref.update({
            "lawyer_notes": lawyer_notes,
            "notesUpdatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

# ══════════════════════════════════════════════════════════
# تحديث ذكي: إنهاء الجلسة وإغلاق الطلب (Closed) في قاعدة البيانات
# ══════════════════════════════════════════════════════════
@bp.route('/api/close_session/<session_id>', methods=['POST'])
@login_required
@role_required('Lawyer')
def close_session(session_id):
    """
    إنهاء الجلسة وإغلاق الطلب الأساسي ونقله للأرشيف
    """
    db = get_db()
    try:
        chat_ref = db.collection('ChatSessions').document(session_id)
        chat_doc = chat_ref.get()
        
        if not chat_doc.exists:
            return jsonify({"success": False, "error": "الجلسة غير موجودة"}), 404
            
        chat_data = chat_doc.to_dict()
        
        # 1. تحديث حالة الجلسة إلى Closed
        chat_ref.update({
            "status": "Closed",
            "closedAt": firestore.SERVER_TIMESTAMP
        })
        
        # 2. تحديث حالة الطلب الأساسي المرتبط بها إلى Closed
        request_id = chat_data.get('requestID')
        if request_id:
            db.collection('Requests').document(request_id).update({
                "status": "Closed",
                "closedAt": firestore.SERVER_TIMESTAMP
            })
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500