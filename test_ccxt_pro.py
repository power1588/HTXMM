# -*- coding: utf-8 -*-

import asyncio
import json
import websockets
import gzip
from datetime import datetime


def decompress_data(data):
    try:
        decompressed = gzip.decompress(data)
        return json.loads(decompressed)
    except Exception as e:
        print(f"Error decompressing data: {str(e)}")
        return None


def format_orderbook(data):
    if 'tick' in data:
        tick = data['tick']
        ts = datetime.fromtimestamp(tick['ts'] / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
        print(f"\nTimestamp: {ts}")
        print("\nTop 5 Asks:")
        for i, ask in enumerate(tick['asks'][:5]):
            print(f"  {i+1}. Price: {ask[0]}, Size: {ask[1]}")
        print("\nTop 5 Bids:")
        for i, bid in enumerate(tick['bids'][:5]):
            print(f"  {i+1}. Price: {bid[0]}, Size: {bid[1]}")
        print("\n" + "="*50)


async def subscribe_to_orderbook():
    uri = "wss://api.hbdm.vn/linear-swap-ws"
    
    print("Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        # 订阅请求
        subscribe_message = {
            "sub": "market.ETH-USDT.depth.step0",
            "id": "id1"
        }
        
        print("Sending subscription message:", json.dumps(subscribe_message))
        await websocket.send(json.dumps(subscribe_message))
        
        print("Waiting for messages...")
        while True:
            try:
                response = await websocket.recv()
                if isinstance(response, bytes):
                    data = decompress_data(response)
                    if data:
                        format_orderbook(data)
                else:
                    print("Received text message:", response)
            except Exception as e:
                print(f"Error: {str(e)}")
                break


async def main():
    print("Starting main function...")
    await subscribe_to_orderbook()


if __name__ == "__main__":
    print("Starting program...")
    asyncio.run(main())