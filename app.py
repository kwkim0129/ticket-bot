import os
import time
import requests
import schedule

URL = 'https://flight.naver.com/flights/domestic/GMP:airport-CJU:airport-20260430?adult=1&fareType=YC'
USER_AGENT = {'User-Agent': 'Mozilla/5.0'}
KAKAO_TOKEN = os.getenv('KAKAO_TOKEN')
CHECK_MINUTES = int(os.getenv('CHECK_MINUTES', '2'))
last_alert_sent = False


def send_kakao(message: str):
    api = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'
    headers = {'Authorization': f'Bearer {KAKAO_TOKEN}'}
    data = {
        'template_object': '{"object_type":"text","text":"' + message + '","link":{"web_url":"' + URL + '"}}'
    }
    r = requests.post(api, headers=headers, data=data, timeout=20)
    print('Kakao status:', r.status_code, r.text)


def check_ticket():
    global last_alert_sent
    try:
        r = requests.get(URL, headers=USER_AGENT, timeout=20)
        html = r.text
        soldout_keywords = ['매진', '예약마감']
        available = not any(word in html for word in soldout_keywords)

        print('Checked. Available =', available)

        if available and not last_alert_sent:
            msg = '🚨 김포→제주 4/30 오전·오후 취소표 가능성 발견! 지금 확인하세요'
            send_kakao(msg)
            last_alert_sent = True

        if not available:
            last_alert_sent = False

    except Exception as e:
        print('Error:', e)


schedule.every(CHECK_MINUTES).minutes.do(check_ticket)
print('Bot started')
check_ticket()

while True:
    schedule.run_pending()
    time.sleep(1)
