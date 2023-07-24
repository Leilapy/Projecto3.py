import socket
import os
import struct
import threading

MAX_DATA_LEN = 512
RRQ = 1
WRQ = 2
DAT = 3
ACK = 4
ERR = 5
DEFAULT_PORT = 69
DEFAULT_DIR = "./data/"

def send_err_packet(sock, error_code, error_msg, client_address):
    err_packet = struct.pack('!H', ERR) + struct.pack('!H', error_code) + error_msg.encode() + b'\x00'
    sock.sendto(err_packet, client_address)

def handle_rrq(sock, client_address, filename):
    try:
        with open(filename, 'rb') as file:
            block_number = 1
            while True:
                data = file.read(MAX_DATA_LEN)
                if not data:
                    break
                dat_packet = struct.pack('!H', DAT) + struct.pack('!H', block_number) + data
                sock.sendto(dat_packet, client_address)

                ack_packet, addr = sock.recvfrom(4)
                ack_opcode, ack_block = struct.unpack('!HH', ack_packet)
                if ack_opcode != ACK or ack_block != block_number:
                    raise Exception("Invalid ACK received")
                
                block_number += 1
    except FileNotFoundError:
        send_err_packet(sock, 1, "File not found", client_address)

def handle_request(sock, client_address, data):
    opcode = struct.unpack('!H', data[:2])[0]
    if opcode == RRQ:
        filename = data[2:data.index(b'\x00', 2)].decode()
        handle_rrq(sock, client_address, filename)
    else:
        # For simplicity, the server only handles RRQ requests
        send_err_packet(sock, 4, "Illegal TFTP operation", client_address)

def handle_client(sock, client_address):
    while True:
        data, _ = sock.recvfrom(8192)
        handle_request(sock, client_address, data)

def main():
    try:
        os.mkdir(DEFAULT_DIR)
    except FileExistsError:
        pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', DEFAULT_PORT))

    print(f"Waiting for requests on 'localhost' port {DEFAULT_PORT}")

    try:
        while True:
            data, client_address = sock.recvfrom(8192)
            client_thread = threading.Thread(target=handle_client, args=(sock, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
        sock.close()

if __name__ == '__main__':
    main()
