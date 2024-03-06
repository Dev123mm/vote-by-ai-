import serial
import sys
gsm_port = "COM7"
import time     
mobile="+917204310710"
e=2
try:
	gsm = serial.Serial(gsm_port, baudrate=9600, timeout=5)
except Exception as e:
	print("Please check GSM module com port")
	print(e)
	sys.exit()
def write_read(x):
    gsm.write(str.encode(x))
    time.sleep(0.05)
    data = gsm.readline()
    print(data)

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
