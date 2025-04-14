import cv2  # type: ignore
import dlib # type: ignore
import numpy as np # type: ignore
import time
from imutils import face_utils # type: ignore
from scipy.spatial import distance as dist # type: ignore
import os
import csv

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.backends import default_backend # type: ignore
from cryptography.hazmat.primitives import padding # type: ignore

def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[2], mouth[9])
    B = dist.euclidean(mouth[4], mouth[7])
    C = dist.euclidean(mouth[0], mouth[6])
    return (A + B) / (2.0 * C)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

EYE_AR_THRESH = 0.2
EYE_AR_CONSEC_FRAMES = 3
MOUTH_AR_THRESH = 0.6

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS['left_eye']
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']
(mStart, mEnd) = (49, 68)

data = {}
try:
    with open('database.csv', 'r') as file:
        reader = csv.reader(file)
        for rows in reader:
            if len(rows) >= 3:  
                try:
                    data[int(rows[0])] = (int(rows[1]), int(rows[2]))
                except ValueError:
                    continue
except FileNotFoundError:
    print("[ERROR] database.csv not found!")
    exit()

user_id = int(input("Enter your ID for authentication: "))
if user_id not in data:
    print("[ERROR] ID not found in the database!")
    exit()

stored_blinks, stored_mouth_opens = data[user_id]
print(f"Stored Blinks: {stored_blinks}, Stored Mouth Opens: {stored_mouth_opens}")

print('[INFO] Starting authentication...')
cap = cv2.VideoCapture(0)
time.sleep(2)  

COUNTER = 0
TOTAL_BLINKS = 0
TOTAL_MOUTH_OPENS = 0
flag = 0
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to capture video!")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    
    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        mouth = shape[mStart:mEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        mar = mouth_aspect_ratio(mouth)
        
        if mar > MOUTH_AR_THRESH and flag == 0:
            flag = 1
            TOTAL_MOUTH_OPENS += 1
            time.sleep(1)
        else:
            flag = 0
        
        if ear < EYE_AR_THRESH:
            COUNTER += 1
        else:
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                TOTAL_BLINKS += 1
            COUNTER = 0
        
        cv2.putText(frame, f"Blinks: {TOTAL_BLINKS}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"Mouth: {TOTAL_MOUTH_OPENS}", (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    
    if time.time() - start_time > 10:
        break

cap.release()
cv2.destroyAllWindows()

print(f"Detected Blinks: {TOTAL_BLINKS}, Detected Mouth Opens: {TOTAL_MOUTH_OPENS}")
if TOTAL_BLINKS == stored_blinks and TOTAL_MOUTH_OPENS == stored_mouth_opens:
    print("Authentication successful! Access granted.")
    encrypted_file_path = input("Enter the encrypted file path to decrypt: ")
    decrypted_file_path = encrypted_file_path.replace(".enc", "")

    try:
        with open("key_iv.bin", "rb") as key_file:
            key_data = key_file.read()
            KEY = key_data[:32]  
            IV = key_data[32:]   

        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

        with open(decrypted_file_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted_data)

        os.remove(encrypted_file_path)

        print(f"File decrypted successfully. Decrypted file saved as {decrypted_file_path}.")
        print(f"Encrypted file {encrypted_file_path} has been deleted.")

    except Exception as e:
        print(f"An error occurred during decryption: {e}")
    
    print(f"File decrypted successfully. Decrypted file saved as {decrypted_file_path}.")
else:
    print("Authentication failed! Access denied.")