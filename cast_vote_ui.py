from imutils.video import VideoStream
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2
from statistics import mode
import mysql.connector
import serial
from adafruit_fingerprint import AdafruitFingerprint
from adafruit_fingerprint.responses import *
import sys
import random
from tkinter import *
from tkinter import messagebox
#from tkinter.ttk import *

import tkinter as tk
from tkinter import PhotoImage
from PIL import Image


root = Tk()
root.geometry("1700x800")

otp_var= StringVar()

finger_sensor_port = "COM6"
gsm_port = "COM7"

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="vote_fp"
)

ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=False,default="encodings.pickle",
	help="path to serialized db of facial encodings")
ap.add_argument("-o", "--output", type=str,
	help="path to output video")
ap.add_argument("-y", "--display", type=int, default=1,
	help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
	help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

print("[INFO] loading encodings...")
data = pickle.loads(open(args["encodings"], "rb").read())

# name = "Unknown"

try:
	baud_rate = '57600'
	serial_port = serial.Serial(finger_sensor_port, baud_rate)
except Exception as e:
	print("Please check fingerprint sensor com port")
	print(e)
	sys.exit()

try:
	gsm = serial.Serial(gsm_port, baudrate=9600, timeout=5)
except Exception as e:
	print("Please check GSM module com port")
	print(e)
	sys.exit()

finger = AdafruitFingerprint(port=serial_port)

response = finger.vfy_pwd()
if response is not FINGERPRINT_PASSWORD_OK:
	print('Did not find fingerprint sensor :(')
	sys.exit()
print('Found Fingerprint Sensor!\n')

def search(finger, page_id, page_num):
    # Buffer constants
    CHAR_BUFF_1 = 0x01
    CHAR_BUFF_2 = 0x02

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
            return False
        elif response is FINGERPRINT_IMAGEFAIL:
            print('Imaging Error')
            return False
        else:
            print('Unknown Error')
            return False

    response = finger.img_2Tz(buffer=CHAR_BUFF_1)
    if response is FINGERPRINT_OK:
        print('Image Converted')
        sys.stdout.flush()
    elif response is FINGERPRINT_IMAGEMESS:
        print('Image too messy')
        return False
    elif response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error')
        return False
    elif response is FINGERPRINT_FEATUREFAIL:
        print('Could not find fingerprint features')
        return False
    elif response is FINGERPRINT_INVALIDIMAGE:
        print('Could not find fingerprint features')
        return False
    else:
        print('Unknown Error')
        return False

    response = finger.search(
        buffer=CHAR_BUFF_1, page_start=page_id, page_num=page_num)
    if isinstance(response, tuple) and len(response) == 3 and response[0] is FINGERPRINT_OK:
        print('Found a print match!\n')
        return response[1], response[2]
    if response is FINGERPRINT_PACKETRECEIVER:
        print('Communication error\n')
        return False
    if response is FINGERPRINT_NOTFOUND:
        print('Did not find a match\n')
        return True,"Not found"

__all__ = ['search']

def go_back(back,present):
    back.deiconify()
    present.destroy()

def write_read(x):
    gsm.write(str.encode(x))
    time.sleep(0.05)
    data = gsm.readline()
    print(data)

def vote():
	global candidate,name,userWindow,voteWindow
	selected = candidate.get()

	mycursor = mydb.cursor()
	mycursor.execute("SELECT * FROM candidate WHERE name=" + "'" + selected + "'")

	myresult = mycursor.fetchall()

	row_count = mycursor.rowcount
	print("number of affected rows: {}".format(row_count))
	if row_count == 0:
		print("Name not registered")

	for row in myresult:
		vote_count = row[2]
		# Now print fetched result

	# print(vote_count)

	vote_count=int(vote_count)
	vote_count+=1
	
	# mycursor = mydb.cursor()
	# print(name)
	mycursor.execute("UPDATE candidate SET vote_count = " + "'" + str(vote_count) + "'" + "WHERE name=" + "'" + selected + "'")
	mydb.commit()
	row_count = mycursor.rowcount
	if row_count == 0:
		print("Error in VOTING")
	else:
		print("Vote registered Successfully")
		time.sleep(2)

	
	mycursor.execute("UPDATE voters_list SET status = 'yes' WHERE name=" + "'" + name + "'")
	mydb.commit()
	row_count = mycursor.rowcount
	if row_count == 0:
		print("Error in updating status")
	else:
		print("Status updated Successfully")
	
	messagebox.showinfo("Vote", "Vote Recorded Successfully")
	mycursor.close()
	root.deiconify()
	voteWindow.destroy()
	
	


def candidate_list():
	global userWindow,candidate,voteWindow
	userWindow.withdraw()
	voteWindow = Toplevel(root)
	voteWindow.title("Candidate List")
	voteWindow.geometry("1700x800")
	candidate = StringVar(value="Blue")
	Radiobutton(voteWindow, text="Blue", variable=candidate, value="Blue").place(x=675, y=50)
	Radiobutton(voteWindow, text="Red", variable=candidate, value="Red").place(x=675, y=100)
	Radiobutton(voteWindow, text="Green", variable=candidate, value="Green").place(x=675, y=150)

	Label(voteWindow, text='ELECTION COMISSION GOVT OF INDIA 23-24',bg="orange",fg="black",font=('times new roman', 10, 'bold')).place(x=675, y=25)


	Button(voteWindow, text='Submit', command=vote).place(x=675, y=200)


def verify_otp():
	global avg_name
	otp = otp_var.get()
	mycursor = mydb.cursor()
	mycursor.execute("SELECT * FROM voters_list WHERE aadhar=" + "'" + avg_name + "'")

	myresult = mycursor.fetchall()

	row_count = mycursor.rowcount
	print("number of affected rows: {}".format(row_count))
	if row_count == 0:
		print("Name not registered")

	for row in myresult:
		db_otp = row[2]
		# Now print fetched result

	print(db_otp)

	# user_otp = input("Enter OTP: ")
	if(str(otp) == db_otp):
		print("otp matched")
		messagebox.showinfo("OTP", "OTP Verified")
		candidate_list()
	else:
		print("otp not matched")
		messagebox.showinfo("OTP", "OTP not matched")
    
def verify_otp_window():
	global userWindow
	root.withdraw()
	userWindow = Toplevel(root)
	userWindow.title("OTP Verification")
	userWindow.geometry("1700x800")

	Label(userWindow, text='OTP', font=('calibre', 10, 'bold')).place(x=675, y=100)
	Entry(userWindow, textvariable=otp_var, font=('calibre', 10, 'normal')).place(x=800, y=100)

	Button(userWindow, text='Submit', command=verify_otp).place(x=775, y=150)

	Button(userWindow, text='Go back', command=lambda: go_back(root,userWindow)).place(x=850, y=150)
	

def send_otp():
	a = random.randrange(1, 10, 2)
	b = random.randrange(1, 10, 2)
	c = random.randrange(1, 10, 1)
	d = random.randrange(1, 10, 3)
	e = str(eval(f"{a}{b}{c}{d}"))
	print(e)
	write_read("AT\n")
	time.sleep(1)
	write_read("AT+CMGF=1\r\n")
	time.sleep(1)
	command = "AT+CMGS=\"{}\"\r\n".format(mobile)
	write_read(command)
	time.sleep(1)
	write_read("You OTP is {}".format(e))
	time.sleep(1)
	gsm.write(b'\x1A')
	time.sleep(0.05)

	data = gsm.readline()
	print(data)

	messagebox.showinfo("OTP", "OTP sent")
	mycursor = mydb.cursor()
	print(name)
	mycursor.execute("UPDATE voters_list SET otp = " + "'" + e + "'" + "WHERE name=" + "'" + name + "'")
	mydb.commit()
	row_count = mycursor.rowcount
	if row_count == 0:
		print("Error in otp")
	else:
		print("OTP updated")
		time.sleep(2)
		verify_otp_window()
	mycursor.close()
	

def verify_finger(match_id):
	if(str(match_id)==finger_id):
		print("You can cast the vote")
		messagebox.showinfo("Fingerprint", "Verified with the database")
		send_otp()
	else:
		print("finger doesn't match with the database")
		messagebox.showinfo("Fingerprint", "Fingerprint did not match with the database")


def check_finger():
	messagebox.showinfo("Fingerprint", "Place your finger on the sensor")
	while True:
		response = search(finger=finger, page_id=1, page_num=255)
		if response:
			id, confidence = response
			if(confidence=="Not found"):
				print("invalid")
				messagebox.showerror("Error", "Invalid finger")
			else:
				messagebox.showinfo("Fingerprint", "Match found, verifying with database")
				print(f'Found ID #{id}', end='')
				print(f' with confidence of {confidence}\n')
				verify_finger(id)
				break

def fetch_details(n):
	global finger_id,mobile,name
	# status="no"
	mycursor = mydb.cursor()
	mycursor.execute("SELECT * FROM voters_list WHERE aadhar=" + "'" + n + "'")

	myresult = mycursor.fetchall()

	row_count = mycursor.rowcount
	print("number of affected rows: {}".format(row_count))
	if row_count == 0:
		print("Name not registered")
		messagebox.showerror("Error", "Name not registered")

		return
	for row in myresult:
		name = row[1]
		finger_id = row[3]
		mobile = row[4]
		status = row[7]
	
	if(status=="yes"):
		messagebox.showerror("Error", "Already casted the vote")
		return

	print("Finger ID: ", finger_id)
	print("Mobile: ", mobile)

	if(finger_id!=""):
		if(mobile!=""):
			print("You can cast the vote")
			check_finger()
		else:
			messagebox.showerror("Error", "Mobile number not registered")
			print("Mobile number not registered")
	else:
		messagebox.showerror("Error", "Finger ID not registered")
		print("Finger ID not registered")
	
def recognize():
	global avg_name
	print("[INFO] starting video stream...")
	vs = VideoStream(src=0).start()
	time.sleep(2.0)
	name_detected=False
	name_list =[]
	ok = False
	avg_name = ""
	while True:
		# grab the frame from the threaded video stream
		frame = vs.read()
		rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		rgb = imutils.resize(frame, width=750)
		r = frame.shape[1] / float(rgb.shape[1])

		boxes = face_recognition.face_locations(rgb,
			model=args["detection_method"])
		encodings = face_recognition.face_encodings(rgb, boxes)
		print(len(encodings))
		names = []
		if(len(encodings)<2):
			# loop over the facial embeddings
			for encoding in encodings:
				# attempt to match each face in the input image to our known
				# encodings
				matches = face_recognition.compare_faces(data["encodings"],
					encoding)
				name = "Unknown"

				if True in matches:
					matchedIdxs = [i for (i, b) in enumerate(matches) if b]
					counts = {}

					for i in matchedIdxs:
						name = data["names"][i]
						counts[name] = counts.get(name, 0) + 1
					name = max(counts, key=counts.get)
				
				# update the list of names
				names.append(name)
				name_list.append(name)

			if(len(name_list)>5):
				name_list=[]
				avg_name=""
				ok =  False

			try:
				if(len(name_list)==5):
					avg_name = mode(name_list)
					ok =  True
			except:
				print("wait")
			# loop over the recognized faces
			for ((top, right, bottom, left), name) in zip(boxes, names):
				# rescale the face coordinates
				top = int(top * r)
				right = int(right * r)
				bottom = int(bottom * r)
				left = int(left * r)

				# draw the predicted face name on the image
				cv2.rectangle(frame, (left, top), (right, bottom),
					(0, 255, 0), 2)
				y = top - 15 if top - 15 > 15 else top + 15
				cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
					0.75, (0, 255, 0), 2)
				
			if ok:
				print(avg_name)
				if(avg_name!="Unknown"):
					messagebox.showinfo("Success","Welcome: "+avg_name+"\nPlease wait while we verify your status")
					name_detected=True
					break
				else:
					messagebox.showerror("Error","Voter not registered")
				break
				
		else:
			print("More than 2 faces")

		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF

		if key == ord("q"):
			break

	cv2.destroyAllWindows()
	vs.stop()
	if name_detected:
		fetch_details(avg_name)


def convert_image(input_path, output_path):
    jpeg_image = Image.open(input_path)
    jpeg_image = jpeg_image.resize((1700, 800), Image.ANTIALIAS)
    jpeg_image.save(output_path, "GIF")


    # Convert the JPEG image to GIF format using PIL
convert_image("5.jpg", "background.gif")  # Replace with your image path

    # Load the background image
bg_image = PhotoImage(file="background.gif")  # Use the converted GIF image

    # Create a label to display the background image
bg_label = tk.Label(root, image=bg_image)
bg_label.place(relwidth=1, relheight=1)  # Cover the entire window



label = Label(root,text="ELECTRONIC VOTING MACHINE POWERED BY AI",fg="white",bg="grey",font=("times new roman",25,"bold"))
label.place(x=400,y=25)

btn = Button(root,text="PRESS THE BUTTON\nFOR VOTING ",bg="orange",fg="black",font=("times new roman",15,"bold"),height="2",width="18",command=recognize)
# btn = Button(root,text="Recognize",command=candidate_list)
btn.place(x=675,y=300)

mainloop()