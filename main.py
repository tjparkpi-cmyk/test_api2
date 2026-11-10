import asyncio
import json
import websockets
import requests
import os

# ⚠️ 본인의 엔트리 작품 ID를 입력하세요 (URL 주소창 맨 뒤 영어+숫자 조합)
PROJECT_ID = "여러분의_엔트리_작품_ID_입력" 

async def entry_bot():
    uri = f"wss://playentry.org/content/{PROJECT_ID}/websocket"
    
    while True: # 연결이 끊어지면 자동으로 재접속하도록 예외처리 추가
        try:
            print("🤖 엔트리 실시간 서버에 연결을 시도합니다...")
            async with websockets.connect(uri) as websocket:
                print("✅ 엔트리 실시간 서버 연동 성공! 감시를 시작합니다.")
                await websocket.send(json.dumps({"type": "connect", "projectId": PROJECT_ID}))

                async for message in websocket:
                    data = json.loads(message)
                    
                    if data.get("type") == "variable" and data.get("name") == "요청_URL":
                        url = data.get("value")
                        if not url:
                            continue
                            
                        print(f"🔗 요청 감지됨: {url}")
                        
                        try:
                            response = requests.get(url, timeout=5)
                            if response.status_code == 200:
                                result_text = response.json().get("message", "데이터 없음")
                            else:
                                result_text = f"에러: {response.status_code}"
                        except Exception as e:
                            result_text = "요청 실패"

                        send_data = {
                            "type": "variable",
                            "name": "응답_데이터",
                            "value": result_text,
                            "projectId": PROJECT_ID
                        }
                        await websocket.send(json.dumps(send_data))
                        print(f"✅ 응답 전송 완료: {result_text}")
                        
        except Exception as e:
            print(f"❌ 연결 오류 발생 ({e}), 5초 후 재접속을 시도합니다.")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(entry_bot())
