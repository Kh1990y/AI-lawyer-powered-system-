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
        
        if chat_doc.exists and chat_doc.to_dict().get('status') == 'Closed':
            return jsonify({"success": False, "error": "هذه الجلسة مغلقة لا يمكن الإرسال"}), 400

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
    db = get_db()
    try:
        db.collection('ChatSessions').document(session_id).update({
            "status": "Closed",
            "closedAt": firestore.SERVER_TIMESTAMP
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500