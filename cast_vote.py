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

finger_sensor_port = "COM6"
gsm_port = "COM5"

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


print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

name_list =[]
ok = False
avg_name = ""

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

def write_read(x):
    gsm.write(str.encode(x))
    time.sleep(0.05)
    data = gsm.readline()
    print(data)
    
def verify_otp():
	mycursor = mydb.cursor()
	mycursor.execute("SELECT * FROM voters_list WHERE name=" + "'" + name + "'")

	myresult = mycursor.fetchall()

	row_count = mycursor.rowcount
	print("number of affected rows: {}".format(row_count))
	if row_count == 0:
		print("Name not registered")

	for row in myresult:
		db_otp = row[3]
		# Now print fetched result

	print(db_otp)

	user_otp = input("Enter OTP: ")
	if(str(user_otp) == db_otp):
		print("otp matched")
	else:
		print("otp not matched")

def send_otp():
	a = random.randrange(1, 10, 2)
	b = random.randrange(1, 10, 2)
	c = random.randrange(1, 10, 1)
	d = random.randrange(1, 10, 4)
	e = str(eval(f"{a}{b}{c}{d}"))
	print(e)
	write_read("AT\n")
	time.sleep(1)
	write_read("AT+CMGF=1\r\n")
	time.sleep(1)
	# write_read("AT+CMGS=\"+918105660919\"\r\n")
	command = "AT+CMGS=\"{}\"\r\n".format(mobile)
	write_read(command)
	time.sleep(1)
	write_read("You OTP is {}".format(e))
	time.sleep(1)
	gsm.write(b'\x1A')
	time.sleep(0.05)

	data = gsm.readline()
	print(data)

	mycursor = mydb.cursor()

	mycursor.execute("UPDATE voters_list SET otp = " + "'" + e + "'" + "WHERE name=" + "'" + name + "'")
	mydb.commit()
	row_count = mycursor.rowcount
	if row_count == 0:
		print("Error in otp")
	else:
		print("OTP updated")
	mycursor.close()
	time.sleep(2)
	verify_otp()

def verify_finger(match_id):
	if(str(match_id)==finger_id):
		print("You can cast the vote")
		send_otp()
	else:
		print("finger od doesn't match with the database")

def check_finger():
	while True:
		response = search(finger=finger, page_id=1, page_num=255)
		if response:
			id, confidence = response
			if(confidence=="Not found"):
				print("invalid")
			else:
				print(f'Found ID #{id}', end='')
				print(f' with confidence of {confidence}\n')
				verify_finger(id)
				break

def fetch_details(name):
	global finger_id,mobile
	mycursor = mydb.cursor()
	mycursor.execute("SELECT * FROM voters_list WHERE name=" + "'" + name + "'")

	myresult = mycursor.fetchall()

	row_count = mycursor.rowcount
	print("number of affected rows: {}".format(row_count))
	if row_count == 0:
		print("Name not registered")

	for row in myresult:
		finger_id = row[5]
		mobile = row[6]

	print("Finger ID: ", finger_id)
	print("Mobile: ", mobile)

	if(finger_id!=""):
		if(mobile!=""):
			print("You can cast the vote")
			check_finger()
		else:
			print("Mobile number not registered")
	else:
		print("Finger ID not registered")
	

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
				fetch_details(avg_name)
			break
			
	else:
		print("More than 2 faces")

	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	if key == ord("q"):
		break

cv2.destroyAllWindows()
vs.stop()