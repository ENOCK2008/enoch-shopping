# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # You can also add logic here for joining specific rooms, etc.

    async def disconnect(self, close_code):
        pass  # Handle disconnecting

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # Handle message here
        await self.send(text_data=json.dumps({
            'message': message
        }))
