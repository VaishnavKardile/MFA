import face_recognition
import numpy as np
import cv2
import base64

def get_face_encoding_from_base64(b64_string):
    """
    Takes a base64 image string from the webcam, finds the face, 
    and returns the biometric encoding as raw bytes.
    """
    # 1. Strip the HTML header from the base64 string
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
        
    # 2. Convert base64 into a format OpenCV can read
    img_data = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 3. Convert from OpenCV's BGR color space to standard RGB
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 4. Locate the face in the image
    face_locations = face_recognition.face_locations(rgb_img)
    
    # 5. Security checks: ensure exactly one face is visible
    if len(face_locations) == 0:
        return None, "Error: No face detected. Please ensure good lighting."
    elif len(face_locations) > 1:
        return None, "Error: Multiple faces detected. Only you should be in frame."
        
    # 6. Generate the 128-dimension encoding
    encodings = face_recognition.face_encodings(rgb_img, face_locations)
    
    # FIX: Convert the raw bytes into a safe Base64 string for MySQL
    encoding_bytes = encodings[0].tobytes()
    safe_string = base64.b64encode(encoding_bytes).decode('utf-8')
    
    return safe_string, "Success"
    
    # Convert to bytes so it can be safely stored in the MySQL BLOB column
    return encodings[0].tobytes(), "Success"


def verify_face_against_db(db_b64_string, new_image_b64):
    """Compares a live webcam photo to the saved database encoding."""
    # 1. Strip the HTML header from the new webcam image
    if ',' in new_image_b64:
        new_image_b64 = new_image_b64.split(',')[1]
        
    # 2. Convert the new webcam image into a format OpenCV can read
    img_data = base64.b64decode(new_image_b64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 3. Find the face in the live webcam image
    face_locations = face_recognition.face_locations(rgb_img)
    if len(face_locations) == 0:
        return False, "No face detected in the login image."
    elif len(face_locations) > 1:
        return False, "Multiple faces detected. Login aborted."
        
    new_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
    
    # 4. Decode the registered face from the database
    db_bytes = base64.b64decode(db_b64_string)
    known_encoding = np.frombuffer(db_bytes, dtype=np.float64)
    
    # 5. The Ultimate Test: Compare the two faces!
    # tolerance=0.5 is a strict security threshold (default is 0.6)
    results = face_recognition.compare_faces([known_encoding], new_encoding, tolerance=0.5)
    
    if results[0]:
        return True, "Face verified successfully."
    else:
        return False, "Biometric mismatch! Face does not match the registered user."