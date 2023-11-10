import socket
import struct
import time
import random

# from gpiozero import LED
# from seeed_dht import DHT

# led = LED(5)
# sensor = DHT('11', 12)

# Lưu trữ giá trị servo trước đó
previous_servo_value = None

server_ip = '192.168.1.234'
server_port = 20000

def process_sw1(sw1):
    if sw1 == 1:
        print("Nhận được tín hiệu điều khiển: Đèn bật")
    else:
        print("Nhận được tín hiệu điều khiển: Đèn tắt")

def process_sw2(sw2):
    if sw2 == 1:
        print("Nhận được tín hiệu điều khiển: Đèn báo bật")
    else:
        print("Nhận được tín hiệu điều khiển: Đèn báo tắt")

def process_servo(servo_value):
    global previous_servo_value
    if servo_value != previous_servo_value:
        print(f"Nhận được tín hiệu điều khiển: Servo quay {servo_value} độ")
        previous_servo_value = servo_value

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
                # humidity, temperature = sensor.read()
                moisture = random.randint(80, 95)
                sonic = random.randint(100, 3000)
                rotaly = random.randint(0, 360)
                print('Moisture {}, Sonic {}, Rotaly {}'.format(moisture, sonic, rotaly))

                if moisture is not None and rotaly is not None and sonic is not None:
                    data = (int(moisture), int(sonic), int(rotaly))
                    data_byte = struct.pack('HHB', *data)
                    length_byte = len(data_byte)
                    stop_byte = 200
                    data_crc = sum(data_byte) & 0xFF

                    packet = struct.pack('BBBBB', 100, 60, 1, length_byte, data_crc)
                    packet += data_byte
                    packet += struct.pack('B', stop_byte)
                    client_socket.send(packet)
                data1 = client_socket.recv(1024)

                if len(data1) >= 2:
                    sw1, sw2 = struct.unpack('>BB', data1[:2])
                    process_sw1(sw1)
                    process_sw2(sw2)
                    
                    data2 = client_socket.recv(1024)
                    servo_value = struct.unpack('>H', data2)[0]
                    process_servo(servo_value)
                else:
                    print("Lỗi khi đọc dữ liệu")
        else:
            print("Lỗi trong quá trình bắt tay.")

    except Exception as e:
        print(f"Lỗi khi kết nối, đang chờ kết nối lại...")
        time.sleep(5)
    finally:
        client_socket.close()