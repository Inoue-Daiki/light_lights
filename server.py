"""Loopback-only, single-session JSON HTTP server (Python standard library)."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from engine import Game

def handler_for(game):
    lock = Lock()
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, value):
            data = json.dumps(value,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            with lock:
                methods = {"/state":game.get_state,"/actions":game.get_actions,"/history":game.get_history}
                if self.path not in methods:
                    return self.reply(404,{"error":"not found"})
                return self.reply(200,methods[self.path]())

        def do_POST(self):
            if self.headers.get_content_type() != "application/json":
                return self.reply(415,{"error":"application/json required"})
            try:
                size = int(self.headers.get("Content-Length","0"))
                if not 0 < size <= 4096:
                    raise ValueError("invalid body length")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data,dict):
                    raise ValueError("object required")
                with lock:
                    if self.path == "/action":
                        result = game.execute_action(data.get("action"),data.get("revision"))
                    elif self.path == "/new":
                        if type(data.get("revision")) is not int or data["revision"] != game.revision:
                            raise ValueError("stale revision")
                        if game.phase not in ("won","lost"):
                            raise ValueError("finish current run first")
                        result = game.new_game(data.get("seed"))
                    else:
                        return self.reply(404,{"error":"not found"})
                return self.reply(200,result)
            except (ValueError,UnicodeError) as exc:
                return self.reply(400,{"error":str(exc)})
    return Handler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--seed",type=int)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1",args.port),handler_for(Game(args.seed))) as server:
        print(f"Light Lights: http://127.0.0.1:{server.server_port}",flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
