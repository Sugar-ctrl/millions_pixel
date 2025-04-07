import io
import pygame
import websockets as ws
import asyncio as aio
from PIL import Image
from base64 import b64encode

clients = set()

async def handler(ws, path):
    print('client connected')
    clients.add(ws)
    try:
        while True:
            await aio.sleep(0)
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
        while True:
            if port>65535:
                print('port out of range')
                break
            try:
                self.server = aio.get_event_loop().run_until_complete(ws.serve(handler, '0.0.0.0', port))
                print('server started on port', port)
                break
            except OSError:
                print(f'port {port} is in use, trying {port+1}')
                port += 1
    def add_frame(self, blocks:pygame.Surface):
        frame = pygame.surfarray.array3d(blocks)
        frame = Image.fromarray(frame)
        frame = frame.rotate(-90)
        frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        byte_io = io.BytesIO()
        frame.save(byte_io, format='PNG')
        b64 = b64encode(byte_io.getvalue()).decode('utf-8')
        content = '{"type": "frame", "data": "' + b64 + '"}'
        aio.get_event_loop().run_until_complete(broadcast(content))

    def close(self):
        self.server.close()
        aio.get_event_loop().run_until_complete(self.server.wait_closed())
        print('server closed')