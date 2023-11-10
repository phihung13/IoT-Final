import socket, json, struct, requests
import random, time
from urllib import request, parse
import paho.mqtt.client as mqtt
# from grove.display.jhd1802 import JHD1802
#from grove.grove_4_digit_display import Grove4DigitDisplay
#display = Grove4DigitDisplay(12,13)
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
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_socket.bind((server_ip, server_port))
    server_socket.listen(1)
    print("================================================")
    print(f"||  Đang lắng nghe kết nối trên cổng {server_port}... ||")
    print("================================================")
    client_socket, client_address = server_socket.accept()
    print(f"Kết nối từ {client_address[0]}:{client_address[1]} đã được thiết lập.")
except Exception as e:
    print(f"Lỗi khi thiết lập máy chủ: {e}")

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

def getbuzzer():
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

def send_lora_packet(sw1, sw2):
    packet = struct.pack('>BB', sw1, sw2)
    client_socket.send(packet)
##########################################################################
def on_connect(client, userdata, flags, rc):
    print("Connected with Result Code: " + str(rc))
    client.subscribe("lora")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    print(f"Received message on topic '{topic}': {payload}")
    
def update_lamp_data(lamp):
    data = {
        "field13": int(lamp)
    } 
    json_data = json.dumps(data)
    print(json_data)
    client.publish("gateway", json_data)
def update_siren_data(siren):
    data = {
        "field14": int(siren)
    } 
    json_data = json.dumps(data)
    print(json_data)
    client.publish("gateway", json_data)
##########################################################################
try:
    received_handshake = client_socket.recv(1024).decode()
    if received_handshake == "Up":
        handshake_message = "Handshake OK"
        client_socket.send(handshake_message.encode())
        received_ok = client_socket.recv(1024).decode()
        client = mqtt.Client()
        client.loop_start()
        if received_ok == "OK":
            while True:
                try:
                    client = mqtt.Client('Nhom1')
                    client.on_connect = on_connect
                    client.on_message = on_message
                    client.username_pw_set(username="phihung", password="phihung")
                    client.connect("192.168.1.234", 1883, 60)
                    data = client_socket.recv(1024)
                    if len(data) >= 5:
                        start_byte, id_byte, cmd_byte, length_byte, crc_byte = struct.unpack('BBBBB', data[:5])
                        received_data = data[5:-1]
                        stop_byte = data[-1]
                        data_crc = sum(received_data) & 0xFF
                        if (start_byte == 100) and (id_byte == 60) and (cmd_byte == 1) and (data_crc == crc_byte) and (stop_byte == 200):
                            moisture, sonic, rotaly = struct.unpack('III', received_data)

                            humi = random.randint(80, 95)
                            temp = random.randint(25, 45)
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
                            value_servo = getbuzzer()
                            sw1, sw2 = getLora()
                            if sw1 != prev_sw1 or sw2 != prev_sw2:
                                update_lamp_data(int(sw1))
                                update_siren_data(int(sw2))
                                prev_sw1 = sw1
                                prev_sw2 = sw2
                            lora_packet = send_lora_packet(sw1, sw2)
                            value_lcd = getLCD()
                            print(f" Hiển thị LCD: {str(value_lcd)}")
                            t = time.strftime("%H%M", time.localtime(time.time()))
                            print(f" Hiển thị 4 Digit Display: {t}")
                            # lcd.clear()
                            # lcd.setCursor(1,0)
                            # lcd.write("{}".format(value_lcd))
                            if value_led1 == '1':
                                # Led1.on()
                                print(" Điều khiển: Led 1 on")
                            else:
                                # Led1.off()
                                print(" Điều khiển: Led 1 off")
                            if value_led2 == '1':
                                # Led2.on()
                                print("             Led 2 on")
                            else:
                                # Led2.off()
                                print("             Led 2 off")
                            if value_servo:
                                print(" To client:  Tín hiệu servo:", value_servo)
                                send_control_signal(int(value_servo))

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
                            if count == 20:
                                print("Gửi giá trị trung bình lên server...")
                                print("************************************")
                                avg_humi = total_humi / 20
                                avg_temp = total_temp / 20
                                avg_mois = total_mois / 20
                                avg_sonic = total_sonic / 20
                                avg_rotaly = total_rotaly / 20
                                data_dict = {
                                    "field4": int(avg_temp),
                                    "field5": int(avg_humi),
                                    "field6": int(avg_rotaly),
                                    "field7": int(avg_mois),
                                    "field8": int(avg_sonic),
                                    "field10": str(t),
                                }
                                params_thingspeak = makeParamThingspeak(humi, temp)  # Server thingspeak
                                data = thingspeakPost(params_thingspeak)

                                response_data = post_data(data_dict)  # Server riêng
                                print("************************************")
                                print("******** Đã gửi lên server *********")
                                print("************************************")
                                total_humi = 0
                                total_temp = 0
                                total_mois = 0
                                total_sonic = 0
                                total_rotaly = 0
                                count = 0
                except Exception as e:
                    print(f"Lỗi trong vòng lặp chính: {e}")
                    time.sleep(3)
        else:
            print("Lỗi trong quá trình bắt tay.")
            time.sleep(3)
except Exception as e:
    print(f"Lỗi chung: {e}")
    time.sleep(3)