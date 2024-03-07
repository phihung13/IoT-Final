import socket, json, struct, requests
import time
from urllib import request, parse
import paho.mqtt.client as mqtt

from grove.display.jhd1802 import JHD1802 as LCD
from grove.grove_4_digit_display import Grove4DigitDisplay
from seeed_dht import DHT
from gpiozero import LED

Led1 = LED(5)
Led2 = LED(16)
display = Grove4DigitDisplay(12, 13)
lcd = LCD()
sensor_dht = DHT('11', 18)

sw1= None
sw2= None
server_ip = '0.0.0.0'
server_port = 20000
total_humi = 0
total_temp = 0
total_mois = 0
total_sonic = 0
total_rotaly = 0
count = 0
avg_humi = 0
avg_temp = 0
avg_mois = 0
avg_sonic = 0
avg_rotaly = 0

prev_led1 = None
prev_led2 = None
prev_servo = None
prev_sw1 = None
prev_sw2 = None
prev_lcd = ""
lcd.write("on")

def makeParamThingspeak(humi, temp):
    params = parse.urlencode({'field1': humi, 'field2': temp}).encode()
    return params

def thingspeakPost(params):
    apiKeyWrite = "VH7RW35C0KBKR3S3"
    req = request.Request('https://api.thingspeak.com/update', data=params, method="POST")
    req.add_header("X-THINGSPEAKAPIKEY", apiKeyWrite)
    r = request.urlopen(req)
    response_data = r.read()
    return response_data

def getled1():
    api_key_read = "567YU3VFWUUYFSTM"
    channel_ID = "2250527"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/1/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field1 = response_data['field1']
    return field1

def getled2():
    api_key_read = "567YU3VFWUUYFSTM"
    channel_ID = "2250527"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/2/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field2 = response_data['field2']
    return field2

def getservo():
    api_key_read = "567YU3VFWUUYFSTM"
    channel_ID = "2250527"

    req = request.Request("https://api.thingspeak.com/channels/%s/fields/3/last.json?api_key=%s" % (channel_ID, api_key_read), method="GET")
    r = request.urlopen(req)
    response_data = r.read().decode()
    response_data = json.loads(response_data)
    field3 = response_data['field3']
    return field3


def getLora():
    url1 = "https://phihung.serveo.net/data/field11"
    url2 = "https://phihung.serveo.net/data/field12"

    try:
        response1 = requests.get(url1)
        response2 = requests.get(url2)

        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()

            sw1 = data1.get('field11')
            sw2 = data2.get('field12')

            return sw1, sw2
        else:
            print(f"Lỗi khi truy cập API. Mã trạng thái URL 1: {response1.status_code}, Mã trạng thái URL 2: {response2.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối tới API: {e}")

def getLCD():
    url = "https://phihung.serveo.net/data/field9"
    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            lcd = data.get('field9')
            return lcd
        else:
            print(f"Lỗi khi truy cập API. Mã trạng thái : {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối tới API: {e}")

def post_data(data_dict):
    url = "https://phihung.serveo.net/update_post?api_key=ABC"

    response_data = {}
    for field_name, value in data_dict.items():
        data = {field_name: value}
        response = requests.post(url, json=data)
        print(response.json())
        response_data[field_name] = response.json()
    return response_data

def send_control_signal(signal_byte):
    control_signal = struct.pack('>H', signal_byte)
    client_socket.send(control_signal)
    print("đã gửi servo")
##########################################################################
def on_connect(client, userdata, flags, rc):
    print("Connected with Result Code: " + str(rc))
    client.subscribe("lcd")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    print(f"Received message on topic '{topic}': {payload}")

try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(1)
    print("================================================")
    print(f"||  Đang lắng nghe kết nối trên cổng {server_port}... ||")
    print("================================================")
    client_socket, client_address = server_socket.accept()
    print(f"Kết nối từ {client_address[0]}:{client_address[1]} đã được thiết lập.")
except Exception as e:
    print(f"Lỗi khi thiết lập máy chủ: {e}")
