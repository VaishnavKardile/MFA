import face_recognition
import numpy as np
import cv2
import base64
import os
from cryptography.fernet import Fernet
from flask import request

# Initialize the AES Encryption tool using your secret key from the .env file
fernet = Fernet(os.getenv('AES_SECRET_KEY'))

def get_face_encoding_from_base64(b64_string):
    """
    Takes a live webcam image, finds the face quickly, extracts the biometric data,
    and returns an AES-encrypted string safe for database storage.
    """
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
        
    img_data = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # ⚡ Shrink image to 1/4 size for lightning-fast scanning
    small_img = cv2.resize(rgb_img, (0, 0), fx=0.25, fy=0.25)
    small_face_locations = face_recognition.face_locations(small_img)
    
    if len(small_face_locations) == 0:
        return None, "Error: No face detected. Please ensure good lighting."
    elif len(small_face_locations) > 1:
        return None, "Error: Multiple faces detected. Only you should be in frame."
        
    # Scale coordinates back up by 4
    face_locations = []
    for top, right, bottom, left in small_face_locations:
        face_locations.append((top * 4, right * 4, bottom * 4, left * 4))
        
    # Generate the high-quality encoding
    encodings = face_recognition.face_encodings(rgb_img, face_locations)
    encoding_bytes = encodings[0].tobytes()
    
    # 🔒 THE ENCRYPTION UPGRADE 🔒
    # Keep it as raw bytes for the database LargeBinary column!
    encrypted_bytes = fernet.encrypt(encoding_bytes)
    
    return encrypted_bytes, "Success"


def verify_face_against_db(db_encrypted_string, new_image_b64):
    """Compares a live webcam photo to the AES-encrypted database encoding."""
    if ',' in new_image_b64:
        new_image_b64 = new_image_b64.split(',')[1]
        
    img_data = base64.b64decode(new_image_b64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # ⚡ Shrink live image to 1/4 size for login scanning
    small_img = cv2.resize(rgb_img, (0, 0), fx=0.25, fy=0.25)
    small_face_locations = face_recognition.face_locations(small_img)
    
    if len(small_face_locations) == 0:
        return False, "No face detected in the login image."
    elif len(small_face_locations) > 1:
        return False, "Multiple faces detected. Login aborted."
        
    # Scale coordinates back up by 4
    face_locations = []
    for top, right, bottom, left in small_face_locations:
        face_locations.append((top * 4, right * 4, bottom * 4, left * 4))
        
    # Extract live encoding
    new_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
    
    # # 🔓 THE DECRYPTION UPGRADE 🔓
    # # Unlock the database string back into raw bytes so OpenCV can read it
    # encrypted_bytes = db_encrypted_string.encode('utf-8')
    # decrypted_bytes = fernet.decrypt(encrypted_bytes)

    
    
    # # Rebuild the numpy array from the decrypted bytes
    # known_encoding = np.frombuffer(decrypted_bytes, dtype=np.float64)

    # 🔓 THE DECRYPTION UPGRADE 🔓
    # The database gives us raw bytes, so we can decrypt them directly!
    decrypted_bytes = fernet.decrypt(db_encrypted_string) 
    
    # Rebuild the numpy array from the decrypted bytes
    known_encoding = np.frombuffer(decrypted_bytes, dtype=np.float64)
    
    # Compare the two faces
    results = face_recognition.compare_faces([known_encoding], new_encoding, tolerance=0.5)
    
    if results:
        return True, "Face verified successfully."
    else:
        return False, "Biometric mismatch! Face does not match the registered user."