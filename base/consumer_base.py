from channels.layers import InMemoryChannelLayer
from channels.generic.websocket import AsyncWebsocketConsumer


class AsyncWebsockerConsumerWrapper(AsyncWebsocketConsumer):
    channel_layer: InMemoryChannelLayer
