from tkinter import *
from tkinter import messagebox
#from tkinter.ttk import *
import cv2
import face_recognition
import mysql.connector
import time
import os
from adafruit_fingerprint import AdafruitFingerprint
from adafruit_fingerprint.responses import *
import serial
import sys


import tkinter as tk
from tkinter import PhotoImage
from PIL import Image


finger_sensor_port = "COM6"
try:
    baud_rate = '57600'
    serial_port = serial.Serial(finger_sensor_port, baud_rate)
except Exception as e:
    print(e)
    sys.exit()

root = Tk()
root.geometry("1700x800")

name = StringVar()
aadhar = StringVar()
fingerid = IntVar()
address = StringVar()
mobile = IntVar()

# Initialize sensor library with serial port connection
finger = AdafruitFingerprint(port=serial_port)

response = finger.vfy_pwd()
if response is not FINGERPRINT_PASSWORD_OK:
    print('Did not find fingerprint sensor :(')
    sys.exit()
print('Found Fingerprint Sensor!\n')

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

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="vote_fp"
)

def insertvalues():
    global name_entry, mobile_entry, aadhar_entry, address_entry, finger_entry
    print(type(name_entry))
    print(type(mobile_entry))
    print(type(aadhar_entry))
    print(type(address_entry))
    print(type(finger_entry))
    mycursor = mydb.cursor()

    sql = "INSERT INTO voters_list (name,finger_id,mobile, aadhar, address) VALUES " \
          "(%s, %s, %s, %s, %s) "
    val = (name_entry, str(finger_entry),"+91"+str(mobile_entry), str(aadhar_entry), address_entry)
    mycursor.execute(sql, val)

    mydb.commit()
    row_count = mycursor.rowcount
    if row_count == 0:
        print("Error values not inserted/Already registered")
    else:
        print("Voter Registered successfully")
        sys.exit()
    mycursor.close()

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
    messagebox.showinfo("Fingerprint sensor", "Remove Finger")
    print('Remove finger')
    time.sleep(1)
    response = -1
    while (response is not FINGERPRINT_NOFINGER):
        response = finger.gen_img()

    messagebox.showinfo("Fingerprint sensor", "Place same finger again")
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
        messagebox.showinfo("Fingerprint sensor", "Prints matched")
        sys.stdout.flush()
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return response
    elif response is FINGERPRINT_ENROLLMISMATCH:
        print('Prints did not match')
        messagebox.showinfo("Fingerprint sensor", "Prints did not match, Try again")
        return response
    else:
        print('Unknown Error')
        return response

    response = finger.store(buffer=CHAR_BUFF_2, page_id=id)
    if response is FINGERPRINT_OK:
        print(f'Print stored in id #{id} of flash library\n')
        sys.stdout.flush()
        insertvalues()
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

def enroll():
    global finger_entry
    print(f'Enrolling id #{finger_entry}\n')
    while not enroll_to_flash_library(finger=finger, id=finger_entry):
        break

def capture():
    global aadhar_entry
    video_capture = cv2.VideoCapture(0)

    path = ("dataset/" + aadhar_entry)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)

    process_this_frame = True
    font = cv2.FONT_HERSHEY_DUPLEX

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

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                face_names.append(name)

        process_this_frame = not process_this_frame
        cv2.putText(frame, "Press S to save", (10,40), font, 1, (255, 255, 255), 2)
        # cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)


        if code == ord('s'):
            for i in range(20):
                print("saving ", i)
                cv2.imwrite(path + "\\" + str(i) + ".jpg", frame)
                time.sleep(0.5)
            break
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
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if code == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()
    messagebox.showinfo("Fingerprint", "Place your finger on the sensor and press ok")
    enroll()

def submit():
    global finger_entry,aadhar_entry, mobile_entry, name_entry,address_entry
    name_entry = name.get()
    address_entry = address.get()
    aadhar_entry = aadhar.get()
    finger_entry = fingerid.get()
    mobile_entry = mobile.get()

    if(len(name_entry) == 0 or len(address_entry) == 0 or len(aadhar_entry) == 0):
        messagebox.showerror("Error", "Please fill all the fields")
        return
    
    if(any(chr.isalpha() for chr in aadhar_entry)):
        messagebox.showerror("Error","Invalid aadhar")
        return
    
    if len(str(aadhar_entry))!=12:
        messagebox.showerror("Error", "Please enter a valid aadhar number")
        return
    
    if len(str(mobile_entry))!=10:
        messagebox.showerror("Error", "Please enter a valid mobile number")
        return
    
    if(finger_entry>250 or finger_entry==0):
        messagebox.showerror("Error", "Please enter a valid finger ID")
        return
    capture()
    insertvalues()

def convert_image(input_path, output_path):
    jpeg_image = Image.open(input_path)
    jpeg_image = jpeg_image.resize((1700, 800), Image.ANTIALIAS)
    jpeg_image.save(output_path, "GIF")


    # Convert the JPEG image to GIF format using PIL
convert_image("3.jpg", "background.gif")  # Replace with your image path

    # Load the background image
bg_image = PhotoImage(file="background.gif")  # Use the converted GIF image

    # Create a label to display the background image
bg_label = tk.Label(root, image=bg_image)
bg_label.place(relwidth=1, relheight=1)  # Cover the entire window



label = Label(root,text="VOTER ENROLLMENT",bg="grey",fg="black",font=("times new roman",25,"bold"))
label.place(x=650,y=25)

name_label = Label(root, text='Name', font=('calibre', 10, 'bold')).place(x=675, y=100)
name_entry = Entry(root, textvariable=name, font=('calibre', 10, 'normal')).place(x=800, y=100)

Label(root, text='Aadhar', font=('calibre', 10, 'bold')).place(x=675, y=150)
# email_entry = Entry(newWindow1, textvariable=email, font=('calibre', 10, 'normal'), show='*')
Entry(root, textvariable=aadhar, font=('calibre', 10, 'normal')).place(x=800, y=150)

Label(root, text='Address', font=('calibre', 10, 'bold')).place(x=675, y=200)
Entry(root, textvariable=address, font=('calibre', 10, 'normal')).place(x=800, y=200)

Label(root, text='Finger ID', font=('calibre', 10, 'bold')).place(x=675, y=250)
Entry(root, textvariable=fingerid, font=('calibre', 10, 'normal')).place(x=800, y=250)

Label(root, text='Mobile number', font=('calibre', 10, 'bold')).place(x=675, y=300)
Entry(root, textvariable=mobile, font=('calibre', 10, 'normal')).place(x=800, y=300)

btn = Button(root,text="SUBMIT",fg="black",bg="orange",font=("times new roman",12,"bold"),height="2",width="8",command=submit)
btn.place(x=760,y=400)

mainloop()
