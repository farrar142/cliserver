import json
from asgiref.sync import sync_to_async

from ninja import NinjaAPI, Schema
from ninja.renderers import BaseRenderer

from climain import CliInterface
from base.serializer import converter

description = """
cliserver api
"""


# class MyRenderer(BaseRenderer):
#     media_type = "application/json"

#     def render(self, request, data, *, response_status):
#         if data:
#             return json.dumps(converter(data))
#         else:
#             return json.dumps([])


api = NinjaAPI(description=description, csrf=False)


class TokenSchema(Schema):
    token: str = "token"

    def __init__(schema: Schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if schema.dict().get("token"):
            del schema.token


class CliForm(TokenSchema):
    hostname: str
    username: str
    password: str
    directory: str
    cmd: str
    port: int


@sync_to_async
@api.get("abc")
def yieldtest(request):
    return {'data': 0}


@sync_to_async
@api.post("get")
def clione(request, form: CliForm):
    print(form)
    print("reached")
    return CliInterface().from_api(form.hostname, form.username, form.password, form.directory, form.cmd, form.port)


@sync_to_async
@api.get("get")
def cli(request, form: CliForm):
    print(form)
    print("reached")
    return CliInterface().from_api(form.hostname, form.username, form.password, form.directory, form.cmd, form.port)
