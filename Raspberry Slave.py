#! /usr/bin/env python3
import sys
sys.path.append('/home/pi/Desktop/truc/IoT-subject/lora/Lora_Driver')

import socket, json, struct, time
from urllib import request

from grove.grove_moisture_sensor import GroveMoistureSensor as gms
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from grove.adc import ADC
from grove.grove_servo import GroveServo
from Lora_Driver.IoT_Driver import mylora

Lora = mylora(verbose=False)
Lora.debug_on = 0
Lora.set_freq(479)

sensor_sonic = GroveUltrasonicRanger(18)
sensor_rotaly=ADC()
getSensor = gms(2)
servo = GroveServo(12)

prev_servo = None
server_ip = '192.168.1.234'
server_port = 20000
num = 0

def getMode():
    api_key_read = "EUK39CTPQTVXKCIU"
    channel_ID = "2342257"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/1/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field1 = response_data['field1']
    return field1
def getSW1():
    api_key_read = "EUK39CTPQTVXKCIU"
    channel_ID = "2342257"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/2/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field2 = response_data['field2']
    return field2
def getSW2():
    api_key_read = "EUK39CTPQTVXKCIU"
    channel_ID = "2342257"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/3/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field3 = response_data['field3']
    return field3
def process_sw1(data):
    sw1 = int(data)
    if sw1 == 1:
        Lora.write_data(1,8,1)
    else:
        Lora.write_data(1,8,0)
def process_sw2(data):
    sw2 = int(data)
    if sw2 == 1:
        Lora.write_data(1,9,1)
    else:
        Lora.write_data(1,9,0)
def process_servo(servo_value):
    global prev_servo
    if servo_value != prev_servo:
        print(servo_value)
        servo.setAngle(servo_value)
        time.sleep(2)
        prev_servo = servo_value
def send_lora_packet(sw1, sw2):
    packet = struct.pack('>BB', sw1, sw2)
    client_socket.send(packet)
    print("đã gửi lên lora packet =",packet)

while True:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        client_socket.send(b'Up')

        received_handshake = client_socket.recv(1024).decode()
        if received_handshake == "Handshake OK":
            client_socket.send(b'OK')
            print("Bắt tay thành công!")
            while True:
                moisture = getSensor.moisture
                sonic = sensor_sonic.get_distance()
                rotaly=sensor_rotaly.read_voltage(0)
                mode = getMode()
                print('Moisture {}, Sonic {}, Rotaly {}'.format(moisture, sonic, rotaly))

                data = (int(moisture), int(sonic), int(rotaly))
                data_byte = struct.pack('III', *data)
                length_byte = len(data_byte)
                stop_byte = 200
                data_crc = sum(data_byte) & 0xFF

                packet = struct.pack('BBBBB', 100, 60, 1, length_byte, data_crc)
                packet += data_byte
                packet += struct.pack('B', stop_byte)
                client_socket.send(packet)
                if int(mode) == 0:
                    print("Lamp and Siren đọc giá trị của node-red")
                    sw1 = getSW1()
                    sw2 = getSW2()
                elif int(mode) == 1:
                    print("Lamp and Siren đọc giá trị của công tắc")
                    sw1 = Lora.read_data(1,4)
                    sw2 = Lora.read_data(1,5)
                process_sw1(sw1)
                process_sw2(sw2)
                print(f"sw1 = {sw1}, sw2 = {sw2}")
                print(f"mode = {mode}")
                lora_packet = send_lora_packet(int(sw1), int(sw2))
                
                data1 = client_socket.recv(1024)
                print(data1)
                servo_value = struct.unpack('>H', data1)[0]
                if servo_value != prev_servo:
                    process_servo(servo_value)
                    prev_servo = servo_value
        else:
            print("Lỗi trong quá trình bắt tay.")

    except Exception as e:
        print(f"Lỗi khi kết nối, đang chờ kết nối lại...")
        time.sleep(5)
    finally:
        client_socket.close()