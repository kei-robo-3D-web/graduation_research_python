import cv2
import mediapipe as mp

# MediaPipeのポーズ推定モジュールをインスタンス化
mp_pose = mp.solutions.hands
pose = mp_pose.Hands()

# Webカメラを開く
cap = cv2.VideoCapture(0)

# カメラが開けない場合のエラーハンドリング
if not cap.isOpened():
    print("Error: Camera not found.")
    exit()

# 画像処理ループ
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # BGRからRGBに変換（MediaPipeはRGB形式を期待するため）
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb_frame)
    if results.multi_hand_landmarks:
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp.solutions.drawing_utils.draw_landmarks(
                image=frame,
                landmark_list=hand_landmarks,
                connections=mp_pose.HAND_CONNECTIONS,
                landmark_drawing_spec=mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_hand_connections_style()
            )

            print(f"Hand {hand_idx + 1}")
            for i, lm in enumerate(hand_landmarks.landmark):
                h, w, _ = frame.shape  # 画像サイズ取得
                cx, cy = int(lm.x * w), int(lm.y * h)  # ピクセル座標に変換
                print(f"  Landmark {i}: (x={cx}, y={cy}, z={lm.z:.4f})")

            

    # 画像を表示
    cv2.imshow("Pose Estimation", frame)

    # 'q'を押すと終了
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 終了処理
cap.release()
cv2.destroyAllWindows()
