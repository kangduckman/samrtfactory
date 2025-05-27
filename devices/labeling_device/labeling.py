# devices/labeling_flask.py
from flask import Flask
import threading, requests, random, time
from datetime import datetime

app = Flask(__name__)

DEVICE_NAME = "labeling"
SERVER_URL = "http://10.1.2.173:5000/data"

NORMAL_MIN = 0.45
NORMAL_MAX = 0.6
ABNORMAL_MIN = 0.61
ABNORMAL_MAX = 0.7

STEP = 0.01
SEND_INTERVAL = 1
ERROR_PROBABILITY = 0.01  # 에러 발생 확률 낮춤
CHECK_INTERVAL = 5  # 에러 진입 시도 주기 제한

def send_value(val):
    payload = {
        "device": DEVICE_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "value": round(val, 3)
    }
    print(f"[→] 송신: {payload}")
    try:
        requests.post(SERVER_URL, json=payload)
    except Exception as e:
        print(f"[X] 전송 실패: {e}")

def sensor_loop():
    current = random.uniform(NORMAL_MIN, NORMAL_MAX)
    error_mode = False
    error_count = 0
    target_error_count = 0
    direction = 1
    check_counter = 0

    while True:
        check_counter += 1

        # 에러 진입 판단
        if not error_mode and check_counter % CHECK_INTERVAL == 0:
            if random.random() < ERROR_PROBABILITY:
                error_mode = True
                target_error_count = random.choices(
                    [random.randint(1, 2), 20], weights=[0.6, 0.4])[0]
                error_count = 0
                direction = 1
                print(f"[!] 이상 상태 진입: {target_error_count}회 이상값 전송 예정")

        if error_mode:
            current += STEP * direction
            if current > ABNORMAL_MAX:
                direction = -1
                current = ABNORMAL_MAX
            elif current < ABNORMAL_MIN:
                direction = 1
                current = ABNORMAL_MIN

            send_value(current)
            error_count += 1
            if error_count >= target_error_count:
                error_mode = False
                print("[✔] 이상 상태 종료 후 정상 복귀")
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
                glitch = round(random.uniform(NORMAL_MAX + 0.01, NORMAL_MAX + 0.03), 3)
                send_value(glitch)
            else:
                send_value(current)

        time.sleep(SEND_INTERVAL)

@app.route('/')
def home():
    return "Labeling simulator is running.", 200

if __name__ == '__main__':
    threading.Thread(target=sensor_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
