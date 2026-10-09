"""Local browser interface reusing the lab's database connection functions."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys

import psycopg
from main import fetch_version, load_config


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def json_response(self, status, payload):
        self.respond(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path != "/":
            self.json_response(404, {"error": "Страница не найдена."})
            return
        self.respond(200, Path(__file__).with_name("index.html").read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/connect":
            self.json_response(404, {"error": "Страница не найдена."})
            return
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            self.json_response(403, {"error": "Откройте форму с адреса этого приложения."})
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            self.json_response(415, {"error": "Ожидается JSON."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict) or set(data) != {"username", "password"}:
                raise ValueError()
            if any(not isinstance(value, str) or not value or "\0" in value for value in data.values()):
                raise ValueError()
        except (ValueError, OSError):
            self.json_response(400, {"error": "Введите логин и пароль."})
            return
        try:
            config = load_config()
            version = fetch_version(config, data["username"], data["password"])
        except psycopg.OperationalError:
            self.json_response(401, {"error": "Не удалось подключиться. Проверьте логин и пароль, а также доступность базы данных."})
            return
        except (psycopg.Error, OSError, ValueError):
            self.json_response(503, {"error": "Не удалось выполнить запрос. Проверьте настройки и состояние базы данных."})
            return
        self.json_response(200, {"username": data["username"], "database": config["dbname"], "version": version})

    def log_message(self, format, *args):
        # Never log request bodies or credentials.
        print("HTTP " + format % args, file=sys.stderr, flush=True)


if __name__ == "__main__":
    print("Форма входа: http://localhost:8081", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
