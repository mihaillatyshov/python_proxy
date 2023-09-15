from datetime import datetime, time, timedelta
from typing import Any, cast

from flask import Blueprint, Flask
from flask.json.provider import DefaultJSONProvider
from requests import Response
from sqlalchemy.ext.declarative import DeclarativeMeta
from api_exceptions import InvalidAPIUsage, ResponseInjectionFound

from base import http_method_funcs_aliases, MethodLiteral
import db_queries
import parsers

base_blueprint = Blueprint("base", __name__)
routes_bp = Blueprint("routes", __name__)
base_blueprint.register_blueprint(routes_bp)


def header_key_has_key_case_insensitive(key_any_case: str, headers: dict[str, Any]) -> bool:
    return key_any_case.lower() in [key.lower() for key in headers]


def get_header_key_case_insensitive(key_any_case: str, headers: dict[str, Any]) -> str | None:
    if not header_key_has_key_case_insensitive(key_any_case, headers):
        return None

    lower_header_keys = [key.lower() for key in headers]
    return list(headers.keys())[lower_header_keys.index(key_any_case.lower())]


class CustomJSONEncoder(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            if hasattr(obj, '__json__'):
                return obj.__json__()
            data = {}
            for column in obj.__table__.columns:
                data[column.name] = getattr(obj, column.name)
            return data
        if isinstance(obj, timedelta) or isinstance(obj, time) or isinstance(obj, datetime):
            return str(obj)

        return DefaultJSONProvider.default(obj)


def create_app():
    app = Flask(__name__)
    app.secret_key = "my super duper puper secret key!"
    app.json_provider_class = CustomJSONEncoder
    app.json = CustomJSONEncoder(app)

    app.register_blueprint(base_blueprint)

    @app.errorhandler(InvalidAPIUsage)
    def app_error_handler(exception: InvalidAPIUsage):
        return exception.to_dict(), exception.status_code

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_queries.DBsession.remove()

    return app


@routes_bp.route("/requests", methods=["GET"])
def get_all_requests():
    return {"requests": db_queries.get_all_requests()}


@routes_bp.route("/requests/<int:id>", methods=["GET"])
def get_request_by_id(id: int):
    return {"request": db_queries.get_request_by_id(id)}


def get_path(db_headers: dict[str, str], path: str) -> str:
    host = db_headers["Host"] if db_headers.get('Host') else "127.0.0.1"
    return f"http://{host}{path}"


def get_headers(db_headers: dict[str, str], db_cookies: dict[str, str]) -> dict[str, str]:
    headers = db_headers.copy()

    if len(db_cookies.keys()) > 0:
        headers["Cookie"] = "; ".join([f"{key}={value}" for key, value in db_cookies.items()]) + ";"

    return headers


def get_data_and_json(db_body_params: dict, headers: dict[str, str]) -> tuple[dict | None, dict | None]:
    data = None
    json = None
    content_type_key = get_header_key_case_insensitive("Content-Type", headers=headers)
    if content_type_key is not None and headers[content_type_key] == "application/x-www-form-urlencoded":
        data = db_body_params
    elif content_type_key is not None:
        json = db_body_params

    return data, json


@routes_bp.route("/repeat/<int:id>", methods=["GET"])
def repeat_request_by_id(id: int):
    db_request = db_queries.get_request_by_id(id)
    requests_command = http_method_funcs_aliases[cast(MethodLiteral, db_request.method)]

    path = get_path(db_request.headers, db_request.path)
    headers = get_headers(db_request.headers, db_request.cookies)
    data, json = get_data_and_json(db_request.body_params, headers)

    proxy_resp = requests_command(url=path,
                                  params=db_request.search_params,
                                  headers=headers,
                                  allow_redirects=False,
                                  data=data,
                                  json=json,
                                  timeout=5)

    response = db_queries.save_response(**parsers.parse_response(proxy_resp, db_request.id))

    return {"response": response}


def check_for_command_injection(response: Response):
    if "root:" in response.text:
        raise ResponseInjectionFound()


# ! variant 1
@routes_bp.route("/scan/<int:id>", methods=["GET"])
def scan_request_by_id(id: int):
    db_request = db_queries.get_request_by_id(id)
    requests_command = http_method_funcs_aliases[cast(MethodLiteral, db_request.method)]

    path = get_path(db_request.headers, db_request.path)
    headers = get_headers(db_request.headers, db_request.cookies)
    data, json = get_data_and_json(db_request.body_params, headers)

    checks = [";cat /etc/passwd;", "|cat /etc/passwd|", "`cat /etc/passwd`"]

    for check_str in checks:
        try:
            proxy_resp = requests_command(url=path + check_str,
                                          params=db_request.search_params,
                                          headers=headers,
                                          allow_redirects=False,
                                          data=data,
                                          json=json,
                                          timeout=5)
            db_queries.save_response(**parsers.parse_response(proxy_resp, db_request.id))
            check_for_command_injection(proxy_resp)

        except Exception as e:
            print(f"skipped: {e}")

        try:
            if data is not None:
                proxy_resp = requests_command(url=path,
                                              params=db_request.search_params,
                                              headers=headers,
                                              allow_redirects=False,
                                              data={
                                                  **data, "super_check_param": check_str
                                              },
                                              json=json,
                                              timeout=5)
                db_queries.save_response(**parsers.parse_response(proxy_resp, db_request.id))
                check_for_command_injection(proxy_resp)
        except Exception as e:
            print(f"skipped: {e}")

        try:
            if headers.get("Cookie") is not None:
                headers["Cookie"] += check_str
                proxy_resp = requests_command(url=path + check_str,
                                              params=db_request.search_params,
                                              headers=headers,
                                              allow_redirects=False,
                                              data=data,
                                              json=json,
                                              timeout=5)
                db_queries.save_response(**parsers.parse_response(proxy_resp, db_request.id))
                check_for_command_injection(proxy_resp)
        except Exception as e:
            print(f"skipped: {e}")

    return {"message": "No Injection"}
