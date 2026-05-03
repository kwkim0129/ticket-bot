import os
import time
import threading
import requests
import schedule
import datetime
from flask import Flask

app = Flask(__name__)

URL = 'https://flight.naver.com/flights/domestic/GMP:airport-CJU:airport-20260430?adult=1&fareType=YC'

DEPART = "GMP"   # 김포
ARRIVE = "CJU"   # 제주
DEPART_DATE = "20260503" # today 
RETURN_DATE = None   # 왕복이면 "20260502"

USER_AGENT = {'User-Agent': 'Mozilla/5.0'}
KAKAO_TOKEN = os.getenv('KAKAO_TOKEN')
CHECK_MINUTES = int(os.getenv('CHECK_MINUTES', '2'))

last_alert_sent = False

@app.route("/")
def home():
    return "Jeju ticket bot running"

def build_flight_url(depart, arrive, depart_date, return_date=None):
    base = "https://flight.naver.com/flights/"

    if return_date:
        path = f"{depart}:city-{arrive}:airport-{depart_date}/{arrive}:airport-{depart}:city-{return_date}"
    else:
        path = f"{depart}:city-{arrive}:airport-{depart_date}"

    query = "?adult=1&fareType=YC&isDirect=false"

    return base + path + query

import json

def send_kakao(message, link_url):
    api = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    headers = {'Authorization': f'Bearer {KAKAO_TOKEN}'}

    template = {
        "object_type": "text",
        "text": message,
        "link": {
            "web_url": link_url,
            "mobile_web_url": link_url
        }
    }

    data = {
        "template_object": json.dumps(template)
    }

    r = requests.post(api, headers=headers, data=data)
    print(r.text)

def check_ticket():
    global last_alert_sent
    try:
        check_url = build_check_url(DEPART, ARRIVE, DEPART_DATE)
        r = requests.get(check_url, headers=USER_AGENT, timeout=20)
        html = r.text


        soldout_keywords = ['매진', '예약마감']
        available = not any(x in html for x in soldout_keywords)

        print("Checked:", available)

        if available and not last_alert_sent:
            url = build_flight_url("SEL", "CJU", "20260524", "20260526")

            send_kakao(
                "🚨 김포→제주 취소표 가능성 발견! 지금 확인하세요",
                notify_url
            )
            last_alert_sent = True

        if not available:
            last_alert_sent = False

    except Exception as e:
        print(e)

def bot_loop():
    schedule.every(CHECK_MINUTES).minutes.do(check_ticket)
    check_ticket()

    send_kakao("✅ 테스트 메시지")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
