import socket
import time
import math

def send_udp_command(udp_socket, message, host, port):
    udp_socket.sendto(message.encode('utf-8'), (host, port))
    print(f"Sent command: {message}")

def send_commands_at_rate(commands, host='127.0.0.1', port=9999, frequency=200):  # Frequency is the Hz we send commands at
    interval = 1.0 / frequency
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for command in commands:
            send_udp_command(udp_socket, command, host, port)
            time.sleep(interval)
    finally:
        udp_socket.close()

def compute_axis_positions(target_location):
    target_x, target_y, target_z = target_location
    
    axis1_radians = math.atan2(target_x, target_y)
    new_axis1 = math.degrees(axis1_radians)
    
    new_axis3 = math.hypot(target_x, target_y)
    
    new_axis2 = target_z

    new_axis4 = (new_axis1 - 90)

    return (new_axis1, new_axis2, -1 * (new_axis3 - 0.05), new_axis4)

if __name__ == '__main__':
    target_location = (1.55, 0.2, 0.44403)
    new_positions = compute_axis_positions(target_location)
    new_axis1, new_axis2, new_axis3, new_axis4 = new_positions

    commands = [
        f"axis1:{new_axis1}",
        f"axis2:{new_axis2}",
        f"axis3:{new_axis3}",
        f"axis4:{new_axis4}",
    ]

    print("New commands to send:", commands)
    send_commands_at_rate(commands, frequency=2)
