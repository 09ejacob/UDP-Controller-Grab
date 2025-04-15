import socket
import numpy as np
import cv2
import os
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
        print("Received TEXT:", text)

    except UnicodeDecodeError:
        # Assume binary JPEG image
        jpeg_array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)

        if image is not None:
            print(f"Received JPEG image: shape={image.shape}")

            # Save image to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"img_{timestamp}_{image_counter:04d}.jpg"
            cv2.imwrite(os.path.join(SAVE_DIR, filename), image)
            print(f"Saved image: {filename}")
            image_counter += 1

        else:
            print("Failed to decode JPEG image")
