import cv2
import numpy as np
import os

out_path = "example_video_test.mp4"
width, height = 640, 360
fps = 24
seconds = 6
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

for i in range(fps * seconds):
    t = i / fps
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # 背景渐变
    frame[:, :, 0] = np.linspace(50, 200, width, dtype=np.uint8)[None, :]
    frame[:, :, 1] = np.linspace(80, 30, height, dtype=np.uint8)[:, None]

    # 移动的圆形和文字
    cx = int((0.1 + 0.8 * (i / (fps * seconds))) * width)
    cy = int(height / 2 + 40 * np.sin(2 * np.pi * (i / (fps * 2))))
    cv2.circle(frame, (cx, cy), 40, (0, 180, 255), -1)

    text = f"Test Video - t={t:.2f}s"
    cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    writer.write(frame)

writer.release()
print(f"Created test video: {os.path.abspath(out_path)}")
