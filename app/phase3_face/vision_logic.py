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


# ── Security threshold for biometric verification ──────────────────────
# Default tolerance in face_recognition is 0.6 (consumer-grade).
# For a 3FA security system, 0.45 dramatically reduces False Acceptance Rate
# while still accommodating minor lighting/angle variation.
FACE_MATCH_THRESHOLD = 0.45


def verify_face_against_db(db_encrypted_string, new_image_b64):
    """
    Compares a live webcam photo against the AES-encrypted database encoding.

    Pipeline:
      1. Decode the base64 webcam frame → full-resolution RGB image.
      2. Downscale to 1/4 ONLY for fast face-location detection.
      3. Scale bounding-box coordinates back up ×4.
      4. Extract the 128-d face encoding from the FULL-RESOLUTION image
         using the upscaled coordinates (preserves fine facial geometry).
      5. Decrypt the stored encoding (AES-256 via Fernet).
      6. Compute the Euclidean distance between the two 128-d vectors.
      7. Reject if distance > FACE_MATCH_THRESHOLD (0.45).

    Returns:
        (bool, str): (is_match, diagnostic_message)
    """
    # ── 1. Decode the live webcam frame ─────────────────────────────────
    if ',' in new_image_b64:
        new_image_b64 = new_image_b64.split(',')[1]

    img_data = base64.b64decode(new_image_b64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return False, "Error: Could not decode the login image."

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ── 2. Downscale ONLY for bounding-box detection (speed) ────────────
    scale_factor = 4
    small_img = cv2.resize(rgb_img, (0, 0), fx=1 / scale_factor, fy=1 / scale_factor)
    small_face_locations = face_recognition.face_locations(small_img)

    if len(small_face_locations) == 0:
        return False, "No face detected in the login image."
    elif len(small_face_locations) > 1:
        return False, "Multiple faces detected. Login aborted."

    # ── 3. Scale coordinates back to original resolution ────────────────
    top, right, bottom, left = small_face_locations[0]
    full_res_location = (
        top    * scale_factor,
        right  * scale_factor,
        bottom * scale_factor,
        left   * scale_factor,
    )

    # ── 4. Extract encoding from the FULL-RESOLUTION image ─────────────
    #    This is the critical fix: encoding quality depends on pixel data
    #    at the bounding-box region, NOT on the thumbnail.
    live_encodings = face_recognition.face_encodings(rgb_img, [full_res_location])

    if len(live_encodings) == 0:
        return False, "Face detected but encoding extraction failed. Try again."

    live_encoding = live_encodings[0]

    # ── 5. Decrypt the stored biometric from the database ───────────────
    #    The database column stores raw Fernet-encrypted bytes.
    decrypted_bytes = fernet.decrypt(db_encrypted_string)
    known_encoding = np.frombuffer(decrypted_bytes, dtype=np.float64)

    # ── 6. Compute Euclidean distance (NOT a loose boolean compare) ─────
    #    face_distance returns an ndarray of distances; we need the first.
    distance = face_recognition.face_distance([known_encoding], live_encoding)[0]

    # ── 7. Strict threshold enforcement ─────────────────────────────────
    if distance <= FACE_MATCH_THRESHOLD:
        return True, f"Face verified. Distance: {distance:.4f} (threshold: {FACE_MATCH_THRESHOLD})"
    else:
        return False, f"Biometric mismatch. Distance: {distance:.4f} exceeds threshold {FACE_MATCH_THRESHOLD}."