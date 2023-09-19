import json

from urllib.parse import parse_qs, urlparse, urlencode
from db_models import Request
from tcp_proxy import HttpRequest, HttpResponse


#########################################################################################################################
################ Request ################################################################################################
#########################################################################################################################
def parse_http_request(request: HttpRequest):
    parsed_url = urlparse(request.path)

    cookies = {}
    if cookies_str := request.get_header("Cookie"):
        del request.headers["Cookie"]
        for item in cookies_str.split(";"):
            splited_item = item.split("=")
            if len(splited_item) == 2:
                cookies[splited_item[0]] = splited_item[1]

    return {
        "method": request.method,
        "path": parsed_url.path,
        "headers": request.headers,
        "cookies": cookies,
        "search_params": parse_qs(parsed_url.query),
        "body_params": request.data.decode() if request.data is not None else None,
        "is_tls": request.is_tls
    }


def db_to_http_request(request: Request) -> HttpRequest:
    result = HttpRequest()
    result.method = request.method
    result.path = request.path + urlencode(request.search_params)
    result.http_version = "HTTP/1.1"
    result.headers = request.headers
    result.headers["Cookie"] = "; ".join([f"{key}={value}" for key, value in request.cookies.items()]) + ";"
    result.data = json.dumps(request.body_params).encode()
    result.is_tls = request.is_tls

    return result


#########################################################################################################################
################ Response ###############################################################################################
#########################################################################################################################
def parse_http_response(response: HttpResponse, request_id: int):
    return {
        "code": response.status_code,
        "message": response.message,
        "headers": response.headers,
        "body": response.data.decode() if response.data is not None else None,
        "request_id": request_id,
    }


#########################################################################################################################
################ Utils ##################################################################################################
#########################################################################################################################
# def search_params_to_str()