try:
    received_handshake = client_socket.recv(1024).decode()
    if received_handshake == "Up":
        handshake_message = "Handshake OK"
        client_socket.send(handshake_message.encode())
        received_ok = client_socket.recv(1024).decode()
        client = mqtt.Client("nhom1")
        client.loop_start()
        if received_ok == "OK":
            while True:
                try:
                    client.on_connect = on_connect
                    client.on_message = on_message
                    client.username_pw_set(username="phihung", password="phihung")
                    client.connect("192.168.1.28", 1883, 60)
                    print("đang nghe data của moi,sonic,rotary")
                    data = client_socket.recv(1024)
                    print(f"data = {data}")
                    if len(data) >= 5:
                        start_byte, id_byte, cmd_byte, length_byte, crc_byte = struct.unpack('BBBBB', data[:5])
                        received_data = data[5:-1]
                        stop_byte = data[-1]
                        data_crc = sum(received_data) & 0xFF
                        if (start_byte == 100) and (id_byte == 60) and (cmd_byte == 1) and (data_crc == crc_byte) and (stop_byte == 200):
                            moisture, sonic, rotaly = struct.unpack('III', received_data)

                            humi, temp = sensor_dht.read()
                            print(f" Sensor : Nhiệt độ: {temp} °C, Độ ẩm: {humi} %")
                            print(f"          Moisture: {moisture}, Sonic: {sonic}, Rotaly: {rotaly}")

                            total_humi += humi
                            total_temp += temp
                            total_mois += moisture
                            total_sonic += sonic
                            total_rotaly += rotaly
                            count = count + 1
                            print("==============================")
                            print(f"|         Lần thứ {count}          |")
                            print("==============================")

                            value_led1 = getled1()
                            value_led2 = getled2()
                            value_servo = getservo()
                            print("đang nghe data của sw1 sw2")
                            data1 = client_socket.recv(1024)
                            if len(data1) >= 2:
                                sw1, sw2 = struct.unpack('>BB', data1[:2])
                            else:
                                print(f"Data SW = {data1}")
                            if sw1 != prev_sw1 or sw2 != prev_sw2:
                                data_dict = {
                                    "field11": int(sw1),
                                    "field12": int(sw2),
                                    "field13": int(sw1),
                                    "field14": int(sw2)
                                }
                                prev_sw1 = sw1
                                prev_sw2 = sw2
                                response_data = post_data(data_dict)
                                print(f"sw1 = {sw1}, sw2 = {sw2}")
                            value_lcd = getLCD()
                            if str(value_lcd) != prev_lcd:
                                lcd.clear()
                                lcd.setCursor(0, 0)
                                lcd.write(f"{str(value_lcd)}")
                                prev_lcd = value_lcd
                                print("lcd lên")
                            print(f" Hiển thị LCD: {str(value_lcd)}")
                            t = time.strftime("%H%M", time.localtime(time.time()))
                            display.show(t)
                            print(f" Hiển thị 4 Digit Display: {t}")
                            if value_led1 == '1':
                                print(" Điều khiển: Led 1 on")
                                Led1.on()
                            else:
                                Led1.off()
                                print(" Điều khiển: Led 1 off")
                            if value_led2 == '1':
                                Led2.on()
                                print("             Led 2 on")
                            else:
                                Led2.off()
                                print("             Led 2 off")

                            if value_led1 != prev_led1 or value_led2 != prev_led2 or value_servo != prev_servo:
                                data_dict = {
                                    "field1": int(value_led1),
                                    "field2": int(value_led2),
                                    "field3": int(value_servo)
                                }
                                response_data = post_data(data_dict)
                                prev_led1 = value_led1
                                prev_led2 = value_led2
                                prev_servo = value_servo
                            if value_servo:
                                print(" To client:  Tín hiệu servo:", value_servo)
                                send_control_signal(int(value_servo))
                            if count == 10:
                                print("Gửi giá trị trung bình lên server...")
                                print("************************************")
                                avg_humi = total_humi / 10
                                avg_temp = total_temp / 10
                                avg_mois = total_mois / 10
                                avg_sonic = total_sonic / 10
                                avg_rotaly = total_rotaly / 10
                                data_dict = {
                                    "field4": int(avg_temp),
                                    "field5": int(avg_humi),
                                    "field6": int(avg_rotaly),
                                    "field7": int(avg_mois),
                                    "field8": int(avg_sonic),
                                    "field10": str(t),
                                }
                                params_thingspeak = makeParamThingspeak(humi, temp)
                                data = thingspeakPost(params_thingspeak)
                                response_data = post_data(data_dict)
                                print("************************************")
                                print("******** Đã gửi lên server *********")
                                print("************************************")
                                total_humi = 0
                                total_temp = 0
                                total_mois = 0
                                total_sonic = 0
                                total_rotaly = 0
                                count = 0
                                send_control_signal(int(value_servo))
                except Exception as e:
                    print(f"Lỗi trong vòng lặp chính: {e}")
                    time.sleep(3)
        else:
            print("Lỗi trong quá trình bắt tay.")
            time.sleep(3)
except Exception as e:
    print(f"Lỗi chung: {e}")
    time.sleep(3)
finally:
    client_socket.close()
