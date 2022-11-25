import socket
import ssl
import json
import time
from typing import Type


class RequestError(Exception):
    """
    Raises error if Request class was misused
    """
    pass


class Response:
    """
    Represents the Response object given after a HTTPs request.
    """
    def __init__(self, content, headers) -> None:
        self.status_code = None
        self.headers = self.get_headers(headers)
        self.content = content

    def get_headers(self, headers):
        headers_dict = {}
        self.status_code = int(headers.split(b"\r\n")[0].split()[1])
        for header in headers.split(b"\r\n")[1:]:
            name, value = header.split(b": ")
            headers_dict[name.lower().decode()] = value.decode()

        return headers_dict

    @property
    def text(self):
        return self.content.decode()

    def json(self):
        return json.loads(self.text)


class Request:

    def __init__(self, method: str, link: str, data: dict, connection=None) -> None:
        self.method = method
        self.protocol, self.host, self.path = self.parse_link(link)
        self.data = data
        self.sock = connection

    @property
    def port(self) -> int:
        if self.protocol == "http":
            return 80

        elif self.protocol == "https":
            return 443

        raise RequestError(f"URL must start with http or https not {self.protocol}")

    def new_connection(self):
        sock = socket.socket()
        sock.connect((self.host, self.port))

        if self.port == 443:
            sock = ssl.create_default_context().wrap_socket(
                sock,
                server_hostname=self.host
            )

            sock.do_handshake()

        return sock

    def get_payload(self):
        if self.method == "GET":
            return f"GET {self.path} HTTP/1.1\r\nHost: {self.host}\r\n\r\n".encode()

        else:
            content_length = len(json.dumps(self.data))
            return f"{self.method} {self.path} HTTP/1.1\r\nHost: {self.host}\r\nContent-Length: {content_length}\r\nContent-Type: application/json\r\n\r\n{self.data}".encode()

    def get_response(self):
        data = self.get_payload()
        if self.sock is None:
            self.sock = self.new_connection()
        self.sock.sendall(data)

        response, body = self.sock.recv(1024 ** 2).split(b"\r\n\r\n", 1)
        for header in response.lower().split(b"\r\n"):
            if b"content-length:" in header:
                content_length = int(header.split(b"content-length: ")[1].decode())

                while content_length > len(body):
                    body += self.sock.recv(1024 ** 2)

        return Response(body, response)

    def parse_link(self, link: str) -> tuple:
        link_data = link.split("/")
        host = link_data[2]
        return link.split(":")[0], host, link.split(host)[1]


class HttpFast:
    """
    Represents a http/s client.
    """
    def __init__(self) -> None:
        self.connections = {}

    def send_request(self, method: str, link: str, data=None) -> Response:

        host = link.split("/")[2]
        request = Request(
            method=method,
            link=link,
            data=data,
            connection=self.connections.get(host)
        )

        response = request.get_response()
        if host not in self.connections:
            self.connections[host] = request.sock
        return response

    def get(self, link: str) -> Response:
        return self.send_request(method="GET", link=link)

    def post(self, link: str, data: dict):
        return self.send_request(method="POST", link=link, data=data)

    def put(self, link: str, data: dict):
        return self.send_request(method="PUT", link=link, data=data)

    def patch(self, link: str, data: dict):
        return self.send_request(method="PATCH", link=link, data=data)

    def delete(self, link: str, data: dict):
        return self.send_request(method="DELETE", link=link, data=data)