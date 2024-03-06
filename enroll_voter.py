import face_recognition
import cv2
import os
import time
import mysql.connector
import sys
import serial

# Adafruit package imports
from adafruit_fingerprint import AdafruitFingerprint
from adafruit_fingerprint.responses import *

finger_sensor_port = "COM6"

try:
    baud_rate = '57600'
    serial_port = serial.Serial(finger_sensor_port, baud_rate)
except Exception as e:
    print(e)
    sys.exit()

# Initialize sensor library with serial port connection
finger = AdafruitFingerprint(port=serial_port)

response = finger.vfy_pwd()
if response is not FINGERPRINT_PASSWORD_OK:
    print('Did not find fingerprint sensor :(')
    sys.exit()
print('Found Fingerprint Sensor!\n')


video_capture = cv2.VideoCapture(0)

obama_image = face_recognition.load_image_file("test.png")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

known_face_encodings = [
    obama_face_encoding
]
known_face_names = [
    "Test"
]

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="vote_fp"
)

personname = input("Enter the name ")
print(personname)
mobile = input("Enter the mobile number ")
print(mobile)


def insertvalues(id):
    mycursor = mydb.cursor()

    sql = "INSERT INTO voters_list (name,finger_id,mobile) VALUES " \
          "(%s, %s, %s) "
    val = (personname, str(id),"+91"+mobile)
    mycursor.execute(sql, val)

    mydb.commit()
    row_count = mycursor.rowcount
    if row_count == 0:
        print("Error values not inserted/Already registered")
    else:
        print("Voter Registered successfully")
        sys.exit()
    mycursor.close()

# path = ("E:/Myprojects/Python/working/face_recognition_vote _test/dataset/" + personname)
path = ("dataset/" + personname)

try:
    os.mkdir(path)
except OSError:
    print("Creation of the directory %s failed" % path)
else:
    print("Successfully created the directory %s " % path)

def fingerprint_detect():
    while True:
        print('\nReady to enroll a fingerprint!\n')
        print('Please type in the ID # (from 1 to 255) you want to save this finger as...')
        id = read_number()
        print(f'Enrolling id #{id}\n')
        while not enroll_to_flash_library(finger=finger, id=id):
            break

def read_number():
    num = 0
    while num < 1 or num > 255:
        try:
            num = int(input())
        except ValueError:
            print('Please provide an integer')
        else:
            if num < 1 or num > 255:
                print('Please provide an integer in the above range')

    return num


def enroll_to_flash_library(finger, id):
    CHAR_BUFF_1 = 0x01
    CHAR_BUFF_2 = 0x02

    print('Waiting for a valid finger to enroll\n')
    sys.stdout.flush()

    # Read finger the first time
    response = -1
    while response is not FINGERPRINT_OK:
        response = finger.gen_img()
        if response is FINGERPRINT_OK:
            print('Image taken')
            sys.stdout.flush()
        elif response is FINGERPRINT_NOFINGER:
            print('waiting...')
            sys.stdout.flush()
        elif response is FINGERPRINT_PACKETRECEIVER:
            print('Communication error')
            sys.stdout.flush()
        elif response is FINGERPRINT_IMAGEFAIL:
            print('Imaging Error')
            sys.stdout.flush()
        else:
            print('Unknown Error')
            sys.stdout.flush()

    response = finger.img_2Tz(buffer=CHAR_BUFF_1)
    if response is FINGERPRINT_OK:
        print('Image Converted')
        sys.stdout.flush()
    elif response is FINGERPRINT_IMAGEMESS:
        print('Image too messy')
        return response
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return response
    elif response is FINGERPRINT_FEATUREFAIL:
        print('Could not find fingerprint features')
        return response
    elif response is FINGERPRINT_INVALIDIMAGE:
        print('Could not find fingerprint features')
        return response
    else:
        print('Unknown Error')
        return response

    # Ensure finger has been removed
    print('Remove finger')
    time.sleep(1)
    response = -1
    while (response is not FINGERPRINT_NOFINGER):
        response = finger.gen_img()

    print('\nPlace same finger again')
    sys.stdout.flush()

    # Read finger the second time
    response = -1
    while response is not FINGERPRINT_OK:
        response = finger.gen_img()
        if response is FINGERPRINT_OK:
            print('Image taken')
            sys.stdout.flush()
        elif response is FINGERPRINT_NOFINGER:
            print('waiting...')
            sys.stdout.flush()
        elif response is FINGERPRINT_PACKETRECEIVER:
            print('Communication error')
            sys.stdout.flush()
        elif response is FINGERPRINT_IMAGEFAIL:
            print('Imaging Error')
            sys.stdout.flush()
        else:
            print('Unknown Error')
            sys.stdout.flush()

    response = finger.img_2Tz(buffer=CHAR_BUFF_2)
    if response is FINGERPRINT_OK:
        print('Image Converted')
        sys.stdout.flush()
    elif response is FINGERPRINT_IMAGEMESS:
        print('Image too messy')
        return response
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return response
    elif response is FINGERPRINT_FEATUREFAIL:
        print('Could not find fingerprint features')
        return response
    elif response is FINGERPRINT_INVALIDIMAGE:
        print('Could not find fingerprint features')
        return response
    else:
        print('Unknown Error')
        return response

    print('Remove finger')
    print('\nChecking both prints...\n')
    sys.stdout.flush()

    # Register model
    response = finger.reg_model()
    if response is FINGERPRINT_OK:
        print('Prints matched')
        sys.stdout.flush()
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return response
    elif response is FINGERPRINT_ENROLLMISMATCH:
        print('Prints did not match')
        return response
    else:
        print('Unknown Error')
        return response

    response = finger.store(buffer=CHAR_BUFF_2, page_id=id)
    if response is FINGERPRINT_OK:
        print(f'Print stored in id #{id} of flash library\n')
        sys.stdout.flush()
        insertvalues(id)
        return response
    if response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        sys.stdout.flush()
        return response
    if response is FINGERPRINT_BADLOCATION:
        print('Could not store in that location')
        sys.stdout.flush()
        return response
    if response is FINGERPRINT_FLASHER:
        print('Error writing to flash')
        sys.stdout.flush()
        return response


# Expose only enroll function from module
__all__ = ['enroll_to_flash_library']

while True:
    code = cv2.waitKey(10)
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Face detected"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            face_names.append(name)

    process_this_frame = not process_this_frame

    if code == ord('s'):
        for i in range(20):
            print("saving ", i)
            cv2.imwrite(path + "\\" + str(i) + ".jpg", frame)
            time.sleep(0.5)
        fingerprint_detect()
    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 1)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if code == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
