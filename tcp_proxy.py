import abc
import socket
import ssl
from http.client import responses as responses_messages
from urllib.parse import parse_qs, urlparse


class HttpBase(abc.ABC):
    def __init__(self):
        self.data = None
        self.http_version = ""
        self.headers = {}

    def _base_data_parser(self, raw_headers: str) -> tuple[str, str, str]:
        raw_lines = raw_headers.split("\n")

        for line in raw_lines[1:]:
            key_value = line.split(":", 1)
            if len(key_value) != 2:
                continue
            self.headers[key_value[0]] = key_value[1].strip()

        first_line = raw_lines[0].split(" ")
        return first_line[0], first_line[1], first_line[2]

    def get_header(self, key_to_find: str) -> str | None:
        for key in self.headers:
            if key.lower() == key_to_find.lower():
                return self.headers[key]

        return None

    def del_header(self, key_to_find: str):
        for key in self.headers:
            if key.lower() == key_to_find.lower():
                del self.headers[key]
                return

    def headers_to_str(self) -> str:
        return "\n".join([f"{key}: {value}" for key, value in self.headers.items()]) + "\n\n"

    @abc.abstractmethod
    def data_from_raw_headers(self, raw_headers: str):
        pass


class HttpRequest(HttpBase):
    def __init__(self):
        super().__init__()
        self.method = ""
        self.path = ""
        self.is_tls = False

    def data_from_raw_headers(self, raw_headers: str):
        self.method, self.path, self.http_version = self._base_data_parser(raw_headers)


class HttpResponse(HttpBase):
    def __init__(self):
        super().__init__()
        self.status_code = 500
        self.message = responses_messages[500]

    def data_from_raw_headers(self, raw_headers: str):
        self.http_version, status_code, self.message = self._base_data_parser(raw_headers)
        self.status_code = int(status_code)


def intercept_request(conn: socket.socket) -> HttpRequest:
    result = HttpRequest()
    raw_request: bytes = b""
    while True:
        conn.settimeout(5.0)
        raw_request += conn.recv(1024)
        if raw_request.find(b"\r\n\r\n") != -1:
            raw_splited_data = raw_request.split(b"\r\n\r\n", 1)
            raw_request = raw_splited_data[1]
            result.data_from_raw_headers(raw_headers=raw_splited_data[0].replace(b"\r\n", b"\n").decode())
            print(result.method, result.path, result.http_version)
            print(result.headers)
            break

    if content_length_str := result.get_header("Content-Length"):
        content_length = int(content_length_str)
        while len(raw_request) < content_length:
            conn.settimeout(5.0)
            raw_request += conn.recv(1024)
        result.data = raw_request

    return result


def make_response(conn: socket.socket, is_tls: bool = False) -> HttpResponse:
    result = HttpResponse()
    raw_request: bytes = b""
    while True:
        conn.settimeout(5.0)
        raw_request += conn.recv(1024)
        if raw_request.find(b"\r\n\r\n") != -1:
            raw_splited_data = raw_request.split(b"\r\n\r\n", 1)
            raw_request = raw_splited_data[1]
            result.data_from_raw_headers(raw_headers=raw_splited_data[0].replace(b"\r\n", b"\n").decode())
            print(result.http_version, result.status_code, result.message)
            print(result.headers)
            break

    if is_tls:
        while True:
            conn.settimeout(5.0)
            data = conn.recv(1024)
            if not data:
                break
            raw_request += data
            if raw_request.endswith(b"\r\n0\r\n\r\n"):
                break
        result.data = raw_request

    else:
        if content_length_str := result.get_header("Content-Length"):
            content_length = int(content_length_str)
            while len(raw_request) < content_length:
                conn.settimeout(5.0)
                raw_request += conn.recv(1024)
            result.data = raw_request

    return result


#########################################################################################################################
################ Funcs ##################################################################################################
#########################################################################################################################
def proxy_client(request: HttpRequest) -> HttpResponse:
    parsed_url = urlparse(request.path)
    first_line = f"{request.method} {parsed_url.path}{parsed_url.query} {request.http_version}\n"
    
    if request.is_tls: 
        # context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.load_default_certs()
        # context.load_verify_locations('./certs/ca.crt')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as client_sock:
            with context.wrap_socket(client_sock, server_hostname=request.get_header('Host')) as tls_client_sock:
                print("TLS SOCK OPENED")
                tls_client_sock.connect((request.get_header('Host'), 443))
                print(tls_client_sock.version())
                tls_client_sock.sendall(first_line.encode())
                tls_client_sock.sendall(request.headers_to_str().encode())
                if request.data:
                    tls_client_sock.sendall(request.data)
                tls_client_sock.settimeout(5.0)

                response = make_response(tls_client_sock, True)
                return response
            
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as client_sock:
            client_sock.connect((request.get_header("Host"), 80))

            client_sock.sendall(first_line.encode())
            client_sock.sendall(request.headers_to_str().encode())
            if request.data:
                client_sock.sendall(request.data)
            client_sock.settimeout(5.0)

            response = make_response(client_sock)

            return response