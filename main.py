import socket
import ssl
import subprocess
from threading import Thread

import db_queries
import parsers
from flask_app import create_app
from tcp_proxy import (HttpRequest, HttpResponse, intercept_request,
                       proxy_client)


def load_file_data(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()
        

def create_tls_context(host: str):
    fixed_host = host.removesuffix(":443")
    result = subprocess.run(["./certs/gen.sh", fixed_host], capture_output=True)
    print(f"Create cert for {fixed_host}")
    
    cert_filepath = f"./certs/{fixed_host}"
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with open(cert_filepath, "wb") as cert_file:
        cert_file.write(result.stdout)
        
    key_filepath = "./certs/cert.key"
    context.load_cert_chain(cert_filepath, key_filepath)
    return context


def server_loop(server_sock: socket.socket):
    while True:
        try:
            connection, client_address = server_sock.accept()
            print("\n===========================================================================")
            print(f"New client accepted {client_address}")

            request = intercept_request(connection)

            request.del_header("Proxy-Connection")
            request.del_header("Accept-Encoding")

            if request.method == "CONNECT":
                tls_context = create_tls_context(request.get_header("Host"))
                connection.sendall("HTTP/1.0 200 Connection established\n\n".encode())
                with tls_context.wrap_socket(connection, server_side=True) as tls_connection:
                    request = intercept_request(tls_connection)
                    request.is_tls = True
                    response = proxy_client(request)
                    
                    
                    tls_connection.sendall(f"{response.http_version} {response.status_code} {response.message}\n".encode())
                    tls_connection.sendall(response.headers_to_str().encode())
                    if response.data:
                        tls_connection.sendall(response.data)
                    
                    db_request = db_queries.save_request(**parsers.parse_http_request(request))
                    db_queries.save_response(**parsers.parse_http_response(response, db_request.id))
                
            else:
                response = proxy_client(request)

                connection.sendall(f"{response.http_version} {response.status_code} {response.message}\n".encode())
                connection.sendall(response.headers_to_str().encode())
                if response.data:
                    connection.sendall(response.data)
                connection.close()
                
                db_request = db_queries.save_request(**parsers.parse_http_request(request))
                db_queries.save_response(**parsers.parse_http_response(response, db_request.id))

        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print("[ Error ]: ", e)


def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        try:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(("0.0.0.0", 8080))
            server_sock.listen()
            print("Server started")

            server_loop(server_sock)

        except KeyboardInterrupt:
            print("Server closed")
            exit()


if __name__ == '__main__':
    thread = Thread(target=run)
    thread.start()
    
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
    
    