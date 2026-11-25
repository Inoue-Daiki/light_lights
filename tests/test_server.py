import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from client import request
from engine import Game
from server import handler_for

class ServerTests(unittest.TestCase):
    def test_http_roundtrip(self):
        g=Game(2)
        with ThreadingHTTPServer(("127.0.0.1",0),handler_for(g)) as server:
            t=threading.Thread(target=server.serve_forever,daemon=True)
            t.start()
            try:
                url=f"http://127.0.0.1:{server.server_port}"
                s=request(url,"/state")
                self.assertEqual(s["actions"],request(url,"/actions"))
                payload={"action":s["actions"][0]["id"],"revision":s["revision"]}
                next_state=request(url,"/action",payload)
                self.assertGreater(next_state["revision"],s["revision"])
                self.assertEqual(len(request(url,"/history")),1)
                with self.assertRaises(HTTPError) as err:
                    request(url,"/action",payload)
                self.assertEqual(err.exception.code,400)
            finally:
                server.shutdown()
                t.join()
