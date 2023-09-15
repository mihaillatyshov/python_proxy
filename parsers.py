from urllib.parse import parse_qs, urlparse
from http.client import responses

from requests import Response

from base import BodyParamsJson, HeadersJson, MethodLiteral


#########################################################################################################################
################ Request ################################################################################################
#########################################################################################################################
def parse_request(
    method: MethodLiteral,
    url: str,
    headers: HeadersJson,
    body_params: BodyParamsJson,
):
    parsed_url = urlparse(url)

    cookies = {}
    if cookies_str := headers.get("Cookie"):
        del headers["Cookie"]
        for item in cookies_str.split(";"):
            splited_item = item.split("=")
            if len(splited_item) == 2:
                cookies[splited_item[0]] = splited_item[1]

    return {
        "method": method,
        "path": parsed_url.path,
        "headers": dict(headers),
        "cookies": cookies,
        "search_params": parse_qs(parsed_url.query),
        "body_params": body_params
    }


#########################################################################################################################
################ Response ###############################################################################################
#########################################################################################################################
def parse_response(response: Response, request_id: int):
    fixed_headers = {key: value for key, value in response.headers.items()}

    return {
        "code": response.status_code,
        "message": responses[response.status_code],
        "headers": fixed_headers,
        "body": response.text,
        "request_id": request_id,
    }


#########################################################################################################################
################ Utils ##################################################################################################
#########################################################################################################################
# def search_params_to_str()