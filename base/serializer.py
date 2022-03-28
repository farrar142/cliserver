from datetime import datetime
from asgiref.sync import sync_to_async
from django.db.models.base import ModelState, ModelBase
from django.db.models import QuerySet
from django.db import models
from pprint import pprint


@sync_to_async
def aconverter(queries: QuerySet) -> dict:
    return converter(queries)


def converter(queries: QuerySet) -> dict:
    """
    querydict타입과 model타입을 구분해서 serialize해줌
    """
    if isinstance(queries, dict):  # 일반 dict타입일경우
        return [serialize(queries)]

    target: list = type_checker(queries)
    try:
        for obj in target:
            obj: dict = serialize(obj)
    except:
        pass
    # pprint(target)#debug
    if target:
        return target
    else:
        return [{}]
        return {'message': 'None Matched'}


def type_checker(queries):
    print(type(queries))
    if isinstance(queries, models.Model):  # Model속성일경우
        target = queries.__dict__
    elif isinstance(queries, QuerySet):
        if isinstance(queries.first(), models.Model):
            target = list(queries.values())
        else:
            print("value")
            target = list(queries)  # Queryset - Query속성일경우
    else:
        try:
            target = queries.__dict__
        except:
            target = queries
    if isinstance(target, list):
        return target
    else:
        return [target]


def serialize(obj: dict) -> dict:
    tmp = obj.copy()
    for k, v in tmp.items():
        if isinstance(obj[k], datetime):
            obj[k] = f'{obj[k]:%Y-%m-%d %H:%M:%S}'
        elif isinstance(obj[k], ModelBase):  # 추상타입일경우 삭제
            del(obj[k])
        elif isinstance(obj[k], ModelState):  # 추상타입일경우 삭제
            del(obj[k])
        elif k == '_state':
            del(obj[k])
    return obj
