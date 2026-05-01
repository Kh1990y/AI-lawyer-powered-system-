# ══════════════════════════════════════════════════════════
# Chat Routes - Chatting, Message Handling & History Retrieval
# ══════════════════════════════════════════════════════════

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from middleware.auth_middleware import login_required, role_required
from config.firebase_config import get_db
from firebase_admin import firestore
import datetime

bp = Blueprint('chat', __name__)

@bp.route('/chat/<session_id>')
@login_required
def chat_room(session_id):
    db = get_db()
    chat_doc = db.collection('ChatSessions').document(session_id).get()
    
    if not chat_doc.exists:
        return redirect(url_for('client.client_home'))
    
    chat_data = chat_doc.to_dict()
    # التحقق مما إذا كان المستخدم جزءاً من المحادثة (أمان إضافي)
    if session['user_id'] not in [chat_data.get('clientID'), chat_data.get('lawyerID')] and session['role'] != 'Admin':
        return "غير مسموح لك بدخول هذه المحادثة", 403

    return render_template(
        'chat_room.html',
        chat_session=chat_data,
        session_id=session_id
    )

@bp.route('/api/get_messages/<session_id>')
@login_required
def get_messages(session_id):
    db = get_db()
    try:
        # جلب الرسائل بدون order_by لتجنب خطأ Index
        messages_docs = db.collection('messages')\
            .where('sessionID', '==', str(session_id))\
            .stream()
        
        messages = []
        for d in messages_docs:
            msg_data = d.to_dict()
            ts = msg_data.get('timestamp')
            
            # معالجة الوقت للعرض
            if ts:
                try:
                    # إذا كان الكائن Timestamp من فيربيز
                    msg_data['time_display'] = ts.strftime('%I:%M %p')
                except:
                    msg_data['time_display'] = ""
            else:
                msg_data['time_display'] = "الآن"
                
            messages.append(msg_data)
            
        # الترتيب يدوياً بواسطة Python بناءً على التوقيت
        messages.sort(key=lambda x: x.get('timestamp').timestamp() if x.get('timestamp') and hasattr(x.get('timestamp'), 'timestamp') else 0)
            
        return jsonify(messages)
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return jsonify([]), 500

@bp.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    db = get_db()
    try:
        # التحقق من حالة الجلسة قبل الإرسال
        session_id = request.form.get('sessionID')
        chat_ref = db.collection('ChatSessions').document(session_id)
        chat_doc = chat_ref.get()
        
        if chat_doc.exists and chat_doc.to_dict().get('status') in ['Closed', 'Rejected']:
            return jsonify({"success": False, "error": "هذه الجلسة مغلقة أو مؤرشفة ولا يمكن الإرسال"}), 400

        db.collection('messages').add({
            "sessionID": str(session_id),
            "senderID": session['user_id'],
            "senderName": session['name'],
            "text": request.form.get('text'),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/close_session/<session_id>', methods=['POST'])
@login_required
@role_required('Lawyer') # المحامي فقط من ينهي الجلسة
def close_session(session_id):
    """
    إنهاء الجلسة وإغلاق الطلب الأساسي وتغيير حالته إلى Closed
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
        
        # 2. تحديث حالة الطلب الأساسي المرتبط بها في جدول Requests إلى Closed
        request_id = chat_data.get('requestID')
        if request_id:
            db.collection('Requests').document(request_id).update({
                "status": "Closed",
                "closedAt": firestore.SERVER_TIMESTAMP
            })
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ══════════════════════════════════════════════════════════
# ميزة الأرشيف: جلب المحادثة التاريخية (للقراءة فقط)
# ══════════════════════════════════════════════════════════
@bp.route('/api/chat/history/<chat_id>', methods=['GET'])
@login_required
def get_chat_history(chat_id):
    """
    جلب سجل المحادثة التاريخية الكامل من قاعدة البيانات للعميل أو المحامي
    """
    db = get_db()
    try:
        chat_doc = db.collection('ChatSessions').document(chat_id).get()
        if not chat_doc.exists:
            chat_doc = db.collection('Requests').document(chat_id).get()
            if not chat_doc.exists:
                return jsonify({"success": False, "msg": "المحادثة غير موجودة"}), 404

        chat_data = chat_doc.to_dict()
        if session['user_id'] not in [chat_data.get('clientID'), chat_data.get('lawyerID')] and session['role'] != 'Admin':
            return jsonify({"success": False, "msg": "غير مصرح لك بالوصول لهذا الأرشيف"}), 403

        # جلب الرسائل من الداتا بيز
        msg_docs = db.collection('messages')\
            .where('sessionID', '==', str(chat_id))\
            .stream()

        messages = []
        for d in msg_docs:
            msg_data = d.to_dict()
            messages.append(msg_data)

        # الترتيب الزمني للرسائل
        messages.sort(key=lambda x: x.get('timestamp').timestamp() if x.get('timestamp') and hasattr(x.get('timestamp'), 'timestamp') else 0)

        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500