import socket
import time


def send_udp_command(message, host="127.0.0.1", port=9999):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(message.encode("utf-8"), (host, port))

        print(f"Sent command: {message}")


def test():
    # send_udp_command("axis1:90")
    # send_udp_command("close_gripper")
    # send_udp_command("open_gripper")
    # send_udp_command("capture")
    # send_udp_command("tp_robot:-1:-2:0")
    # send_udp_command("start_overview_camera")
    # time.sleep(2)
    # send_udp_command("stop_overview_camera")
    # send_udp_command("reload:Grab.usd")
    # send_udp_command("add_colliding_item")
    # send_udp_command("axis1:-95")
    # time.sleep(0.5)
    # send_udp_command("axis2:0.7")
    # time.sleep(0.5)
    # send_udp_command("axis3:1.5")
    # time.sleep(0.5)
    # send_udp_command("axis2:0.5")
    # time.sleep(0.5)
    # send_udp_command("close_gripper")
    # time.sleep(0.5)
    # send_udp_command("axis2:0.7")
    # time.sleep(0.5)
    # send_udp_command("open_gripper")
    # time.sleep(0.5)

    send_udp_command("capture:boxCamera1:stream=true")


def default_scenario():
    send_udp_command("axis:1:90")
    time.sleep(3.0)
    send_udp_command("axis:2:0.5")
    time.sleep(3.0)
    send_udp_command("axis:3:-1.45")
    time.sleep(3.0)
    force_sensor()
    time.sleep(1)
    send_udp_command("axis:2:0.05")
    time.sleep(3.0)
    send_udp_command("close_gripper")
    time.sleep(1)
    send_udp_command("axis:2:0.75")
    time.sleep(3)
    force_sensor()
    time.sleep(1)
    send_udp_command("axis:1:0")
    time.sleep(3)
    send_udp_command("open_gripper")


def force_sensor():
    send_udp_command("force_data")


if __name__ == "__main__":
    # while True:
    #     force_sensor()
    #     time.sleep(0.1)
    # while True:
    #     test()
    #     time.sleep(0.1)
    # while True:
    #     # force_sensor()
    #     test()
    #     time.sleep(0.1)
    test()
    # default_scenario()
    # time.sleep(0.5)
    # send_udp_command("capture")
