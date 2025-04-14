from scipy.spatial import distance as dist # type: ignore
from imutils.video import VideoStream # type: ignore
from imutils import face_utils # type: ignore
import time
import numpy as np # type: ignore
import imutils # type: ignore
import cv2 # type: ignore
import dlib # type: ignore
from csv import writer
from time import sleep
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.backends import default_backend # type: ignore
import os
from cryptography.hazmat.primitives import padding # type: ignore

def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[2], mouth[9])  # 51, 59
    B = dist.euclidean(mouth[4], mouth[7])  # 53, 57
    C = dist.euclidean(mouth[0], mouth[6])  # 49, 55
    return (A + B) / (2.0 * C)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

MOUTH_AR_THRESH = 0.6
EYE_AR_THRESH = 0.2
EYE_AR_CONSEC_FRAMES = 3
IMAGE_SAVE_PATH = "1.jpg"  

if not os.path.exists("key_iv.bin"):
    KEY = os.urandom(32)  
    IV = os.urandom(16)  
    with open("key_iv.bin", "wb") as key_file:
        key_file.write(KEY + IV)
else:
    with open("key_iv.bin", "rb") as key_file:
        key_data = key_file.read()
        KEY = key_data[:32]  
        IV = key_data[32:]   

record = []
rt = int(input("ENTER YOUR ID TO ENROLL: "))
record.append(rt)

COUNTER = 0
TOTAL = 0
TM = 0
flag = 0
enroll = 0

print('[INFO] Loading facial landmark predictor...')
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS['left_eye']
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']
(mStart, mEnd) = (49, 68)

print('[INFO] Starting video stream...')
vs = VideoStream(src=0).start()
time.sleep(1.0)
start_time = time.time()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        leftEye = shape[lStart: lEnd]
        rightEye = shape[rStart: rEnd]
        mouth = shape[mStart:mEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        mar = mouth_aspect_ratio(mouth)

        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        mouthHull = cv2.convexHull(mouth)
        cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)
        cv2.putText(frame, "MAR: {:.2f}".format(mar), (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        if mar > MOUTH_AR_THRESH and flag == 0:
            flag = 1
            cv2.putText(frame, "Mouth is Open!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            TM += 1
            sleep(1)
        else:
            flag = 0

        if ear < EYE_AR_THRESH:
            COUNTER += 1
        else:
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                TOTAL += 1
            COUNTER = 0

        cv2.putText(frame, "Blinks: {}".format(TOTAL), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "Mouth: {}".format(TM), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        if enroll == 0:
            cv2.imwrite(IMAGE_SAVE_PATH, frame)  
        elif enroll == 1:
            cv2.imwrite("2.jpg", frame)  

        elapsed_time = time.time() - start_time
        if elapsed_time > 10 and enroll < 2:
            enroll += 1
            record.append(TOTAL)
            record.append(TM)
            TOTAL = 0
            TM = 0
            print(f"COMPLETED STEP {enroll}")
            sleep(5)
            start_time = time.time()

    if enroll == 2:
        break

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()

print("Final Record:", record)
with open('database.csv', 'a') as f_object:
    writer_object = writer(f_object)
    writer_object.writerow(record)

file_path = input("Enter the file path to encrypt: ")

with open(file_path, 'rb') as file:
    file_data = file.read()

padder = padding.PKCS7(algorithms.AES.block_size).padder()
padded_data = padder.update(file_data) + padder.finalize()

cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
encryptor = cipher.encryptor()
encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

encrypted_file_path = file_path + '.enc'
with open(encrypted_file_path, 'wb') as encrypted_file:
    encrypted_file.write(encrypted_data)

os.remove(file_path)

print(f"File encrypted successfully. Encrypted file saved as {encrypted_file_path}.")
