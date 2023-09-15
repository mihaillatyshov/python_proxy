from typing import Any, Callable, Literal, TypeAlias

import requests

MethodLiteral: TypeAlias = Literal["GET", "POST", "PUT", "HEAD", "OPTIONS", "PATCH", "TRACE", "DELETE", "CONNECT"]
HeadersJson = dict[str, str]
CookiesJson = dict[str, str]
SearchParamsJson = dict[str, list[str]]
BodyParamsJson = dict[str, Any]

http_method_funcs_aliases: dict[MethodLiteral, Callable] = {
    "GET": requests.get,
    "POST": requests.post,
    "PUT": requests.put,
    "HEAD": requests.head,
    "OPTIONS": requests.options,
    "PATCH": requests.patch,
    "DELETE": requests.delete
}
