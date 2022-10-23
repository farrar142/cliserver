import json
from typing import Literal
from asgiref.sync import async_to_sync, sync_to_async
from unidecode import unidecode
from base.consumer_base import AsyncWebsockerConsumerWrapper
from .tasks import send_ws_message
from climain import CliInterface, HostInformation

SSHOrder = Literal["connect_to_paramiko"]


class SSHConsumer(AsyncWebsockerConsumerWrapper):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = u'ssh_%s' % unidecode(self.user_id)
        # Join room group
        print("joining group")
        await self.channel_layer.group_add(
            unidecode(self.room_group_name),
            self.channel_name
        )
        print("join group succesfully")

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        order: SSHOrder = text_data_json.get('order', 'connect_to_paramiko')
        data = text_data_json.get('data', {})
        result = {}
        if order == "connect_to_paramiko":
            self.cli = CliInterface.from_api(self.user_id, **data)
            print(self.cli)
        elif order == "command":
            command = data.get("cmd")
            datas = []
            for i in self.cli.exec_command(command):
                datas.append(i)
                print("send message")
                send_ws_message.delay(self.user_id,
                                      {
                                          'type': 'emit',
                                          'order': order,
                                          'username': self.user_id,
                                          'data': datas
                                      })
            return print("message End")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'emit',
                'order': order,
                'username': self.user_id,
                'data': result
            }
        )

    async def emit(self, event):
        order = event['order']
        username = event['username']
        data = event['data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'author': username,
            'order': order,
            'data': data,
        }))
