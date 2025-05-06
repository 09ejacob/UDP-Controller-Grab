import socket
import time
import math


def send_udp_command(sock, message, host, port):
    sock.sendto(message.encode("utf-8"), (host, port))
    print(f"Sent command: {message}")


def send_command_sets_at_rate(command_sets, host="127.0.0.1", port=9999, frequency=200):
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
    axis3_extension = extension - 0.05
    return (axis1_angle, axis2_position, axis3_extension, axis4_angle)


def generate_interpolated_commands_linear(
    current_axes, target_axes, move_duration, frequency
):
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
            f"axis4:{interpolated_axes[3]}",
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

            if "rotation" in step:
                target_axes = (
                    target_axes[0],
                    target_axes[1],
                    target_axes[2],
                    target_axes[3] + step["rotation"],
                )

            move_commands = generate_interpolated_commands_linear(
                current_axes, target_axes, move_duration, frequency
            )
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
                move_commands = generate_interpolated_commands_linear(
                    current_axes, new_target_axes, move_duration, frequency
                )
                all_command_sets.extend(move_commands)
                current_axes = new_target_axes
            else:
                delay_steps = int(delay_duration * frequency)
                for _ in range(delay_steps):
                    all_command_sets.append([command_str])
        else:
            print("Unknown step type:", step["type"])
    return all_command_sets, current_axes


def add_safety_margin(original_number, positive=True):
    margin = 0.025 if positive else -0.025

    return original_number + margin


def pick_and_stack_box(
    box_position, stack_position, stack_rotation, safety_x, safety_y, delay
):
    sequence = [
        {
            "type": "command",
            "command": "axis1:-90",
            "delay": 2.0 / delay,
        },  # Turn towards the pallet
        {
            "type": "command",
            "command": f"axis2:{box_position[2]}",
            "delay": 1.0,
        },  # Raise axis2
        {
            "type": "move",
            "target": (box_position[0], box_position[1], box_position[2] + 0.15),
            "duration": 3.0 / delay,
        },  # Move axes to the box position
        {
            "type": "move",
            "target": (box_position[0], box_position[1], box_position[2] - 0.15),
            "duration": 2.0 / delay,
        },  # Lower axis2
        {
            "type": "command",
            "command": "close_gripper",
            "delay": 1.0 / delay,
        },  # Close gripper
        {
            "type": "command",
            "command": "capture:baseCamera:boxCamera1:boxCamera2",
            "delay": 1 / frequency,
        },  # Take picture
        {
            "type": "move",
            "target": (box_position[0], box_position[1], box_position[2] + 0.3),
            "duration": 2.0 / delay,
        },  # Raise axis2
        {
            "type": "command",
            "command": "axis3:0",
            "delay": 2.0 / delay,
        },  # Retract axis3
        {
            "type": "command",
            "command": "axis1:0",
            "delay": 2.0 / delay,
        },  # Straighten axis1
        {
            "type": "command",
            "command": "axis2:0.5",
            "delay": 2.0 / delay,
        },  # Set axis2 to 0.5
        {
            "type": "command",
            "command": f"axis2:{stack_position[2] + 0.3}",
            "delay": 2.0 / delay,
        },  # Raise axis2
        {
            "type": "move",
            "target": (
                add_safety_margin(stack_position[0], safety_x),
                add_safety_margin(stack_position[1], safety_y),
                stack_position[2] + 0.3,
            ),
            "duration": 4.0 / delay,
            "rotation": stack_rotation,
        },  # Move towards stack position
        {
            "type": "move",
            "target": (stack_position[0], stack_position[1], stack_position[2] - 0.2),
            "duration": 1.0 / delay,
            "rotation": stack_rotation,
        },  # Lower axis2
        {
            "type": "command",
            "command": "add_colliding_item",
            "delay": 1.0 / frequency,
        },  # Add item to robots pallet prim
        {
            "type": "command",
            "command": "open_gripper",
            "delay": 1.0 / delay,
        },  # Open gripper
        {
            "type": "command",
            "command": "capture:baseCamera:boxCamera1:boxCamera2",
            "delay": 1 / frequency,
        },  # Take picture
        {
            "type": "move",
            "target": (stack_position[0], stack_position[1], stack_position[2] + 0.2),
            "duration": 2.0 / delay,
            "rotation": stack_rotation,
        },  # Raise axis2
        {
            "type": "command",
            "command": "axis3:0",
            "delay": 2.0 / delay,
        },  # Retract axis3
        {
            "type": "command",
            "command": "axis2:0",
            "delay": 2.0 / delay,
        },  # Set axis2 to 0
    ]
    return sequence


