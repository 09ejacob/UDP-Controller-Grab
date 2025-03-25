import socket
import time
import math

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



def compute_axis_moves(target_location, current_axes=(0.0, 0.0, 0.0)):
    x, y, z = target_location
    current_axis1, current_axis2, current_axis3 = current_axes

    desired_axis1 = math.degrees(math.atan2(y, x))
    desired_axis2 = z
    desired_axis3 = math.sqrt(x**2 + y**2)

    delta_axis1 = desired_axis1 - current_axis1
    delta_axis2 = desired_axis2 - current_axis2
    delta_axis3 = desired_axis3 - current_axis3

    return {"axis1": delta_axis1, "axis2": delta_axis2, "axis3": delta_axis3}


# Possible commands are:
# axisx:x - Moves axis x to location x
# force_data - Makes robot controller print out force sensor data
# close_gripper - Closes the gripper
# open_gripper - Opens the gripper
# tp_robot:x:y:z - Teleports the robot to given x, y, and z coordinates
if __name__ == '__main__':
    commands = [
        "axis2:0.51",
        "axis2:0.52",
        "axis2:0.53",
        "axis2:0.54",
        "axis2:0.55",
        "axis2:0.56",
        "axis2:0.57",
        "axis2:0.58",
        "axis2:0.59",
        "axis2:0.60",
        "axis2:0.61",
        "axis2:0.62",
        "axis2:0.63",
        "axis2:0.64",
        "axis2:0.65",
        "axis2:0.66",
        "axis2:0.67",
        "axis2:0.68",
        "axis2:0.69",
        "axis2:0.70",
        # "tp_robot:-2:-2:0"
    ]
    #send_commands_at_rate(commands, frequency=10)

    current_axes = (0.0, 0.0, 0.5)
    target_location = (1.24999, -0.2, 0.44404)
    moves = compute_axis_moves(target_location, current_axes)
    print("Axis moves required:", moves)
