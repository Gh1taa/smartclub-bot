"""Start the bot on a free web host (Render). Locally, keep using:  python bot.py

Free web services must answer on a web port and fall asleep after 15 minutes without visits,
so this opens a tiny "I'm alive" page on $PORT (visited every few minutes by cron-job.org)
and then runs the normal bot.
"""
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import bot


class Alive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Smart Club bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass  # don't fill the logs with the pings


server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "10000"))), Alive)
threading.Thread(target=server.serve_forever, daemon=True).start()
bot.main()