def pick_and_stack_bottle(bottles_position, stack_position, stack_rotation, delay):
    sequence = [
        {
            "type": "command",
            "command": "axis1:-90",
            "delay": 2.0 / delay,
        },  # Turn towards the pallet
        {
            "type": "command",
            "command": f"axis2:{bottles_position[2]}",
            "delay": 1.0,
        },  # Raise axis2
        {
            "type": "move",
            "target": (
                bottles_position[0],
                bottles_position[1],
                bottles_position[2] + 0.3,
            ),
            "duration": 3.0 / delay,
        },  # Move axes to the box position
        {
            "type": "command",
            "command": "open_gripper",
            "delay": 1 / frequency,
        },  # Open bottlegripper
        {
            "type": "move",
            "target": (
                bottles_position[0],
                bottles_position[1],
                bottles_position[2] + 0.15,
            ),
            "duration": 2.0 / delay,
        },  # Lower axis2
        {
            "type": "command",
            "command": "close_gripper",
            "delay": 1.0 / delay,
        },  # Close gripper
        {
            "type": "command",
            "command": "capture:baseCamera:boxCamera1:boxCamera2",
            "delay": 1 / frequency,
        },  # Take picture
        {
            "type": "move",
            "target": (
                bottles_position[0],
                bottles_position[1],
                bottles_position[2] + 0.45,
            ),
            "duration": 2.0 / delay,
        },  # Raise axis2
        {
            "type": "command",
            "command": "axis3:0",
            "delay": 2.0 / delay,
        },  # Retract axis3
        {
            "type": "command",
            "command": "axis1:0",
            "delay": 2.0 / delay,
        },  # Straighten axis1
        {
            "type": "command",
            "command": "axis2:0.5",
            "delay": 2.0 / delay,
        },  # Set axis2 to 0.5
        {
            "type": "command",
            "command": f"axis2:{stack_position[2] + 0.3}",
            "delay": 2.0 / delay,
        },  # Raise axis2
        {
            "type": "move",
            "target": (stack_position[0], stack_position[1], stack_position[2] + 0.3),
            "duration": 3.0 / delay,
            "rotation": stack_rotation,
        },  # Move towards stack position
        {
            "type": "move",
            "target": (
                stack_position[0],
                stack_position[1],
                stack_position[2] + 0.1375,
            ),
            "duration": 1.0 / delay,
            "rotation": stack_rotation,
        },  # Lower axis2
        {
            "type": "command",
            "command": "add_colliding_item",
            "delay": 1.0 / frequency,
        },  # Add item to robots pallet prim
        {
            "type": "command",
            "command": "open_gripper",
            "delay": 1.0 / delay,
        },  # Open gripper
        {
            "type": "command",
            "command": "capture:baseCamera:boxCamera1:boxCamera2",
            "delay": 1 / frequency,
        },  # Take picture
        {
            "type": "move",
            "target": (stack_position[0], stack_position[1], stack_position[2] + 0.3),
            "duration": 2.0 / delay,
            "rotation": stack_rotation,
        },  # Raise axis2
        {
            "type": "command",
            "command": "axis3:0",
            "delay": 2.0 / delay,
        },  # Retract axis3
        {
            "type": "command",
            "command": "axis2:0.1",
            "delay": 2.0 / delay,
        },  # Set axis2 to 0
    ]
    return sequence


