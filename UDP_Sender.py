import socket
import time

def send_udp_command(message, host='127.0.0.1', port=9999):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(message.encode('utf-8'), (host, port))
        print(f"Sent command: {message}")

def test():
    send_udp_command("axis:2:0.5")

def defaultScenario():
    send_udp_command("axis:1:90")
    time.sleep(3.0)
    send_udp_command("axis:2:0.5")
    time.sleep(3.0)
    send_udp_command("axis:3:-1.45")
    time.sleep(3.0)
    send_udp_command("force_data")
    time.sleep(1)
    send_udp_command("axis:2:0.05")
    time.sleep(3.0)
    send_udp_command("close_gripper")
    time.sleep(1)
    send_udp_command("axis:2:0.75")
    time.sleep(3)
    send_udp_command("force_data")
    time.sleep(1)
    send_udp_command("axis:1:0")
    time.sleep(3)
    send_udp_command("open_gripper")


if __name__ == '__main__':
    #test()
    defaultScenario()