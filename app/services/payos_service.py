"""
PayOS Service - Final Complete Version với QR Code VietQR
"""
import os
import time
from payos import PayOS, PaymentData, ItemData
from typing import Dict, Any, Optional

# Debug: In ra giá trị biến môi trường (optional)
PAYOS_CLIENT_ID = os.environ.get('PAYOS_CLIENT_ID')
PAYOS_API_KEY = os.environ.get('PAYOS_API_KEY')
PAYOS_CHECKSUM_KEY = os.environ.get('PAYOS_CHECKSUM_KEY')

print(f"[DEBUG] Environment PayOS vars loaded: CLIENT_ID={PAYOS_CLIENT_ID is not None}")

class PayOSService:
    def __init__(self, client_id: str, api_key: str, checksum_key: str):
        """
        Khởi tạo PayOS Service với SDK chính thức
        """
        self.client_id = client_id
        self.api_key = api_key
        self.checksum_key = checksum_key
        
        # Khởi tạo PayOS SDK
        self.payos = PayOS(
            client_id=client_id,
            api_key=api_key,
            checksum_key=checksum_key
        )
        print(f"[DEBUG] PayOS SDK initialized for client: {client_id}")
    
    def create_payment_link(self, order_code, amount: int, description: str, 
                          return_url: str, cancel_url: str, webhook_url: str = None, items=None, expired_at=None) -> Dict[str, Any]:
        """
        Tạo link thanh toán PayOS với QR Code VietQR
        """
        try:
            # Chuyển order_code thành số nguyên nếu là string
            if isinstance(order_code, str):
                # Tạo orderCode số nguyên từ timestamp và hash
                order_code_int = int(f"{int(time.time())}{abs(hash(order_code)) % 1000}")
            else:
                order_code_int = int(order_code)
            
            print(f"[DEBUG] OrderCode đã convert: {order_code_int} (type: {type(order_code_int)})")
            
            # Đảm bảo description ≤ 25 ký tự cho PayOS
            short_description = description[:25] if len(description) > 25 else description
            print(f"[DEBUG] Description: '{short_description}' (length: {len(short_description)})")
            
            # Tạo items mặc định nếu không có
            if not items:
                items = [ItemData(name=short_description, quantity=1, price=amount)]
            else:
                # Convert dict items thành ItemData objects
                item_objects = []
                for item in items:
                    if isinstance(item, dict):
                        item_obj = ItemData(
                            name=item.get('name', 'Sản phẩm')[:50],  # Giới hạn tên item
                            quantity=item.get('quantity', 1),
                            price=item.get('price', amount)
                        )
                        item_objects.append(item_obj)
                    else:
                        item_objects.append(item)
                items = item_objects
            
            print(f"[DEBUG] Items: {[{'name': item.name, 'quantity': item.quantity, 'price': item.price} for item in items]}")
            
            # Tạo PaymentData object theo đúng SDK
            payment_data = PaymentData(
                orderCode=order_code_int,  # Phải là số nguyên
                amount=int(amount),
                description=short_description,  # Cắt ngắn description
                items=items,
                cancelUrl=cancel_url,
                returnUrl=return_url
            )
            
            # Nếu có webhook_url, set vào payment_data (nếu SDK hỗ trợ)
            if webhook_url:
                try:
                    payment_data.webhookUrl = webhook_url
                    print(f"[DEBUG] Đã set webhook_url cho payment: {webhook_url}")
                except Exception as e:
                    print(f"[DEBUG] Không thể set webhook_url cho payment_data: {e}")
            print(f"[DEBUG] PaymentData created: orderCode={payment_data.orderCode}, amount={payment_data.amount}")
            
            # Gọi SDK PayOS - method đúng
            result = self.payos.createPaymentLink(paymentData=payment_data)
            
            print(f"[DEBUG] PayOS result type: {type(result)}")
            print(f"[DEBUG] PayOS result: {result}")
            
            # Trả về kết quả theo format chuẩn - PayOS SDK trả về CreatePaymentResult object
            if result:
                return {
                    'success': True,
                    'checkout_url': getattr(result, 'checkoutUrl', None),
                    'checkoutUrl': getattr(result, 'checkoutUrl', None),  # Backward compatibility
                    'paymentLinkId': getattr(result, 'paymentLinkId', None),
                    'orderCode': getattr(result, 'orderCode', None),
                    'qrCode': getattr(result, 'qrCode', None),  # QR Code VietQR data
                    'bin': getattr(result, 'bin', None),
                    'accountNumber': getattr(result, 'accountNumber', None),
                    'accountName': getattr(result, 'accountName', None),
                    'amount': getattr(result, 'amount', None),
                    'status': getattr(result, 'status', None),
                    'currency': getattr(result, 'currency', 'VND'),
                    'description': getattr(result, 'description', short_description),
                    'expiredAt': getattr(result, 'expiredAt', None),
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'error': True,
                    'message': 'PayOS trả về kết quả rỗng'
                }
                
        except Exception as e:
            print(f"[PAYOS ERROR] Exception: {e}")
            import traceback
            print(f"[PAYOS ERROR] Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': True,
                'message': f"Lỗi PayOS: {str(e)}",
                'details': str(e)
            }
    
    def get_payment_info(self, order_code: int) -> Dict[str, Any]:
        """
        Lấy thông tin thanh toán từ PayOS
        """
        try:
            result = self.payos.getPaymentLinkInformation(orderId=order_code)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            print(f"[PAYOS ERROR] Get payment info: {e}")
            return {
                'success': False,
                'error': True,
                'message': f"Lỗi lấy thông tin payment: {str(e)}"
            }
    
    def cancel_payment(self, order_code: int, reason: str = "Hủy đơn hàng") -> Dict[str, Any]:
        """
        Hủy thanh toán
        """
        try:
            result = self.payos.cancelPaymentLink(orderId=order_code, cancellationReason=reason)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            print(f"[PAYOS ERROR] Cancel payment: {e}")
            return {
                'success': False,
                'error': True,
                'message': f"Lỗi hủy payment: {str(e)}"
            }
    
    def verify_webhook_data(self, webhook_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xác thực webhook từ PayOS
        """
        try:
            webhook_data = self.payos.verifyPaymentWebhookData(webhook_body)
            return {
                'success': True,
                'verified': True,
                'data': webhook_data
            }
        except Exception as e:
            print(f"[PAYOS ERROR] Verify webhook: {e}")
            return {
                'success': False,
                'verified': False,
                'error': True,
                'message': f"Lỗi xác thực webhook: {str(e)}"
            }
    
    def confirm_webhook_url(self, webhook_url: str) -> Dict[str, Any]:
        """
        Xác nhận webhook URL
        """
        try:
            result = self.payos.confirmWebhook(webhook_url)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            print(f"[PAYOS ERROR] Confirm webhook: {e}")
            return {
                'success': False,
                'error': True,
                'message': f"Lỗi confirm webhook: {str(e)}"
            }
    
    def is_payment_successful(self, status: str) -> bool:
        """Kiểm tra payment thành công"""
        return str(status).lower() in ['paid', 'success', 'completed', 'successful']
    
    def is_payment_failed(self, status: str) -> bool:
        """Kiểm tra payment thất bại"""
        return str(status).lower() in ['failed', 'cancelled', 'expired', 'timeout']
    
    def format_amount(self, amount: float) -> int:
        """Format amount cho PayOS"""
        return int(amount)
    
    def create_payment_items(self, booking):
        """Tạo items từ booking"""
        return [ItemData(
                            name=f"Nha {booking.home.title}"[:50],  # Giới hạn 50 ký tự
            quantity=1,
            price=int(booking.total_price)
        )]
    
    def get_bank_name_from_bin(self, bin_code: str) -> str:
        """
        Lấy tên ngân hàng từ BIN code
        """
        bank_mapping = {
            '970422': 'Ngân hàng TMCP Quân đội (MB Bank)',
            '970415': 'Ngân hàng TMCP Công thương Việt Nam (VietinBank)',
            '970436': 'Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)',
            '970418': 'Ngân hàng TMCP Đầu tư và Phát triển Việt Nam (BIDV)',
            '970405': 'Ngân hàng Nông nghiệp và Phát triển Nông thôn (Agribank)',
            '970407': 'Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)',
            '970432': 'Ngân hàng TMCP Việt Nam Thịnh vượng (VPBank)',
            '970423': 'Ngân hàng TMCP Tiên Phong (TPBank)',
            '970403': 'Ngân hàng TMCP Sài Gòn (SCB)',
            '970454': 'Ngân hàng TMCP Việt Nam Thương Tín (VietBank)',
        }
        return bank_mapping.get(bin_code, f'Ngân hàng (BIN: {bin_code})')
    
    def format_qr_display_data(self, payment_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format dữ liệu để hiển thị QR code và thông tin thanh toán
        """
        if not payment_result.get('success'):
            return payment_result
            
        bin_code = payment_result.get('bin', '')
        bank_name = self.get_bank_name_from_bin(bin_code)
        
        return {
            **payment_result,
            'bank_name': bank_name,
            'formatted_amount': f"{payment_result.get('amount', 0):,.0f} VND",
            'qr_data': payment_result.get('qrCode', ''),  # VietQR data để tạo QR
            'display_info': {
                'bank_name': bank_name,
                'account_number': payment_result.get('accountNumber', ''),
                'account_name': payment_result.get('accountName', ''),
                'amount': payment_result.get('amount', 0),
                'formatted_amount': f"{payment_result.get('amount', 0):,.0f} VND",
                'description': payment_result.get('description', ''),
                'order_code': payment_result.get('orderCode', ''),
            }
        }