from flask import Blueprint, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.models import Owner, Renter, db
from app.utils.email_service import email_service
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

email_verification_bp = Blueprint('email_verification', __name__, url_prefix='/email-verification')

# Renter Email Verification Routes
@email_verification_bp.route('/renter/send-otp', methods=['POST'])
@login_required
def renter_send_otp():
    """Gửi mã OTP để verify email cho Renter"""
    try:
        # Kiểm tra user có phải là Renter không
        if not current_user.is_renter():
            return jsonify({'success': False, 'message': 'Chỉ Renter mới có thể verify email'}), 403
        
        renter = current_user
        
        # Kiểm tra email đã verify chưa
        if renter.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        
        # Kiểm tra số lần gửi trong ngày
        today = datetime.now().date().isoformat()
        send_count = session.get('renter_email_send_count', {}).get(today, 0)
        blocked_until = session.get('renter_email_send_blocked_until')
        now = datetime.now()
        if send_count >= email_service.max_resend_per_day:
            # Nếu đã bị block, kiểm tra thời gian
            if blocked_until:
                blocked_until_dt = datetime.fromisoformat(blocked_until)
                if now < blocked_until_dt:
                    seconds_left = int((blocked_until_dt - now).total_seconds())
                    minutes = seconds_left // 60
                    seconds = seconds_left % 60
                    return jsonify({'success': False, 'message': f'Bạn đã gửi quá {email_service.max_resend_per_day} lần. Vui lòng thử lại sau {minutes} phút {seconds} giây.'}), 400
                else:
                    # Đã hết thời gian block, reset lại bộ đếm
                    send_count = 0
                    session['renter_email_send_count'][today] = 0
                    session.pop('renter_email_send_blocked_until', None)
            else:
                # Nếu chưa có thời gian block, set block 5 phút
                session['renter_email_send_blocked_until'] = (now + timedelta(minutes=5)).isoformat()
                return jsonify({'success': False, 'message': f'Bạn đã gửi quá {email_service.max_resend_per_day} lần. Vui lòng thử lại sau 5 phút.'}), 400
        
        # Tạo mã OTP
        otp = email_service.generate_otp()
        
        # Gửi email với token bảo mật
        success, message, secure_token = email_service.send_verification_email(
            renter.email, 
            otp, 
            renter.full_name or renter.username,
            renter.id
        )
        
        if success:
            # Lưu OTP và token vào session với thời gian hết hạn mới
            session['renter_email_verification_otp'] = otp
            session['renter_email_verification_token'] = secure_token
            session['renter_email_verification_expires'] = (datetime.now() + timedelta(minutes=email_service.otp_expiry_minutes)).isoformat()
            session['renter_email_verification_attempts'] = 0
            
            # Cập nhật số lần gửi
            if 'renter_email_send_count' not in session:
                session['renter_email_send_count'] = {}
            session['renter_email_send_count'][today] = send_count + 1
            
            logger.info(f"OTP sent successfully to renter {renter.email}")
            return jsonify({
                'success': True, 
                'message': f'Mã OTP đã được gửi đến email của bạn (có hiệu lực {email_service.otp_expiry_minutes} phút)',
                'email': renter.email,
                'expires_in': email_service.otp_expiry_minutes,
                'token': secure_token
            })
        else:
            logger.error(f"Failed to send OTP to renter {renter.email}: {message}")
            return jsonify({'success': False, 'message': f'Không thể gửi email: {message}'}), 500
            
    except Exception as e:
        logger.error(f"Error in renter_send_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/renter/verify-otp', methods=['POST'])
@login_required
def renter_verify_otp():
    """Xác thực mã OTP cho Renter"""
    try:
        # Kiểm tra user có phải là Renter không
        if not current_user.is_renter():
            return jsonify({'success': False, 'message': 'Chỉ Renter mới có thể verify email'}), 403
        
        renter = current_user
        data = request.get_json()
        otp_input = data.get('otp', '').strip()
        
        if not otp_input:
            return jsonify({'success': False, 'message': 'Vui lòng nhập mã OTP'}), 400
        
        # Kiểm tra email đã verify chưa
        if renter.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        
        # Lấy OTP và token từ session
        stored_otp = session.get('renter_email_verification_otp')
        stored_token = session.get('renter_email_verification_token')
        expires_str = session.get('renter_email_verification_expires')
        
        if not stored_otp or not stored_token or not expires_str:
            return jsonify({'success': False, 'message': 'Mã OTP không hợp lệ hoặc đã hết hạn'}), 400
        
        # Kiểm tra thời gian hết hạn
        expires = datetime.fromisoformat(expires_str)
        if datetime.now() > expires:
            # Xóa OTP hết hạn
            session.pop('renter_email_verification_otp', None)
            session.pop('renter_email_verification_token', None)
            session.pop('renter_email_verification_expires', None)
            session.pop('renter_email_verification_attempts', None)
            return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 400
        
        # Kiểm tra số lần thử
        attempts = session.get('renter_email_verification_attempts', 0)
        if attempts >= email_service.max_attempts_per_otp:
            return jsonify({'success': False, 'message': f'Bạn đã thử quá {email_service.max_attempts_per_otp} lần. Vui lòng yêu cầu mã mới'}), 400
        
        # Tăng số lần thử
        session['renter_email_verification_attempts'] = attempts + 1
        
        # Xác thực token bảo mật
        verified_otp, timestamp = email_service.verify_secure_token(stored_token, renter.id)
        if not verified_otp or verified_otp != stored_otp:
            return jsonify({'success': False, 'message': 'Token xác thực không hợp lệ'}), 400
        
        # Kiểm tra OTP
        if otp_input != stored_otp:
            return jsonify({'success': False, 'message': 'Mã OTP không đúng'}), 400
        
        # OTP đúng - cập nhật database
        renter.email_verified = True
        renter.first_login = False
        db.session.commit()
        
        # Xóa OTP khỏi session
        session.pop('renter_email_verification_otp', None)
        session.pop('renter_email_verification_token', None)
        session.pop('renter_email_verification_expires', None)
        session.pop('renter_email_verification_attempts', None)
        
        logger.info(f"Email verified successfully for renter {renter.email}")
        return jsonify({
            'success': True, 
            'message': 'Email đã được xác thực thành công!',
            'redirect_url': url_for('renter.dashboard')
        })
        
    except Exception as e:
        logger.error(f"Error in renter_verify_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/renter/resend-otp', methods=['POST'])
@login_required
def renter_resend_otp():
    """Gửi lại mã OTP cho Renter"""
    try:
        # Kiểm tra user có phải là Renter không
        if not current_user.is_renter():
            return jsonify({'success': False, 'message': 'Chỉ Renter mới có thể verify email'}), 403
        
        renter = current_user
        
        # Kiểm tra email đã verify chưa
        if renter.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        
        # Kiểm tra số lần gửi lại trong ngày
        today = datetime.now().date().isoformat()
        resend_count = session.get('renter_email_resend_count', {}).get(today, 0)
        
        if resend_count >= email_service.max_resend_per_day:
            return jsonify({'success': False, 'message': f'Bạn đã gửi lại quá {email_service.max_resend_per_day} lần trong ngày. Vui lòng thử lại vào ngày mai'}), 400
        
        # Tạo mã OTP mới
        otp = email_service.generate_otp()
        
        # Gửi email với token bảo mật
        success, message, secure_token = email_service.send_resend_otp_email(
            renter.email, 
            otp, 
            renter.full_name or renter.username,
            renter.id
        )
        
        if success:
            # Lưu OTP mới vào session
            session['renter_email_verification_otp'] = otp
            session['renter_email_verification_token'] = secure_token
            session['renter_email_verification_expires'] = (datetime.now() + timedelta(minutes=email_service.otp_expiry_minutes)).isoformat()
            session['renter_email_verification_attempts'] = 0
            
            # Cập nhật số lần gửi lại
            if 'renter_email_resend_count' not in session:
                session['renter_email_resend_count'] = {}
            session['renter_email_resend_count'][today] = resend_count + 1
            
            logger.info(f"OTP resent successfully to renter {renter.email}")
            return jsonify({
                'success': True, 
                'message': f'Mã OTP mới đã được gửi đến email của bạn (có hiệu lực {email_service.otp_expiry_minutes} phút)',
                'email': renter.email,
                'expires_in': email_service.otp_expiry_minutes,
                'token': secure_token
            })
        else:
            logger.error(f"Failed to resend OTP to renter {renter.email}: {message}")
            return jsonify({'success': False, 'message': f'Không thể gửi email: {message}'}), 500
            
    except Exception as e:
        logger.error(f"Error in renter_resend_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/renter/check-status', methods=['GET'])
@login_required
def renter_check_status():
    """Kiểm tra trạng thái verify email cho Renter"""
    try:
        if not current_user.is_renter():
            return jsonify({'success': False, 'message': 'Chỉ Renter mới có thể kiểm tra trạng thái'}), 403
        renter = current_user
        # Kiểm tra OTP còn hiệu lực không
        expires_str = session.get('renter_email_verification_expires')
        remaining_time = 0
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now() < expires:
                remaining_time = int((expires - datetime.now()).total_seconds() / 60)
        # Lấy số lần gửi mã và thời gian block
        today = datetime.now().date().isoformat()
        send_count = session.get('renter_email_send_count', {}).get(today, 0)
        blocked_until = session.get('renter_email_send_blocked_until')
        blocked_until_str = None
        if blocked_until:
            try:
                dt = datetime.fromisoformat(blocked_until)
                blocked_until_str = dt.strftime('%H:%M:%S')
            except:
                blocked_until_str = blocked_until
        return jsonify({
            'success': True,
            'email_verified': renter.email_verified,
            'first_login': renter.first_login,
            'email': renter.email,
            'needs_verification': not renter.email_verified and renter.first_login,
            'remaining_time': remaining_time,
            'max_attempts': email_service.max_attempts_per_otp,
            'max_resend': email_service.max_resend_per_day,
            'send_count': send_count,
            'blocked_until': blocked_until,
            'blocked_until_str': blocked_until_str
        })
    except Exception as e:
        logger.error(f"Error in renter_check_status: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500 

# Owner Email Verification Routes (Original routes)
@email_verification_bp.route('/send-otp', methods=['POST'])
@login_required
def send_otp():
    """Gửi mã OTP để verify email cho Owner hoặc Renter"""
    try:
        # Cho phép cả Owner và Renter
        if not (current_user.is_owner() or current_user.is_renter()):
            return jsonify({'success': False, 'message': 'Chỉ Owner hoặc Renter mới có thể verify email'}), 403
        user = current_user
        # Chọn prefix session và các biến phù hợp
        if user.is_owner():
            session_prefix = ''
        else:
            session_prefix = 'renter_'
        # Kiểm tra email đã verify chưa
        if user.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        # Kiểm tra số lần gửi trong ngày
        today = datetime.now().date().isoformat()
        send_count = session.get(f'{session_prefix}email_send_count', {}).get(today, 0)
        blocked_until = session.get(f'{session_prefix}email_send_blocked_until')
        now = datetime.now()
        if send_count >= email_service.max_resend_per_day:
            if blocked_until:
                blocked_until_dt = datetime.fromisoformat(blocked_until)
                if now < blocked_until_dt:
                    seconds_left = int((blocked_until_dt - now).total_seconds())
                    minutes = seconds_left // 60
                    seconds = seconds_left % 60
                    return jsonify({'success': False, 'message': f'Bạn đã gửi quá {email_service.max_resend_per_day} lần. Vui lòng thử lại sau {minutes} phút {seconds} giây.'}), 400
                else:
                    send_count = 0
                    session[f'{session_prefix}email_send_count'][today] = 0
                    session.pop(f'{session_prefix}email_send_blocked_until', None)
            else:
                session[f'{session_prefix}email_send_blocked_until'] = (now + timedelta(minutes=5)).isoformat()
                return jsonify({'success': False, 'message': f'Bạn đã gửi quá {email_service.max_resend_per_day} lần. Vui lòng thử lại sau 5 phút.'}), 400
        # Tạo mã OTP
        otp = email_service.generate_otp()
        # Gửi email với token bảo mật
        success, message, secure_token = email_service.send_verification_email(
            user.email, 
            otp, 
            user.full_name or user.username,
            user.id
        )
        if success:
            # Lưu OTP và token vào session với thời gian hết hạn mới
            session[f'{session_prefix}email_verification_otp'] = otp
            session[f'{session_prefix}email_verification_token'] = secure_token
            session[f'{session_prefix}email_verification_expires'] = (datetime.now() + timedelta(minutes=email_service.otp_expiry_minutes)).isoformat()
            session[f'{session_prefix}email_verification_attempts'] = 0
            # Cập nhật số lần gửi
            if f'{session_prefix}email_send_count' not in session:
                session[f'{session_prefix}email_send_count'] = {}
            session[f'{session_prefix}email_send_count'][today] = send_count + 1
            logger.info(f"OTP sent successfully to {user.email}")
            return jsonify({
                'success': True, 
                'message': f'Mã OTP đã được gửi đến email của bạn (có hiệu lực {email_service.otp_expiry_minutes} phút)',
                'email': user.email,
                'expires_in': email_service.otp_expiry_minutes,
                'token': secure_token
            })
        else:
            logger.error(f"Failed to send OTP to {user.email}: {message}")
            return jsonify({'success': False, 'message': f'Không thể gửi email: {message}'}), 500
    except Exception as e:
        logger.error(f"Error in send_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/verify-otp', methods=['POST'])
@login_required
def verify_otp():
    """Xác thực mã OTP cho Owner hoặc Renter"""
    try:
        if not (current_user.is_owner() or current_user.is_renter()):
            return jsonify({'success': False, 'message': 'Chỉ Owner hoặc Renter mới có thể verify email'}), 403
        user = current_user
        if user.is_owner():
            session_prefix = ''
        else:
            session_prefix = 'renter_'
        data = request.get_json()
        otp_input = data.get('otp', '').strip()
        if not otp_input:
            return jsonify({'success': False, 'message': 'Vui lòng nhập mã OTP'}), 400
        if user.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        stored_otp = session.get(f'{session_prefix}email_verification_otp')
        stored_token = session.get(f'{session_prefix}email_verification_token')
        expires_str = session.get(f'{session_prefix}email_verification_expires')
        if not stored_otp or not stored_token or not expires_str:
            return jsonify({'success': False, 'message': 'Mã OTP không hợp lệ hoặc đã hết hạn'}), 400
        expires = datetime.fromisoformat(expires_str)
        if datetime.now() > expires:
            session.pop(f'{session_prefix}email_verification_otp', None)
            session.pop(f'{session_prefix}email_verification_token', None)
            session.pop(f'{session_prefix}email_verification_expires', None)
            session.pop(f'{session_prefix}email_verification_attempts', None)
            return jsonify({'success': False, 'message': 'Mã OTP đã hết hạn'}), 400
        attempts = session.get(f'{session_prefix}email_verification_attempts', 0)
        if attempts >= email_service.max_attempts_per_otp:
            return jsonify({'success': False, 'message': f'Bạn đã thử quá {email_service.max_attempts_per_otp} lần. Vui lòng yêu cầu mã mới'}), 400
        session[f'{session_prefix}email_verification_attempts'] = attempts + 1
        verified_otp, timestamp = email_service.verify_secure_token(stored_token, user.id)
        if not verified_otp or verified_otp != stored_otp:
            return jsonify({'success': False, 'message': 'Token xác thực không hợp lệ'}), 400
        if otp_input != stored_otp:
            return jsonify({'success': False, 'message': 'Mã OTP không đúng'}), 400
        user.email_verified = True
        user.first_login = False
        db.session.commit()
        session.pop(f'{session_prefix}email_verification_otp', None)
        session.pop(f'{session_prefix}email_verification_token', None)
        session.pop(f'{session_prefix}email_verification_expires', None)
        session.pop(f'{session_prefix}email_verification_attempts', None)
        logger.info(f"Email verified successfully for {user.email}")
        redirect_url = url_for('owner.dashboard') if user.is_owner() else url_for('renter.dashboard')
        return jsonify({
            'success': True, 
            'message': 'Email đã được xác thực thành công!',
            'redirect_url': redirect_url
        })
    except Exception as e:
        logger.error(f"Error in verify_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/resend-otp', methods=['POST'])
@login_required
def resend_otp():
    """Gửi lại mã OTP cho Owner hoặc Renter"""
    try:
        if not (current_user.is_owner() or current_user.is_renter()):
            return jsonify({'success': False, 'message': 'Chỉ Owner hoặc Renter mới có thể verify email'}), 403
        user = current_user
        if user.is_owner():
            session_prefix = ''
        else:
            session_prefix = 'renter_'
        if user.email_verified:
            return jsonify({'success': False, 'message': 'Email đã được xác thực'}), 400
        today = datetime.now().date().isoformat()
        resend_count = session.get(f'{session_prefix}email_resend_count', {}).get(today, 0)
        if resend_count >= email_service.max_resend_per_day:
            return jsonify({'success': False, 'message': f'Bạn đã gửi lại quá {email_service.max_resend_per_day} lần trong ngày. Vui lòng thử lại vào ngày mai'}), 400
        otp = email_service.generate_otp()
        success, message, secure_token = email_service.send_resend_otp_email(
            user.email, 
            otp, 
            user.full_name or user.username,
            user.id
        )
        if success:
            session[f'{session_prefix}email_verification_otp'] = otp
            session[f'{session_prefix}email_verification_token'] = secure_token
            session[f'{session_prefix}email_verification_expires'] = (datetime.now() + timedelta(minutes=email_service.otp_expiry_minutes)).isoformat()
            session[f'{session_prefix}email_verification_attempts'] = 0
            if f'{session_prefix}email_resend_count' not in session:
                session[f'{session_prefix}email_resend_count'] = {}
            session[f'{session_prefix}email_resend_count'][today] = resend_count + 1
            logger.info(f"OTP resent successfully to {user.email}")
            return jsonify({
                'success': True, 
                'message': f'Mã OTP mới đã được gửi đến email của bạn (có hiệu lực {email_service.otp_expiry_minutes} phút)',
                'email': user.email,
                'expires_in': email_service.otp_expiry_minutes,
                'token': secure_token
            })
        else:
            logger.error(f"Failed to resend OTP to {user.email}: {message}")
            return jsonify({'success': False, 'message': f'Không thể gửi email: {message}'}), 500
    except Exception as e:
        logger.error(f"Error in resend_otp: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@email_verification_bp.route('/check-status', methods=['GET'])
@login_required
def check_status():
    """Kiểm tra trạng thái verify email cho Owner hoặc Renter"""
    try:
        if not (current_user.is_owner() or current_user.is_renter()):
            return jsonify({'success': False, 'message': 'Chỉ Owner hoặc Renter mới có thể kiểm tra trạng thái'}), 403
        user = current_user
        if user.is_owner():
            session_prefix = ''
        else:
            session_prefix = 'renter_'
        expires_str = session.get(f'{session_prefix}email_verification_expires')
        remaining_time = 0
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now() < expires:
                remaining_time = int((expires - datetime.now()).total_seconds() / 60)
        today = datetime.now().date().isoformat()
        send_count = session.get(f'{session_prefix}email_send_count', {}).get(today, 0)
        blocked_until = session.get(f'{session_prefix}email_send_blocked_until')
        blocked_until_str = None
        if blocked_until:
            try:
                dt = datetime.fromisoformat(blocked_until)
                blocked_until_str = dt.strftime('%H:%M:%S')
            except:
                blocked_until_str = blocked_until
        return jsonify({
            'success': True,
            'verified': user.email_verified,
            'first_login': user.first_login,
            'email': user.email,
            'needs_verification': not user.email_verified and user.first_login,
            'remaining_time': remaining_time,
            'max_attempts': email_service.max_attempts_per_otp,
            'send_count': send_count,
            'blocked_until': blocked_until_str
        })
    except Exception as e:
        logger.error(f"Error in check_status: {e}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500 