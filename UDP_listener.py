import socket
import struct
import json
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt

SAVE_DIR = "received_images"
PLOT_BASE = "force_plots"

timestamp_folder = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
PLOT_DIR = os.path.join(PLOT_BASE, timestamp_folder)

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

# ← Add this at the module level:
fragment_buffer = {}  # msg_id (bytes) → {'total':int, 'chunks':{idx:bytes}}

image_counter = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9998))
print("Listening for UDP messages...")

collecting = False
force_values = []
time_values = []
segment_idx = 0
start_time = None

try:
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
while True:
    data, addr = sock.recvfrom(65535)

    # Try to reassemble fragments
    if len(data) >= 12:
        msg_id = data[:8]
        total_chunks, idx = struct.unpack("!HH", data[8:12])
        # only treat it as a fragment if total_chunks>1 (and sane)
        if 1 < total_chunks < 20 and idx < total_chunks:
            buf = fragment_buffer.setdefault(
                msg_id, {"total": total_chunks, "chunks": {}}
            )
            buf["chunks"][idx] = data[12:]
            if len(buf["chunks"]) < buf["total"]:
                continue
            full = b"".join(buf["chunks"][i] for i in range(buf["total"]))
            del fragment_buffer[msg_id]
            data = full

    try:
        text = data.decode("utf-8")
        if text.startswith("{") and text.endswith("}"):
            print("[TEXT] Received JSON:", text)
        else:
            print("[TEXT] Received:", text)
        continue

        if txt and txt.startswith("{") and txt.endswith("}"):
            print(txt)
            continue

    try:
        if len(data) < 4:
            print("Packet too short.")
            continue

        meta_len = struct.unpack("!I", data[:4])[0]
        if len(data) < 4 + meta_len:
            print("Packet missing image data.")
            continue

        metadata = json.loads(data[4 : 4 + meta_len].decode("utf-8"))
        jpeg_bytes = data[4 + meta_len :]

        metadata = json.loads(metadata_bytes.decode("utf-8"))
        camera_id = metadata.get("camera_id", "unknown")
        frame_id = metadata.get("frame_id", 0)
        timestamp = metadata.get("timestamp", datetime.now().isoformat())

        print(f"[IMAGE] From {camera_id} | Frame {frame_id} | Time {timestamp}")

        # Decode and save the JPEG
        jpeg_array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        image = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)

        if image is not None:
            safe_ts = timestamp.replace(":", "-").replace("T", "_").replace("Z", "")
            filename = f"{camera_id}_{safe_ts}_{frame_id:04d}.jpg"
            cv2.imwrite(os.path.join(SAVE_DIR, filename), image)
            print(f"[SAVED] {filename}")
        else:
            print("[ERROR] Could not decode JPEG")

    except Exception as e:
        print(f"[ERROR] Failed to handle packet: {e}")
