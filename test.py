from typing import Any, Dict, Optional, TypeVar, TypedDict
from typing_extensions import Self
import paramiko
from paramiko.channel import ChannelFile
from channels.layers import get_channel_layer, InMemoryChannelLayer
import time
import os
from climain.tasks import send_ws_message

from climain import CliInterface
os.environ['DJANGO_SETTINGS_MODULE'] = 'base.settings'


def yield_test():
    for i in range(10):
        yield i
        time.sleep(0.005)


if __name__ == "__main__":
    instance = CliInterface.get_or_connect(1, {
        "port": 7720,
        "hostname": "honeycombpizza.link",
        "username": "root",
        "password": "eowjsrhkddurtlehdrneowjsfh304qjsrlf28"
    })
    # instance.exec_command('docker ps -a')
    instance.exec_command("cd /server/initial")
    res = instance.exec_command("ls -al")
    # res = instance.exec_command('docker logs -f -n 5 redis')
    channel: Optional[InMemoryChannelLayer] = get_channel_layer()
    # if res is not None and channel is not None:
    #     datas = []
    #     idx = 0
    #     for i in res:
    #         datas.append(i)
    #         print("messageSend", i)
    #         send_ws_message.delay(1, {
    #             'type': 'emit',
    #             "order": "order",
    #             "username": "username",
    #             "data": i
    #         })
    # send_ws_message.delay(1, {
    #     'type': 'emit',
    #     "order": "order",
    #     "username": "username",
    #     "data": datas
    # })
    # print("tlqkffkak")
    # print(datas)
    # print(len(datas))
    # print(datas)
    # print(len(datas))
    instance.close()
