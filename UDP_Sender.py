import socket
import time
import math

def send_udp_command(sock, message, host, port):
    sock.sendto(message.encode('utf-8'), (host, port))
    print(f"Sent command: {message}")

def send_command_sets_at_rate(command_sets, host='127.0.0.1', port=9999, frequency=200):
    interval = 1.0 / frequency
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for command_set in command_sets:
            for cmd in command_set:
                send_udp_command(sock, cmd, host, port)
            time.sleep(interval)
    finally:
        sock.close()

def compute_axis_positions(target_position):
    x, y, z = target_position

    axis1_radians = math.atan2(x, y)
    axis1_degrees = math.degrees(axis1_radians)

    extension = math.hypot(x, y)

    axis2 = z

    axis4_degrees = axis1_degrees - 90

    axis3 = -1 * (extension - 0.05)

    return (axis1_degrees, axis2, axis3, axis4_degrees)

def generate_interpolated_commands_linear(current_axes, target_axes, move_duration, update_frequency):
    total_steps = int(move_duration * update_frequency)
    command_sets = []

    for i in range(total_steps):
        fraction = (i + 1) / total_steps
        interpolated_axes = tuple(
            current_axes[j] + fraction * (target_axes[j] - current_axes[j])
            for j in range(4)
        )

        command_set = [
            f"axis1:{interpolated_axes[0]}",
            f"axis2:{interpolated_axes[1]}",
            f"axis3:{interpolated_axes[2]}",
            f"axis4:{interpolated_axes[3]}"
        ]
        command_sets.append(command_set)

    return command_sets

def process_sequence(sequence, current_axes, update_frequency):
    all_command_sets = []

    for step in sequence:
        if step["type"] == "move":
            target_position = step["target"]
            move_duration = step.get("duration", 5.0)
            target_axes = compute_axis_positions(target_position)
            move_commands = generate_interpolated_commands_linear(current_axes, target_axes, move_duration, update_frequency)
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
                move_commands = generate_interpolated_commands_linear(current_axes, new_target_axes, move_duration, update_frequency)
                all_command_sets.extend(move_commands)
                current_axes = new_target_axes

            else:
                delay_steps = int(delay_duration * update_frequency)
                for _ in range(delay_steps):
                    all_command_sets.append([command_str])

        else:
            print("Unknown step type:", step["type"])
    return all_command_sets, current_axes

if __name__ == '__main__':
    update_frequency = 200
    current_axes = (0, 0, 0, 0)
    
    sequence = [
        {"type": "move", "target": (0, 0, 0.44403), "duration": 1.0},   # Raise axis2
        {"type": "command", "command": "axis1:90", "delay": 2.0},         # Rotate axis1 to 90
        {"type": "move", "target": (1.55, 0.2, 0.44403), "duration": 3.0}, # Move to box
        {"type": "move", "target": (1.55, 0.2, 0.37), "duration": 2.0},    # Lower axis2
        {"type": "command", "command": "close_gripper", "delay": 1.0},      # Close gripper
        {"type": "move", "target": (1.55, 0.2, 0.70), "duration": 2.0},    # Raise axis2
        {"type": "command", "command": "axis3:0", "delay": 2.0},            # Retract axis3
        {"type": "command", "command": "axis1:0", "delay": 2.0},            # Rotate axis1 back to 0
        {"type": "move", "target": (0, 1, 0.5), "duration": 3.0},         # Move to stack position
        {"type": "command", "command": "open_gripper", "delay": 1.0},         # Open gripper
        {"type": "move", "target": (0, 1, 0.6), "duration": 2.0},         # Raise axis2
        {"type": "move", "target": (0, 0, 0.6), "duration": 3.0},             # Return to home 1
        {"type": "move", "target": (0, 0, 0.0), "duration": 3.0},             # Return to home 2
    ]
    
    all_command_sets, final_axes = process_sequence(sequence, current_axes, update_frequency)

    send_command_sets_at_rate(all_command_sets, frequency=update_frequency)
