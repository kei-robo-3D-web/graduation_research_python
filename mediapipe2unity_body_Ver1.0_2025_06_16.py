import cv2
import mediapipe as mp
import websockets
import asyncio
import threading
import json

current_websocket = None
event_loop = None
shutdown_event = None

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


    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not found.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        pose_data = []
        if results.pose_landmarks:
            usingLandmarks = [11,12,13,14,15,16,25,26,27,28]
            for i in usingLandmarks:
                    lm = results.pose_landmarks.landmark[i]
                    pose_data.append({"x": lm.x, "y": lm.y, "z": lm.z})

            # 骨格の描画（関節＋線）
            mp.solutions.drawing_utils.draw_landmarks(
                image=frame,
                landmark_list=results.pose_landmarks,
                connections=mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp.solutions.drawing_styles.get_default_pose_landmarks_style(),
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=(0,255,0), thickness=2)
            )

            # WebSocket送信（Unity側受信を想定）
            if current_websocket is not None:
                try:
                    asyncio.run_coroutine_threadsafe(
                        current_websocket.send(json.dumps({"bodys": pose_data})),
                        loop
                    )
                except Exception as e:
                    print("Send failed:", e)

        # ウィンドウ表示
        cv2.imshow("Pose Estimation", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Q pressed: shutting down.")
            loop.call_soon_threadsafe(shutdown_event.set)
            break

    cap.release()
    cv2.destroyAllWindows()

async def main():
    global event_loop, shutdown_event
    event_loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    # MediaPipeをスレッドで起動
    thread1 = threading.Thread(target=mediape_thread, args=(event_loop,))
    thread1.start()

    async with websockets.serve(echo, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await shutdown_event.wait()
        print("WebSocket server shutting down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt received.")
