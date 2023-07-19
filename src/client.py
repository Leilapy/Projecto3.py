"""
TFTPy - This module implements an interactive and command line TFTP 
client.

This client accepts the following options:
    $ python3 client.py [-p serv_port] server
    $ python3 client.py get [-p serv_port] server remote_file [local_file] 
    $ python3 client.py put [-p serv_port] server local_file [remote_file]

(C) João Galamba, 2023
"""


def main():
    print("TFTPy - Cliente de TFTP (em desenvolvimento)")
    print("Usage:")
    print("""\
$ python3 client.py [-p serv_port] server
$ python3 client.py get [-p serv_port] server remote_file [local_file] 
$ python3 client.py put [-p serv_port] server local_file [remote_file]
    """)
#:

if __name__ == '__main__':
    main()
#:
