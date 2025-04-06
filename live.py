import io
import pygame
import websockets as ws
import asyncaio as aio
from PIL import Image

clients = set()

async def handler(ws, path):
    print('client connected')
    clients.add(ws)
    try:
        while True:
            await aio.sleep(0.1)
    except:
        pass
    finally:
        clients.remove(ws)
        print('client disconnected')
        
async def broadcast(msg):
    for client in clients:
        await client.send(msg)

class Live:
    def __init__(self, port:int=80):
        self.port = port
        self.server = aio.get_event_loop().run_until_complete(ws.serve(handler, '0.0.0.0', port))
        print('server started')
    def addframe(self, blocks:pygame.Surface):
        content = pygame.surfarray.array3d(blocks)
        content = Image.fromarray(content)
        byte_io = io.BytesIO()
        content.save(byte_io, format='PNG')
        aio.get_event_loop().run_until_complete(broadcast(content))