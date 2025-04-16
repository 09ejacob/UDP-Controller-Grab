import socket
import numpy as np
import cv2
import os
import struct
import json
from datetime import datetime

SAVE_DIR = "received_images"
os.makedirs(SAVE_DIR, exist_ok=True)

image_counter = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9998))

print("Listening for UDP messages...")

while True:
    data, addr = sock.recvfrom(65535)

    try:
        text = data.decode("utf-8")
        # Check if it's likely a JSON object without image data
        if text.startswith("{") and text.endswith("}"):
            print("[TEXT] Received JSON:", text)
        else:
            print("[TEXT] Received:", text)
        continue

    except UnicodeDecodeError:
        pass

    try:
        # Parse structured image packet
        if len(data) < 4:
            print("[WARN] Packet too short.")
            continue

        meta_len = struct.unpack("!I", data[:4])[0]

        if len(data) < 4 + meta_len:
            print("[WARN] Packet missing image data.")
            continue

        metadata_bytes = data[4 : 4 + meta_len]
        jpeg_bytes = data[4 + meta_len :]

        metadata = json.loads(metadata_bytes.decode("utf-8"))
        camera_id = metadata.get("camera_id", "unknown")
        frame_id = metadata.get("frame_id", 0)
        timestamp = metadata.get("timestamp", datetime.now().isoformat())

        print(f"[IMAGE] From {camera_id} | Frame {frame_id} | Time {timestamp}")

        # Decode JPEG
        jpeg_array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        image = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)

        if image is not None:
            # Save image
            safe_timestamp = (
                timestamp.replace(":", "-").replace("T", "_").replace("Z", "")
            )
            filename = f"{camera_id}_{safe_timestamp}_{frame_id:04d}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(filepath, image)
            print(f"[SAVED] {filename}")
        else:
            print("[ERROR] Could not decode JPEG")

    except Exception as e:
        print(f"[ERROR] Failed to handle packet: {e}")
