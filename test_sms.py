import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')

# Put YOUR personal verified smartphone number here
MY_PHONE_NUMBER = "+911010101010" 

try:
    print("Connecting to Twilio...")
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    
    message = client.messages.create(
        body="Test Successful! Your 3FA SMS Gateway is working.",
        from_=TWILIO_NUMBER,
        to=MY_PHONE_NUMBER
    )
    
    print(f"SUCCESS! Message sent. SID: {message.sid}")
except Exception as e:
    print(f"FAILED: {e}")