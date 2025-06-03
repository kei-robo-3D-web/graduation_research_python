import asyncio
import websockets

async def echo(websocket):
    async for message in websocket:
        print(f"Received message: {message}")
        await websocket.send(f"Echo: {message}")

async def main():
    async with websockets.serve(echo, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # サーバーを永久に待機させるためのダミー処理

# 実行
asyncio.run(main())
