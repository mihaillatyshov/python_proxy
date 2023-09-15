import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import parse_qs

import requests

import db_queries
import parsers
from base import MethodLiteral, http_method_funcs_aliases
from flask_app import create_app


def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8080)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.process_request("GET")

    def do_POST(self):
        self.process_request("POST")

    def do_PUT(self):
        self.process_request("PUT")

    def do_HEAD(self):
        self.process_request("HEAD")

    def do_OPTIONS(self):
        self.process_request("OPTIONS")

    def do_PATCH(self):
        self.process_request("PATCH")

    def do_DELETE(self):
        self.process_request("DELETE")

    def process_request(self, method: MethodLiteral):
        requests_command = http_method_funcs_aliases[method]
        del self.headers["Proxy-Connection"]

        body_params = {}
        data_param = None
        json_param = None
        if content_type := self.headers.get('content-type'):
            ctype, pdict = cgi.parse_header(content_type)
            if ctype == 'multipart/form-data':
                body_params = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                body_params = parse_qs(self.rfile.read(length), keep_blank_values=True)
                body_params = {key.decode(): [v.decode() for v in vals] for key, vals in body_params.items()}
                data_param = body_params
            elif length := int(self.headers['content-length']):
                body_params = json.loads(self.rfile.read(length).decode())
                json_param = body_params

        db_request = db_queries.save_request(**parsers.parse_request(method, self.path, self.headers, body_params))

        proxy_resp = requests_command(url=self.path,
                                      headers=self.headers,
                                      allow_redirects=False,
                                      timeout=5,
                                      json=json_param,
                                      data=data_param)

        self.send_response(proxy_resp.status_code)

        self._headers_buffer = [self._headers_buffer[0]]
        for key, value in proxy_resp.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(proxy_resp.text.encode())

        db_queries.save_response(**parsers.parse_response(proxy_resp, db_request.id))

    def do_CONNECT(self):
        # parsers.parse_request(f"https://{self.path}")

        with requests.get(url=f"https://{self.path}", headers=self.headers, allow_redirects=False,
                          stream=True) as proxy_resp:
            for line in proxy_resp.iter_lines():
                print(line.decode())

        self.send_response(proxy_resp.status_code)

        self._headers_buffer = [self._headers_buffer[0]]
        for key, value in proxy_resp.headers.items():
            self.send_header(key, value)
        self.end_headers()


if __name__ == '__main__':
    thread = Thread(target=run, args=(HTTPServer, HttpGetHandler))
    thread.start()

    app = create_app()
    app.run(host="0.0.0.0", port=8000)
