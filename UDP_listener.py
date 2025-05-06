import socket
import struct
import json
import os
import time
from datetime import datetime
import numpy as np
import cv2
import matplotlib.pyplot as plt

SAVE_DIR = "received_images"
PLOT_BASE = "force_plots"
timestamp_folder = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
PLOT_DIR = os.path.join(PLOT_BASE, timestamp_folder)

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

fragment_buffer = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9998))
print("Listening for UDP messages...")

collecting = False
force_values = []
time_values = []
segment_idx = 0
start_time = None

while True:
    data, addr = sock.recvfrom(65535)

    try:
        txt = data.decode("utf-8")
    except UnicodeDecodeError:
        txt = None

    if txt and txt.startswith("axis"):
        parts = txt.strip().split(";")
        try:
            d = {k: float(v) for k, v in (p.split(":") for p in parts)}
        except ValueError:
            continue

        force = d.get("force_N")
        if force is None:
            continue

        if force != 0.0:
            if not collecting:
                collecting = True
                force_values = []
                time_values = []
                start_time = time.time()
            t = time.time() - start_time
            force_values.append(force)
            time_values.append(t)

        elif collecting:
            fn = os.path.join(PLOT_DIR, f"segment_{segment_idx:03d}.jpg")
            plt.figure()
            plt.plot(time_values, force_values)
            plt.xlabel("Time (s)")
            plt.ylabel("Force (N)")
            plt.title(f"Force Segment {segment_idx}")
            plt.savefig(fn)
            plt.close()
            print(f"Plot saved {fn}")
            segment_idx += 1
            collecting = False

        print(txt)
        continue

    # Fragment reassembly
    if len(data) >= 12:
        msg_id = data[:8]
        total, idx = struct.unpack("!HH", data[8:12])
        if 1 < total < 20 and idx < total:
            buf = fragment_buffer.setdefault(msg_id, {"total": total, "chunks": {}})
            buf["chunks"][idx] = data[12:]
            if len(buf["chunks"]) < buf["total"]:
                continue
            data = b"".join(buf["chunks"][i] for i in range(buf["total"]))
            del fragment_buffer[msg_id]

    # JSON-only text messages
    try:
        text = data.decode("utf-8")
        if text.startswith("{") and text.endswith("}"):
            print("[TEXT] Received JSON:", text)
            continue
        else:
            print("[TEXT] Received:", text)
            continue
    except UnicodeDecodeError:
        pass

    # Image packet (4-byte len + JSON + JPEG)
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

    # Decode & save JPEG
    jpeg_array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    image = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)
    if image is not None:
        safe_ts = timestamp.replace(":", "-").replace("T", "_").replace("Z", "")
        filename = f"{camera_id}_{safe_ts}_{frame_id:04d}.jpg"
        cv2.imwrite(os.path.join(SAVE_DIR, filename), image)
        print(f"[SAVED] {filename}")
    else:
        print("[ERROR] Could not decode JPEG")
