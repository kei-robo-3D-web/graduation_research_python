import cv2
import mediapipe as mp
import websockets
import asyncio
import threading
import json

current_websocket = None
event_loop = None  # イベントループ保持用
shutdown_event = None  # シャットダウン用イベント

async def echo(websocket):
    global current_websocket
    current_websocket = websocket
    try:
        async for message in websocket:
            print(f"Received from Unity: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed.")

def mediape_thread(loop):
    global current_websocket, shutdown_event

    mp_pose = mp.solutions.hands
    pose = mp_pose.Hands()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not found.")
        exit()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        hand_data = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for lm in hand_landmarks.landmark:
                    hand_data.append({"x": lm.x, "y": lm.y, "z": lm.z})

            if current_websocket is not None:
                try:
                    asyncio.run_coroutine_threadsafe(
                        current_websocket.send(json.dumps({"hands": hand_data})),
                        loop
                    )
                except Exception as e:
                    print("Send failed:", e)

        cv2.imshow("Pose Estimation", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Q pressed: shutting down.")
            # イベントをセットしてWebSocketも止める
            loop.call_soon_threadsafe(shutdown_event.set)
            break

    cap.release()
    cv2.destroyAllWindows()

async def main():
    global event_loop, shutdown_event
    event_loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    # メディアパイプ処理を別スレッドで起動
    thread1 = threading.Thread(target=mediape_thread, args=(event_loop,))
    thread1.start()

    async with websockets.serve(echo, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        # shutdown_event が set() されるまで待つ
        await shutdown_event.wait()
        print("WebSocket server shutting down.")

# 実行
asyncio.run(main())
