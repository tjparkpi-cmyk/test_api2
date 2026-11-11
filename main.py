
import os
import json
import asyncio
import logging
from datetime import datetime

import requests
import websockets

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# -------------------------
# 설정
# -------------------------

PROJECT_ID = os.getenv("PROJECT_ID")
PORT = int(os.getenv("PORT", "10000"))

ENTRY_WS_URL = (
    f"wss://playentry.org/content/{PROJECT_ID}/websocket"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------------
# HTTP 서버
# -------------------------

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            body = b"Entry Bot is running!"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/health":
            body = json.dumps({
                "status": "running",
                "websocket": "managed separately"
            }).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


def start_http():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    logging.info("HTTP server started on port %s", PORT)
    server.serve_forever()


# -------------------------
# JSON 분석
# -------------------------

def log_entry_message(message):

    print("\n========== ENTRY MESSAGE ==========")

    try:
        data = json.loads(message)

        print(json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ))

    except (json.JSONDecodeError, TypeError):
        print(message)

    print("===================================\n")


# -------------------------
# 외부 URL 요청
# -------------------------

def request_url(url):

    try:
        response = requests.get(
            url,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        logging.error("HTTP request failed: %s", error)

    except ValueError:
        logging.error("Invalid JSON response")

    return None


# -------------------------
# Entry WebSocket
# -------------------------

async def entry_worker():

    if not PROJECT_ID:
        raise RuntimeError("PROJECT_ID 환경변수가 없습니다.")

    while True:

        try:
            logging.info("Connecting to Entry WebSocket...")

            async with websockets.connect(
                ENTRY_WS_URL,
                ping_interval=20,
                ping_timeout=20
            ) as websocket:

                logging.info("Entry WebSocket connected!")

                async for message in websocket:

                    log_entry_message(message)

        except Exception as error:

            logging.error(
                "WebSocket disconnected: %s",
                error
            )

            logging.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


# -------------------------
# 프로그램 시작
# -------------------------

async def main():

    http_thread = Thread(
        target=start_http,
        daemon=True
    )

    http_thread.start()

    await entry_worker()


if __name__ == "__main__":
    asyncio.run(main())
