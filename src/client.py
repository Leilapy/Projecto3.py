"""
TFTPy - This module implements an interactive and command line TFTP 
client.

This client accepts the following options:
    $ python3 client.py [-p serv_port] server
    $ python3 client.py get [-p serv_port] server remote_file [local_file] 
    $ python3 client.py put [-p serv_port] server local_file [remote_file]

(C) João Galamba, 2023 (Leila Cuber)
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
# arquivo: cliente.py

import sys
from tftp import TFTPClient

def interactive_client():
    """
    Cliente TFTP interativo.
    """
    print("Bem-vindo ao cliente TFTP interativo!")
    server = input("Digite o endereço do servidor TFTP: ")
    mode = input("Digite 'get' para obter um arquivo ou 'put' para enviar um arquivo: ")

    if mode not in ["get", "put"]:
        print("Modo inválido. Use 'get' ou 'put'.")
        return

    source_file = input("Digite o nome do arquivo no servidor (arquivo remoto): ")
    dest_file = input("Digite o nome do arquivo local (ou pressione Enter para manter o mesmo nome): ")
    dest_file = dest_file.strip() if dest_file.strip() else None

    client = TFTPClient(server)
    try:
        if mode == "get":
            client.get_file(source_file, dest_file)
            print(f"Arquivo '{source_file}' obtido com sucesso!")
        else:  # mode == "put"
            client.put_file(source_file, dest_file)
            print(f"Arquivo '{source_file}' enviado com sucesso!")
    except TFTPClient.Err as e:
        print(f"Erro TFTP {e.error_code}: {e.error_msg}")
    except TFTPClient.ProtocolError as pe:
        print(f"Erro de protocolo TFTP: {pe}")
    except Exception as ex:
        print(f"Erro desconhecido: {ex}")

def non_interactive_client():
    """
    Cliente TFTP não interativo.
    """
    if len(sys.argv) not in [4, 5]:
        print("Uso: python3 cliente.py (get|put) server source_file [dest_file]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode not in ["get", "put"]:
        print("Modo inválido. Use 'get' ou 'put'.")
        sys.exit(1)

    server = sys.argv[2]
    source_file = sys.argv[3]
    dest_file = sys.argv[4] if len(sys.argv) == 5 else None

    client = TFTPClient(server)
    try:
        if mode == "get":
            client.get_file(source_file, dest_file)
            print(f"Arquivo '{source_file}' obtido com sucesso!")
        else:  # mode == "put"
            client.put_file(source_file, dest_file)
            print(f"Arquivo '{source_file}' enviado com sucesso!")
    except TFTPClient.Err as e:
        print(f"Erro TFTP {e.error_code}: {e.error_msg}")
    except TFTPClient.ProtocolError as pe:
        print(f"Erro de protocolo TFTP: {pe}")
    except Exception as ex:
        print(f"Erro desconhecido: {ex}")

def main():
    if len(sys.argv) > 1:
        non_interactive_client()
    else:
        interactive_client()

if __name__ == "__main__":
    main()
