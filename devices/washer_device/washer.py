# devices/washer_flask.py
from flask import Flask
import threading, requests, random, time
from datetime import datetime

app = Flask(__name__)

DEVICE_NAME = "washer"
SERVER_URL = "ip-10-1-2-173.us-east-2.compute.internal"

NORMAL_MIN = 55
NORMAL_MAX = 65
ABNORMAL_MIN = 65.5
ABNORMAL_MAX = 68

STEP = 0.5
SEND_INTERVAL = 1
ERROR_PROBABILITY = 0.01

def send_value(val):
    payload = {
        "device": DEVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "value": round(val, 2)
    }
    print(f"[→] 송신: {payload}")
    try:
        requests.post(SERVER_URL, json=payload)
    except:
        print("[X] 전송 실패")

def sensor_loop():
    current = random.uniform(NORMAL_MIN, NORMAL_MAX)
    err_mode = False
    err_count = 0
    target_err_count = 0
    direction = 1

    while True:
        if not err_mode and random.random() < ERROR_PROBABILITY:
            err_mode = True
            target_err_count = random.choices([random.randint(1, 2), 20], weights=[0.6, 0.4])[0]
            err_count = 0
            direction = 1
            print(f"[!] 이상 상태 진입: {target_err_count}회")

        if err_mode:
            current += STEP * direction
            if current > ABNORMAL_MAX:
                direction = -1
                current = ABNORMAL_MAX
            elif current < ABNORMAL_MIN:
                direction = 1
                current = ABNORMAL_MIN

            send_value(current)
            err_count += 1
            if err_count >= target_err_count:
                err_mode = False
                print("[✔] 이상 종료 후 정상 복귀")
                current = NORMAL_MAX
        else:
            current += STEP * direction
            if current > NORMAL_MAX:
                direction = -1
                current = NORMAL_MAX
            elif current < NORMAL_MIN:
                direction = 1
                current = NORMAL_MIN

            if random.random() < 0.02:
                send_value(round(random.uniform(NORMAL_MAX + 0.1, NORMAL_MAX + 0.4), 2))
            else:
                send_value(current)
        time.sleep(SEND_INTERVAL)

@app.route('/')
def home():
    return "Washer simulator is running.", 200

if __name__ == '__main__':
    threading.Thread(target=sensor_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)