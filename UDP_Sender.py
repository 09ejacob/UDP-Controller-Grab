import socket
import time

def send_udp_command(message, host='127.0.0.1', port=9999):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(message.encode('utf-8'), (host, port))
        print(f"Sent command: {message}")

def test():
    send_udp_command("axis:2:0.5")

def defaultScenario():
    #while True:
        send_udp_command("axis:2:0.5")
        #send_udp_command("axis:2:90.0")
        time.sleep(3.0)
        send_udp_command("force_data")
        time.sleep(3.0)
        send_udp_command("axis:2:0.0")
        time.sleep(3.0)
        send_udp_command("force_data")


if __name__ == '__main__':
    test()
    #defaultScenario()