if __name__ == "__main__":
    frequency = 200
    delay = 1

    current_axes = (0, 0, 0, 0)

    pick_sequence_box1_1 = pick_and_stack_box(
        (-1.55, -0.2, 0.644), (-0.2, 1.625, 0.744), 90, False, False, delay
    )
    pick_sequence_box1_2 = pick_and_stack_box(
        (-1.25, 0.2, 2.644), (0.2, 1.625, 0.744), 90, True, False, delay
    )
    pick_sequence_box1_3 = pick_and_stack_box(
        (-1.55, -1.1 + 1, 0.644), (0.2, 0.325 + 1, 0.744), 90, True, False, delay
    )  # Plus 1 to the y axis because we teleport the robot

    # Stack 1
    pick_sequence_box2_1 = pick_and_stack_box(
        (-1.55, -0.2, 0.644), (-0.2, 1.625, 0.744), 90, False, False, delay
    )
    pick_sequence_box2_2 = pick_and_stack_box(
        (-1.85, 0.2, 0.644), (0.2, 1.625, 0.744), 90, True, False, delay
    )
    pick_sequence_box2_3 = pick_and_stack_box(
        (-1.85, -0.2, 0.644), (0.2, 1.325, 0.744), 90, True, False, delay
    )
    pick_sequence_box2_4 = pick_and_stack_box(
        (-0.95, 0.2, 0.444), (-0.2, 1.325, 0.744), 90, False, False, delay
    )
    pick_sequence_box2_5 = pick_and_stack_box(
        (-0.95, -0.2, 0.444), (-0.2, 1.025, 0.744), 90, False, False, delay
    )
    pick_sequence_box2_6 = pick_and_stack_box(
        (-1.25, 0.2, 0.444), (0.2, 1.025, 0.744), 90, True, False, delay
    )
    pick_sequence_box2_7 = pick_and_stack_box(
        (-1.25, -0.2, 0.444), (-0.2, 0.725, 0.744), 90, False, False, delay
    )
    pick_sequence_box2_8 = pick_and_stack_box(
        (-1.55, 0.2, 0.444), (0.2, 0.725, 0.744), 90, True, False, delay
    )
    # Stack 2
    pick_sequence_box2_9 = pick_and_stack_box(
        (-1.25, 0.2, 2.644), (-0.2, 1.625, 0.944), 90, False, False, delay
    )
    pick_sequence_box2_10 = pick_and_stack_box(
        (-1.25, -0.2, 2.644), (0.2, 1.625, 0.944), 90, True, False, delay
    )
    pick_sequence_box2_11 = pick_and_stack_box(
        (-1.55, 0.2, 2.644), (0.2, 1.325, 0.944), 90, True, False, delay
    )
    pick_sequence_box2_12 = pick_and_stack_box(
        (-1.55, -0.2, 2.644), (-0.2, 1.325, 0.944), 90, False, False, delay
    )
    pick_sequence_box2_13 = pick_and_stack_box(
        (-1.85, 0.2, 2.644), (-0.2, 1.025, 0.944), 90, False, False, delay
    )
    pick_sequence_box2_14 = pick_and_stack_box(
        (-1.85, -0.2, 2.644), (0.2, 1.025, 0.944), 90, True, False, delay
    )
    pick_sequence_box2_15 = pick_and_stack_box(
        (-0.95, 0.2, 2.444), (-0.2, 0.725, 0.944), 90, False, False, delay
    )
    pick_sequence_box2_16 = pick_and_stack_box(
        (-0.95, -0.2, 2.444), (0.2, 0.725, 0.944), 90, True, False, delay
    )
    # Stack 3
    pick_sequence_box2_17 = pick_and_stack_box(
        (-1.55, -1.1 + 1, 0.644), (-0.2, 1.625, 1.144), 90, False, False, delay
    )
    pick_sequence_box2_18 = pick_and_stack_box(
        (-1.55, -0.7 + 1, 0.644), (0.2, 1.625, 1.144), 90, True, False, delay
    )
    pick_sequence_box2_19 = pick_and_stack_box(
        (-1.85, -0.7 + 1, 0.644), (0.2, 1.325, 1.144), 90, True, False, delay
    )
    pick_sequence_box2_20 = pick_and_stack_box(
        (-1.85, -1.1 + 1, 0.644), (-0.2, 1.325, 1.144), 90, False, False, delay
    )
    pick_sequence_box2_21 = pick_and_stack_box(
        (-0.95, -1.1 + 1, 0.444), (-0.2, 1.025, 1.144), 90, False, False, delay
    )
    pick_sequence_box2_22 = pick_and_stack_box(
        (-0.95, -0.7 + 1, 0.444), (0.2, 1.025, 1.144), 90, True, False, delay
    )
    pick_sequence_box2_23 = pick_and_stack_box(
        (-1.25, -1.1 + 1, 0.444), (-0.2, 0.725, 1.144), 90, False, False, delay
    )
    pick_sequence_box2_24 = pick_and_stack_box(
        (-1.25, -0.7 + 1, 0.444), (0.2, 0.725, 1.144), 90, True, False, delay
    )

    pick_sequence_bottles_1 = pick_and_stack_bottle(
        (-0.95, 1.0 - 1, 0.145), (-0.3, 2.625 - 1, 0.644), 90, delay
    )
    pick_sequence_bottles_2 = pick_and_stack_bottle(
        (-0.95, 0.8 - 1, 1.945), (0, 2.625 - 1, 0.644), 90, delay
    )
    pick_sequence_bottles_3 = pick_and_stack_bottle(
        (-0.95, -1.2 + 1, 1.945), (0.3, 0.65 + 1, 0.644), 90, delay
    )

    small_sequence_box = (
        pick_sequence_box1_1
        + pick_sequence_box1_2
        + [{"type": "command", "command": "tp_robot:0:-1:0", "delay": 1.0}]
        + pick_sequence_box1_3
        + [{"type": "command", "command": "wait", "delay": 1.0}]
    )

    big_sequence_box = (
        pick_sequence_box2_1
        + pick_sequence_box2_2
        + pick_sequence_box2_3
        + pick_sequence_box2_4
        + pick_sequence_box2_5
        + pick_sequence_box2_6
        + pick_sequence_box2_7
        + pick_sequence_box2_8
        + pick_sequence_box2_9
        + pick_sequence_box2_10
        + pick_sequence_box2_11
        + pick_sequence_box2_12
        + pick_sequence_box2_13
        + pick_sequence_box2_14
        + pick_sequence_box2_15
        + pick_sequence_box2_16
        + [{"type": "command", "command": "tp_robot:0:-1:0", "delay": 1.0 / frequency}]
        + pick_sequence_box2_17
        + pick_sequence_box2_18
        + pick_sequence_box2_19
        + pick_sequence_box2_20
        + pick_sequence_box2_21
        + pick_sequence_box2_22
        + pick_sequence_box2_23
        + pick_sequence_box2_24
        + [{"type": "command", "command": "wait", "delay": 1.0}]
    )

    small_sequence_bottles = (
        [{"type": "command", "command": "tp_robot:0:1:0", "delay": 1.0}]
        + pick_sequence_bottles_1
        + pick_sequence_bottles_2
        + [{"type": "command", "command": "tp_robot:0:-1:0", "delay": 1.0}]
        + pick_sequence_bottles_3
        + [{"type": "command", "command": "wait", "delay": 1.0}]
    )

    all_command_sets, final_axes = process_sequence(
        small_sequence_box, current_axes, frequency
    )

    start_time = time.time()

    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # send_udp_command(udp_socket, "start_overview_camera:1", "127.0.0.1", 9999)
    # udp_socket.close()

    send_command_sets_at_rate(all_command_sets, frequency=frequency)

    end_time = time.time()
    execution_time = end_time - start_time

    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # send_udp_command(udp_socket, "stop_overview_camera", "127.0.0.1", 9999)
    # udp_socket.close()

    print(f"Total execution time: {execution_time:.2f} seconds")
    print("Program done.")
