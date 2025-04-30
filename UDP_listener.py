import socket
import struct
import json
import os
from datetime import datetime

SAVE_DIR = "received_images"
os.makedirs(SAVE_DIR, exist_ok=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9998))

print("Listening for UDP messages...")

while True:
    data, addr = sock.recvfrom(65535)

    try:
        txt = data.decode("utf-8")
        if txt.startswith("{") and txt.endswith("}"):
            print("[TEXT] Received JSON:", txt)
        else:
            print("[TEXT] Received:", txt)
        continue
    except UnicodeDecodeError:
        pass

    if len(data) < 4:
        print("[WARN] Packet too short.")
        continue

    meta_len = struct.unpack("!I", data[:4])[0]
    if len(data) < 4 + meta_len:
        print("[WARN] Packet missing image data.")
        continue

    metadata = json.loads(data[4 : 4 + meta_len].decode("utf-8"))
    jpeg_bytes = data[4 + meta_len :]

    cam = metadata.get("camera_id", "unknown")
    frame = metadata.get("frame_id", 0)
    ts = metadata.get("timestamp", datetime.now().isoformat())
    safe_ts = ts.replace(":", "-").replace("T", "_").replace("Z", "")

    fname = f"{cam}_{safe_ts}_{frame:04d}.jpg"
    path = os.path.join(SAVE_DIR, fname)

    # just write the raw JPEG bytes
    with open(path, "wb") as f:
        f.write(jpeg_bytes)

    print(f"[SAVED] {fname}")
