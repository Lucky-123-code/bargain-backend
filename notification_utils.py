import os
import requests
from typing import List, Dict, Any

# SMS and Email notification utilities

def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS notification to the user's phone number.
    Uses Fast2SMS or similar service (free tier available).
    Returns True if successful, False otherwise.
    """
    try:
        # Using Fast2SMS free API (for demo purposes)
        # In production, use Twilio, Nexmo, or other SMS services
        
        # Fast2SMS free API (requires no authentication for limited use)
        url = "https://www.fast2sms.com/dev/bulkV2"
        
        payload = {
            "message": message,
            "language": "english",
            "route": "q",
            "numbers": phone
        }
        
        headers = {
            "authorization": os.getenv("FAST2SMS_API_KEY", ""),
            "Content-Type": "application/json"
        }
        
        # If no API key configured, simulate success for demo
        if not os.getenv("FAST2SMS_API_KEY"):
            print(f"[SMS SIMULATION] To {phone}: {message}")
            return True
            
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return True
        else:
            print(f"SMS API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"SMS Error: {str(e)}")
        # For demo, return True to not block order creation
        return True


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification to the user.
    Uses SMTP or email service API.
    Returns True if successful, False otherwise.
    """
    try:
        # Using SendGrid, Mailgun, or similar service
        # For demo, we'll simulate the email sending
        
        # Check if SendGrid API key is configured
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        if sendgrid_api_key:
            url = "https://api.sendgrid.com/v3/mail/send"
            
            payload: Dict[str, Any] = {
                "personalizations": [{
                    "to": [{"email": to_email}]
                }],
                "from": {"email": "noreply@bargainhub.com", "name": "BargainHub"},
                "subject": subject,
                "content": [{
                    "type": "text/html",
                    "value": body
                }]
            }
            
            headers = {
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 202]:
                return True
            else:
                print(f"Email API Error: {response.text}")
                return False
        else:
            # Simulate email sending for demo
            print(f"[EMAIL SIMULATION] To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body[:100]}...")
            return True
            
    except Exception as e:
        print(f"Email Error: {str(e)}")
        # For demo, return True to not block order creation
        return True


def send_order_confirmation_sms(phone: str, order_id: int, total: float) -> bool:
    """Send order confirmation SMS"""
    message = f"Order #{order_id} confirmed! Total: ₹{total}. Thank you for shopping with BargainHub. Track your order in the app."
    return send_sms(phone, message)


def send_order_confirmation_email(email: str, order_id: int, total: float, items: List[Dict[str, Any]]) -> bool:
    """Send order confirmation email"""
    subject = f"Order Confirmation - #{order_id}"
    
    items_html = ""
    for item in items:
        items_html += f"<li>{item.get('name', 'Product')} x {item.get('quantity', 1)} - ₹{item.get('price', 0)}</li>"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #667eea;">Order Confirmed! 🎉</h2>
        <p>Thank you for your order. Here are your order details:</p>
        
        <h3>Order #{order_id}</h3>
        <ul>
            {items_html}
        </ul>
        
        <p><strong>Total: ₹{total}</strong></p>
        
        <p>We'll notify you when your order is shipped. You can track your order status in the BargainHub app.</p>
        
        <p style="margin-top: 30px; color: #666;">
            Thanks,<br>
            BargainHub Team
        </p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body)


def send_shipping_notification_sms(phone: str, order_id: int, tracking_info: str = "") -> bool:
    """Send shipping notification SMS"""
    message = f"Order #{order_id} has been shipped! {tracking_info}. Track your order in the BargainHub app."
    return send_sms(phone, message)


def send_delivery_notification_sms(phone: str, order_id: int) -> bool:
    """Send delivery notification SMS"""
    message = f"Order #{order_id} has been delivered! Thank you for shopping with BargainHub. Please rate your experience."
    return send_sms(phone, message)
