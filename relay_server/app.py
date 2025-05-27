from flask import Flask, request, jsonify
#import pymysql
from datetime import datetime
import time

app = Flask(__name__)

'''# DB 연결 설정
db_config = {
    "host": "localhost",  # AWS 이식할 때 교체
    "password": "your_password",
    "database": "smart_factory",
    "charset": "utf8mb4",
    "autocommit": True
}'''

# 디바이스 정상 범위 및 연속 이상 판단 기준
DEVICE_CONFIG = {
    "washer":   {"normal_min": 55,   "normal_max": 65,   "threshold_count": 5},
    "charger":  {"normal_min": 2.0,  "normal_max": 2.1,  "threshold_count": 2},
    "capper":   {"normal_min": 0.85, "normal_max": 1.1,  "threshold_count": 3},
    "labeling": {"normal_min": 0.45, "normal_max": 0.6,  "threshold_count": 3}
}

# 디바이스 상태 메모리 저장소
device_state = {}

'''# DB에 로그 저장
def insert_device_log(device, value, status):
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO device_logs (device_id, value, status, log_time)
                VALUES (
                    (SELECT id FROM devices WHERE device_name = %s),
                    %s, %s, %s
                )
            """
            cursor.execute(sql, (device, value, status, datetime.now()))
    finally:
        conn.close()

# 장기 이상 발생 시 수리 이력 기록
def insert_repair_event(device, abnormal_count):
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO repair_events (device_id, start_time, end_time, abnormal_count, details)
                VALUES (
                    (SELECT id FROM devices WHERE device_name = %s),
                    %s, %s, %s, %s
                )
            """
            now = datetime.now()
            details = f"{abnormal_count}회 연속 이상 → 수리"
            cursor.execute(sql, (device, now, now, abnormal_count, details))
    finally:
        conn.close()
'''
@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    device = data["device"]
    value = data["value"]
    now = time.time()

    print(f"[📦] 수신된 원시 데이터: {data}")

    config = DEVICE_CONFIG.get(device)
    if not config:
        return jsonify({"error": "unknown device"}), 400

    if device not in device_state:
        device_state[device] = {
            "abnormal_count": 0,
            "consecutive_abnormal": 0,
            "in_long_error": False,
            "long_error_counter": 0
        }

    state = device_state[device]
    is_normal = config["normal_min"] <= value <= config["normal_max"]

    #insert_device_log(device, value, "normal" if is_normal else "abnormal")

    if state["in_long_error"]:
        state["long_error_counter"] += 1
        print(f"[💥] {device}: 장기 이상 유지 중 {state['long_error_counter']}회 → {value}")
        if state["long_error_counter"] >= 20:
            print(f"[🛠] {device}: 수리 완료. 정상 복귀")
            #insert_repair_event(device, state["consecutive_abnormal"])
            state.update({
                "abnormal_count": 0,
                "consecutive_abnormal": 0,
                "in_long_error": False,
                "long_error_counter": 0
            })
    else:
        if is_normal:
            if state["consecutive_abnormal"] > 0:
                print(f"[↘] {device}: 정상값 복귀 → {value}")
            state["consecutive_abnormal"] = 0
        else:
            state["abnormal_count"] += 1
            state["consecutive_abnormal"] += 1
            print(f"[!] {device}: 이상값 감지 → {value} (연속 {state['consecutive_abnormal']}회)")

            if state["consecutive_abnormal"] >= config["threshold_count"]:
                print(f"[⚠] {device}: 연속 이상으로 장기 이상 상태 진입")
                state["in_long_error"] = True
                state["long_error_counter"] = 1

    return jsonify({"status": "received"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)