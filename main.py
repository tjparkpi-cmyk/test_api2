import asyncio
import json
import websockets
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

PROJECT_ID = "6af282c01849c26d27255ba2"


# Render 포트 확인용 HTTP 서버
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Entry Bot is running!")

    def log_message(self, format, *args):
        pass


def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"HTTP 서버 실행: {port}")
    server.serve_forever()


async def entry_bot():
    uri = f"wss://playentry.org/content/{PROJECT_ID}/websocket"

    while True:
        try:
            print("엔트리 서버 연결 시도...")

            async with websockets.connect(uri) as websocket:
                print("엔트리 실시간 서버 연결 성공!")

                await websocket.send(json.dumps({
                    "type": "connect",
                    "projectId": PROJECT_ID
                }))

                async for message in websocket:
                    data = json.loads(message)

                    if data.get("type") == "variable" and data.get("name") == "요청_URL":
                        url = data.get("value")

                        if not url:
                            continue

                        print(f"요청 감지: {url}")

                        try:
                            response = requests.get(url, timeout=5)

                            if response.status_code == 200:
                                result_text = response.json().get(
                                    "message", "데이터 없음"
                                )
                            else:
                                result_text = f"에러: {response.status_code}"

                        except Exception:
                            result_text = "요청 실패"

                        send_data = {
                            "type": "variable",
                            "name": "응답_데이터",
                            "value": result_text,
                            "projectId": PROJECT_ID
                        }

                        await websocket.send(json.dumps(send_data))
                        print(f"응답 전송 완료: {result_text}")

        except Exception as e:
            print(f"연결 오류: {e}")
            await asyncio.sleep(5)


async def main():
    Thread(target=start_http_server, daemon=True).start()
    await entry_bot()


if __name__ == "__main__":
    asyncio.run(main())
