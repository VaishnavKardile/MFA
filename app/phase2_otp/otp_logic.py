# import pyotp
# import qrcode
# import io
# import base64

# def generate_secret():
#     """Generates a new 32-character base32 secret."""
#     return pyotp.random_base32()

# def get_qr_code_base64(username, secret, issuer="3FA_System"):
#     """Generates a QR code and returns it as a base64 string for HTML."""
#     totp = pyotp.TOTP(secret)
#     uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    
#     img = qrcode.make(uri)
#     buf = io.BytesIO()
#     img.save(buf)
#     return base64.b64encode(buf.getvalue()).decode('utf-8')

# def send_otp_base64(user) :
#     return

# def check_otp(secret, otp_code):
#     """Verifies the 6-digit code against the secret."""
#     totp = pyotp.TOTP(secret)
#     return totp.verify(otp_code)


import random
from twilio.rest import Client
import os
import threading

# These should be in your .env file for security
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')

def generate_sms_otp():
    """Generates a random 6-digit numeric string."""
    return str(random.randint(100000, 999999))

def send_otp_via_sms(phone_number, otp_code):
    """Sends the OTP code to the user's phone via Twilio."""
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your 3FA Security Code is: {otp_code}. Do not share this with anyone.",
            from_=TWILIO_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"SMS Gateway Error: {e}")
        return False
    
def send_otp_async(phone_number, otp_code):
    thread = threading.Thread(target=send_otp_via_sms, args=(phone_number, otp_code))
    thread.start()    
    return True