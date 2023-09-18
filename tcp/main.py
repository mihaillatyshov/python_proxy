import socket
from urllib.parse import parse_qs, urlparse

from tcp_proxy import make_response, intercept_request, HttpRequest, HttpResponse


def proxy_client(request: HttpRequest) -> HttpResponse:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
        client_sock.connect((request.get_header("Host"), 80))

        parsed_url = urlparse(request.path)
        first_line = f"{request.method} {parsed_url.path}{parsed_url.query} {request.http_version}\n"
        client_sock.sendall(first_line.encode())
        client_sock.sendall(request.headers_to_str().encode())
        if request.data:
            client_sock.sendall(request.data)
        # client_sock.settimeout(5.0)

        response = make_response(client_sock)

        # raw_data = b""
        # while True:
        #     print("RECV")
        #     recv_data = client_sock.recv(1024)
        #     print("recv_data: ", recv_data)
        #     if not recv_data:
        #         break
        #     raw_data += recv_data

        # print("raw_data", raw_data.decode())

        return response


def server_loop(server_sock: socket.socket):
    while True:
        try:
            connection, client_address = server_sock.accept()
            print("===========================================================================")
            print(f"New client accepted {client_address}")
            print("===========================================================================")

            request = intercept_request(connection)

            request.del_header("Proxy-Connection")
            request.del_header("Accept-Encoding")

            response = proxy_client(request)

            connection.sendall(f"{response.http_version} {response.status_code} {response.message}\n".encode())
            connection.sendall(response.headers_to_str().encode())
            if response.data:
                connection.sendall(response.data)
            connection.close()

        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print("[ Error ]: ", e)


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        try:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(("0.0.0.0", 8080))
            server_sock.listen()

            server_loop(server_sock)

        except KeyboardInterrupt:
            print("Sock closed")
            exit()