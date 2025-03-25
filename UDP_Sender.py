import socket
import time

def send_udp_command(udp_socket, message, host, port):
    udp_socket.sendto(message.encode('utf-8'), (host, port))
    print(f"Sent command: {message}")

def send_commands_at_rate(commands, host='127.0.0.1', port=9999, frequency=200): # Frequency is the hz we send commands at
    interval = 1.0 / frequency
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for command in commands:
            send_udp_command(udp_socket, command, host, port)
            time.sleep(interval)
    finally:
        udp_socket.close()


# Possible commands are:
# axis:x:x - Moves axis x to location x
# force_data - Makes robot controller print out force sensor data
# close_gripper - Closes the gripper
# open_gripper - Opens the gripper
if __name__ == '__main__':
    commands = [
        "axis:2:0.51",
        "axis:2:0.52",
        "axis:2:0.53",
        "axis:2:0.54",
        "axis:2:0.55",
        "axis:2:0.56",
        "axis:2:0.57",
        "axis:2:0.58",
        "axis:2:0.59",
        "axis:2:0.60",
        "axis:2:0.61",
        "axis:2:0.62",
        "axis:2:0.63",
        "axis:2:0.64",
        "axis:2:0.65",
        "axis:2:0.66",
        "axis:2:0.67",
        "axis:2:0.68",
        "axis:2:0.69",
        "axis:2:0.70",
    ]
    send_commands_at_rate(commands, frequency=10)