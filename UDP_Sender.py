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

    new_axis4 = abs(90 - new_axis1)

    return (new_axis1, new_axis2, -1 * (new_axis3 - 0.05), new_axis4)

# Possible commands are:
# axisx:x - Moves axis x to location x
# force_data - Makes robot controller print out force sensor data
# close_gripper - Closes the gripper
# open_gripper - Opens the gripper
# tp_robot:x:y:z - Teleports the robot to given x, y, and z coordinates
if __name__ == '__main__':
    commands = [
        "axis1:99.09034842937326",
        "axis2:0.44404",
        "axis3:-1.215889015711883",
    ]
    target_location = (1.24999, -0.2, 0.44404)
    new_positions = compute_axis_positions(target_location)
    print("New axis positions:", new_positions)

    #send_commands_at_rate(commands, frequency=10)
