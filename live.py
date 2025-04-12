import io
from pygame import Surface, surfarray
import websockets as ws
import asyncio as aio
from PIL import Image
from base64 import b64encode
from typing import Dict
import json

async def handler(ws, path, server):
    print('client connected')
    server.clients.add(ws)
    try:
        async for msg in ws:
            print('received message:', msg)
    except:
        pass
    finally:
        server.clients.remove(ws)
        print('client disconnected')

class Live:
    def __init__(self, port:int=80):
        self.port = port
        self.clients = set()
        while True:
            if port>65535:
                print('port out of range')
                break
            try:
                self.server = aio.get_event_loop().run_until_complete(ws.serve(lambda ws, path:handler(ws, path, self), '0.0.0.0', port))
                print('server started on port', port)
                self.running = True
                break
            except OSError:
                print(f'port {port} is in use, trying {port+1}')
                port += 1
    def add_frame(self, blocks:Surface, others:Dict):
        frame = surfarray.array3d(blocks)
        # 将[x,y,z]转换为[y,x,z]
        frame = frame.transpose([1, 0, 2])
        frame = Image.fromarray(frame)
        byte_io = io.BytesIO()
        frame.save(byte_io, format='PNG')
        b64 = b64encode(byte_io.getvalue()).decode('utf-8')
        content = {'type': 'frame', 'data': b64, 'others': others}
        aio.get_event_loop().run_until_complete(self.broadcast(json.dumps(content, separators=(',', ':'))))

    def close(self):
        self.server.close()
        aio.get_event_loop().run_until_complete(self.server.wait_closed())
        for i in self.clients:
            i.close()
        print('server closed')

    async def broadcast(self, msg):
        for client in self.clients:
            try:
                await client.send(msg)
            except ws.exceptions.ConnectionClosedError:
                self.clients.remove(client)