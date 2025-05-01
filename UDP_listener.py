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

        if txt and txt.startswith("{") and txt.endswith("}"):
            print(txt)
            continue

        if len(data) < 4:
            print("Packet too short.")
            continue

        meta_len = struct.unpack("!I", data[:4])[0]
        if len(data) < 4 + meta_len:
            print("Packet missing image data.")
            continue

        metadata = json.loads(data[4 : 4 + meta_len].decode("utf-8"))
        jpeg_bytes = data[4 + meta_len :]
        cam = metadata.get("camera_id", "unknown")
        frame = metadata.get("frame_id", 0)
        ts = metadata.get("timestamp", datetime.now().isoformat())
        safe_ts = ts.replace(":", "-").replace("T", "_").replace("Z", "")

        fname = f"{cam}_{safe_ts}_{frame:04d}.jpg"
        path = os.path.join(SAVE_DIR, fname)

        with open(path, "wb") as f:
            f.write(jpeg_bytes)

        print(f"Saved: {fname}")

except KeyboardInterrupt:
    print("\nInterrupted.")

    if collecting and force_values:
        fn = os.path.join(PLOT_DIR, f"segment_{segment_idx:03d}.jpg")

        plt.figure()
        plt.plot(time_values, force_values)
        plt.xlabel("Time (s)")
        plt.ylabel("Force (N)")
        plt.title(f"Force Segment {segment_idx}")
        plt.savefig(fn)
        plt.close()

        print(f"Plot saved {fn}")

    print("Done.")
