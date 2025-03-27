from flask import Flask, request, render_template
import socket

app = Flask(__name__)

UDP_HOST = "127.0.0.1"
UDP_PORT = 9999


def send_udp_command(message, host=UDP_HOST, port=UDP_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(message.encode("utf-8"), (host, port))
        print(f"Sent command: {message}")


@app.route("/")
def index():
    # Renders templates/index.html
    return render_template("index.html")


@app.route("/set_target", methods=["POST"])
def set_target():
    """Handles slider changes from the client."""
    data = request.get_json()
    if not data or "axis" not in data or "target" not in data:
        return "Missing axis or target value", 400

    axis = data["axis"]
    target_val = data["target"]

    message = f"axis{axis}:{target_val}"
    send_udp_command(message)
    return f"Command sent: {message}"


@app.route("/set_gripper", methods=["POST"])
def set_gripper():
    """Handles open/close gripper button presses."""
    data = request.get_json()
    if not data or "action" not in data:
        return "Missing gripper action", 400

    action = data["action"].strip().lower()
    if action == "open":
        send_udp_command("open_gripper")
        return "Opened gripper"
    elif action == "close":
        send_udp_command("close_gripper")
        return "Closed gripper"
    else:
        return f"Unknown gripper action '{action}'", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
