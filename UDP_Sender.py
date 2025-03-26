import socket
import time
import math

def send_udp_command(sock, message, host, port):
    sock.sendto(message.encode('utf-8'), (host, port))
    print(f"Sent command: {message}")

def send_command_sets_at_rate(command_sets, host='127.0.0.1', port=9999, frequency=200):
    interval = 1.0 / frequency
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for command_set in command_sets:
            for command in command_set:
                send_udp_command(udp_socket, command, host, port)
            time.sleep(interval)
    finally:
        udp_socket.close()

def compute_axis_positions(target_position):
    target_x, target_y, target_z = target_position
    axis1_angle = math.degrees(math.atan2(target_x, target_y))
    extension = math.hypot(target_x, target_y)
    axis2_position = target_z
    axis4_angle = axis1_angle - 90
    axis3_extension = -1 * (extension - 0.05)
    return (axis1_angle, axis2_position, axis3_extension, axis4_angle)

def generate_interpolated_commands_linear(current_axes, target_axes, move_duration, frequency):
    num_steps = int(move_duration * frequency)
    command_sets = []
    for step in range(num_steps):
        fraction = (step + 1) / num_steps
        interpolated_axes = tuple(
            current_axes[i] + fraction * (target_axes[i] - current_axes[i])
            for i in range(4)
        )
        command_set = [
            f"axis1:{interpolated_axes[0]}",
            f"axis2:{interpolated_axes[1]}",
            f"axis3:{interpolated_axes[2]}",
            f"axis4:{interpolated_axes[3]}"
        ]
        command_sets.append(command_set)
    return command_sets

def process_sequence(sequence, current_axes, frequency):
    all_command_sets = []
    for step in sequence:
        if step["type"] == "move":
            target_position = step["target"]
            move_duration = step.get("duration", 5.0)
            target_axes = compute_axis_positions(target_position)
            move_commands = generate_interpolated_commands_linear(current_axes, target_axes, move_duration, frequency)
            all_command_sets.extend(move_commands)
            current_axes = target_axes
        elif step["type"] == "command":
            command_str = step["command"]
            delay_duration = step.get("delay", 1.0)
            if command_str.startswith("axis"):
                parts = command_str.split(":")
                axis_label = parts[0]
                new_value = float(parts[1])
                axis_index = int(axis_label[4:]) - 1
                new_target_axes = list(current_axes)
                new_target_axes[axis_index] = new_value
                new_target_axes = tuple(new_target_axes)
                move_duration = delay_duration
                move_commands = generate_interpolated_commands_linear(current_axes, new_target_axes, move_duration, frequency)
                all_command_sets.extend(move_commands)
                current_axes = new_target_axes
            else:
                delay_steps = int(delay_duration * frequency)
                for _ in range(delay_steps):
                    all_command_sets.append([command_str])
        else:
            print("Unknown step type:", step["type"])
    return all_command_sets, current_axes

def pick_and_stack_box(box_position, stack_position):
    sequence = [
        {"type": "command", "command": "axis1:90", "delay": 2.0},
        {"type": "command", "command": f"axis2:{box_position[2]}", "delay": 1.0},
        {"type": "move", "target": (box_position[0], box_position[1], box_position[2] + 0.15), "duration": 3.0},
        {"type": "move", "target": (box_position[0], box_position[1], box_position[2] - 0.1), "duration": 2.0},
        {"type": "command", "command": "close_gripper", "delay": 1.0},
        {"type": "move", "target": (box_position[0], box_position[1], box_position[2] + 0.3), "duration": 2.0},
        {"type": "command", "command": "axis3:0", "delay": 2.0},
        {"type": "command", "command": "axis1:0", "delay": 2.0},
        {"type": "move", "target": (stack_position[0], stack_position[1], stack_position[2] + 0.2), "duration": 3.0},
        {"type": "move", "target": (stack_position[0], stack_position[1], stack_position[2] - 0.1), "duration": 1.0},
        {"type": "command", "command": "open_gripper", "delay": 1.0},
        {"type": "move", "target": (stack_position[0], stack_position[1], stack_position[2] + 0.2), "duration": 2.0},
        {"type": "command", "command": "axis3:0", "delay": 2.0},
        {"type": "command", "command": "axis2:0", "delay": 2.0},
    ]
    return sequence

if __name__ == '__main__':
    frequency = 200
    current_axes = (0, 0, 0, 0)
    pick_sequence1 = pick_and_stack_box((1.55, 0.2, 0.44403), (-0.35, 1.75, 0.6))
    #pick_sequence2 = pick_and_stack_box((1.24999, -0.2, 0.44403), (0, 1.75, 0.6))
    #pick_sequence3 = pick_and_stack_box((1.55, -0.2, 0.444), (0.35, 1.75, 0.6))
    pick_sequence2 = pick_and_stack_box((1.85002, -0.79999 + 1, 0.64409), (0, 1.75, 0.6)) # Plus 1 to the y axis because we teleport the robot
    pick_sequence3 = pick_and_stack_box((1.85001, -1.20001 + 1, 0.64407), (0.35, 1.75, 0.6)) # Plus 1 to the y axis because we teleport the robot
    
    full_sequence = (pick_sequence1 + 
                    [{"type": "command", "command": "nudge_box:/World/Environment/stack1/box_1_14:0:1:0", "delay": 1.0}] +
                    [{"type": "command", "command": "tp_robot:0:-1:0", "delay": 1.0}] +
                    pick_sequence2 +
                    [{"type": "command", "command": "wait", "delay": 1.0}]+
                    pick_sequence3 +
                    [{"type": "command", "command": "wait", "delay": 1.0}])
    
    all_command_sets, final_axes = process_sequence(full_sequence, current_axes, frequency)

    send_command_sets_at_rate(all_command_sets, frequency=frequency)
