from api_exceptions import RequestNotFoundException
from base import (BodyParamsJson, CookiesJson, HeadersJson, MethodLiteral, SearchParamsJson)
from db_models import Request, Response, create_db_session_from_json_config_file

DBsession = create_db_session_from_json_config_file()


#########################################################################################################################
################ Request ################################################################################################
#########################################################################################################################
def save_request(
    method: MethodLiteral,
    path: str,
    headers: HeadersJson,
    cookies: CookiesJson,
    search_params: SearchParamsJson,
    body_params: BodyParamsJson,
) -> Request:
    request = Request(method=method,
                      path=path,
                      headers=headers,
                      cookies=cookies,
                      search_params=search_params,
                      body_params=body_params)

    DBsession.add(request)
    DBsession.commit()

    return request


def get_request_by_id(request_id: int) -> Request:
    request = DBsession.query(Request).filter(Request.id == request_id).one_or_none()

    if request is None:
        raise RequestNotFoundException(request_id)

    return request


def get_all_requests() -> list[Request]:
    return DBsession.query(Request).all()


#########################################################################################################################
################ Response ###############################################################################################
#########################################################################################################################
def save_response(code: int, message: str, headers: HeadersJson, body: str, request_id: int) -> Response:
    response = Response(code=code, message=message, headers=headers, body=body, request_id=request_id)

    DBsession.add(response)
    DBsession.commit()

    return response
