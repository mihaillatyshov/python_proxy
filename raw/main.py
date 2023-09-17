# echo-server.py

import socket

import requests

HOST = "127.0.0.1"                                                                                                      # Standard loopback interface address (localhost)
PORT = 8080                                                                                                             # Port to listen on (non-privileged ports are > 1023)


def str_to_headers(raw_headers: str) -> tuple[str, str, str, dict[str, str]]:
    raw_lines = raw_headers.split("\n")

    m_p_hv = raw_lines[0].split(" ")
    method = m_p_hv[0]
    path = m_p_hv[1]
    http_version = m_p_hv[2]

    headers = {}
    raw_lines = raw_lines[1:]
    for raw_line in raw_lines:
        splited_line = raw_line.split(":")
        if len(splited_line) != 2:
            continue
        headers[splited_line[0]] = splited_line[1]

    return method, path, http_version, headers


def headers_to_str() -> str:
    pass


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
    server_sock.bind((HOST, PORT))
    server_sock.listen()
    while True:
        try:
            server_conn, addr = server_sock.accept()
            with server_conn:
                print(f"Connected from {addr}")
                data = server_conn.recv(1024).decode()
                # print(data)
                # data.replace("\r\n", "\n")
                # if data.find("\n\n")

                splited_data = data.split("\n\n")

                if not data:
                    break

                requests_command = requests.get
                method, path, http_version, headers = raw_headers_to_str(splited_data[0])

                print(method, path, http_version)
                print(headers)

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
                    client_sock.connect((path))
                    client_sock.sendall()

                proxy_resp = requests_command(url=self.path,
                                              headers=self.headers,
                                              allow_redirects=False,
                                              timeout=5,
                                              json=json_param,
                                              data=data_param)

                server_conn.sendall('HTTP/1.0 200 OK\n\n<div>HI!!!</div>'.encode())
                server_conn.close()
        except KeyboardInterrupt:
            server_conn.close()
            server_sock.close()
            exit()
        except Exception as e:
            print("[ ERROR ] Connection: ", e)
