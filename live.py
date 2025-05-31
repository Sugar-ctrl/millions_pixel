import io
from pygame import Surface, surfarray, image
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
        while server.running:
            await ws.recv()
    except:
        pass
    finally:
        server.removing.add(ws)
        print('client disconnected')

class Live:
    def __init__(self, port:int=80):
        self.port = port
        self.clients = set()
        self.removing = set()
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
        byte_io = io.BytesIO()
        image.save(blocks, byte_io, 'png')
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
        # 批量发送减少系统调用
        tasks = []
        for client in list(self.clients):
            if client.open:
                tasks.append(client.send(msg))
        
        # 并行发送
        await aio.gather(*tasks, return_exceptions=True)
        
        # 清理断开连接的客户端
        self.removing = [c for c in self.clients if not c.open]
        for c in self.removing:
            self.clients.remove(c)
