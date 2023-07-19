"""
This module handles all TFTP related "stuff": data structures, packet 
definitions, methods and protocol operations.

(C) João Galamba, 2023
"""

import ipaddress
import re
import struct
import string
from socket import (
    socket,
    AF_INET, SOCK_DGRAM,
    herror,
    gaierror,
    gethostbyaddr,
    gethostbyname_ex,
)

###############################################################
##
##      PROTOCOL CONSTANTS AND TYPES
##
###############################################################

MAX_DATA_LEN = 512            # bytes
MAX_BLOCK_NUMBER = 2**16 - 1  # 0..65535
INACTIVITY_TIMEOUT = 25.0     # segs
DEFAULT_MODE = 'octet'
DEFAULT_BUFFER_SIZE = 8192    # bytes

# TFTP message opcodes
# RRQ, WRQ, DAT, ACK, ERR = range(1, 6)
RRQ = 1   # Read Request
WRQ = 2   # Write Request
DAT = 3   # Data transfer
ACK = 4   # Acknowledge DAT
ERR = 5   # Error packet; what the server responds if a read/write 
          # can't be processed, read and write errors during file 
          # transmission also cause this message to be sent, and 
          # transmission is then terminated. The error number gives a 
          # numeric error code, followed by an ASCII error message that
          # might contain additional, operating system specific 
          # information.

ERR_NOT_DEFINED = 0
ERR_FILE_NOT_FOUND = 1
ERR_ACCESS_VIOLATION = 2
# Acresentar códigos de erro em falta

ERROR_MESSAGES = {
    ERR_NOT_DEFINED: 'Not defined, see error message (if any)',
    ERR_FILE_NOT_FOUND: 'File not found',
    ERR_ACCESS_VIOLATION: 'Access violation',
    # Acresentar mensagens em falta
}

INET4Address = tuple[str, int]        # TCP/UDP address => IPv4 and port

###############################################################
##
##      SEND AND RECEIVE FILES
##
###############################################################

def get_file(server_addr: INET4Address, filename: str):
    """
    Get the remote file given by `filename` through a TFTP RRQ
    connection to remote server at `server_addr`.
    """
    with socket(AF_INET, SOCK_DGRAM) as sock:
        sock.settimeout(INACTIVITY_TIMEOUT)
        with open(filename, 'wb') as file:
            rrq = pack_rrq(filename)
            next_block_number = 1
            sock.sendto(rrq, server_addr)
            while True:
                packet, server_addr = sock.recvfrom(DEFAULT_BUFFER_SIZE)
                opcode = unpack_opcode(packet)

                if opcode == DAT:
                    block_number, data = unpack_dat(packet)
                    if block_number not in (next_block_number, next_block_number - 1):
                        raise ProtocolError(f'Unexpected block number: {block_number}')

                    if block_number == next_block_number:
                        file.write(data)
                        next_block_number += 1

                    ack = pack_ack(block_number)
                    sock.sendto(ack, server_addr)

                    if len(data) < 512:
                        break
                #:
                elif opcode == ERR:
                    error_code, error_msg = unpack_err(packet)
                    raise Err(error_code, error_msg)
                #:
                else:
                    raise ProtocolError(f'Invalid opcode: {opcode}')
        #:
    #:
#:

# def get_file(server_addr: INET4Address, filename: str):
    # 1. Criar um socket DGRAM para comunicar com servidor em server_addr
    # 2. Abrir um ficheiro local com nome 'filename' para escrita binária 
    # 3. Enviar RRQ para o servidor em server_addr
    # 4. Esperar por pacote enviado pelo servidor [1]
    #       4.1 Extrair opcode do pacote recebido
    #       4.2 Se opcode for DAT:
    #           a) Obter block_number e data (ie, o bloco de dados) (UNPACK)
    #           b) Se block_number não for next_block_number ou 
    #              next_block_number - 1 => ERRO de protocolo [2]
    #           c) Se block_number == next_block_number [3], gravamos
    #              bloco de dados no ficheiro e incrementamos next_block_number
    #           d) Enviar ACK reconhecendo o último pacote recebido
    #           e) Se bloco de dados < 512, terminar o RRQ
    #       4.3 Se pacote for ERR: assinalar o erro lançando a excepção apropriada
    #       4.4 Se for outro tipo de pacote: assinalar ERRO de protocolo
    #       4.5 Voltar a 4
    #
    # [1] Terminar quando dimensão do bloco de dados do pacote 
    #     DAT for < 512 bytes (ou se ocorrer um erro)
    # [2] next_block_number indica o próximo block_number. contador
    #     inicializado a 1 antes do passo 4.
    # [3] Isto quer dizer que recebemos um novo DAT
#:

def put_file():
    pass
#:

###############################################################
##
##      PACKET PACKING AND UNPACKING
##
###############################################################

def pack_rrq(filename: str, mode: str = DEFAULT_MODE):
    return pack_rrq_wrq(RRQ, filename, mode)
#:

def pack_wrq(filename: str, mode: str = DEFAULT_MODE):
    return pack_rrq_wrq(WRQ, filename, mode)
#:

def pack_rrq_wrq(opcode: int, filename: str, mode: str):
    if not is_ascii_printable(filename):
        raise ValueError(f"Invalid filename: {filename}. Not ASCII printable.")
    encoded_filename = filename.encode() + b'\x00'
    encoded_mode = mode.encode() + b'\x00'
    fmt = f'!H{len(encoded_filename)}s{len(encoded_mode)}s'
    return struct.pack(fmt, opcode, encoded_filename, encoded_mode)
#:

def unpack_rrq(packet: bytes) -> tuple[str, str]:
    return unpack_rrq_wrq(RRQ, packet)
#:

def unpack_wrq(packet: bytes) -> tuple[str, str]:
    return unpack_rrq_wrq(WRQ, packet)
#:

def unpack_rrq_wrq(opcode: int, packet: bytes) -> tuple[str, str]:
    received_opcode = unpack_opcode(packet)
    if received_opcode != opcode:
        raise ValueError(f"Invalid opcode: {received_opcode}. Expected opcode: {opcode}")
    delim_pos = packet.index(b'\x00', 2)
    filename = packet[2:delim_pos].decode()
    mode = packet[delim_pos + 1:-1].decode()
    return (filename, mode)
#:

def pack_dat(block_number: int, data: bytes) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        raise ValueError(f'Invalid block number: {block_number}')
    if len(data) > MAX_DATA_LEN:
        raise ValueError(f'Invalid data length: {len(data)}')

    fmt = f'!HH{len(data)}s'
    return struct.pack(fmt, DAT, block_number, data)
#:

def unpack_dat(packet: bytes) -> tuple[int, bytes]:
    opcode, block_number = struct.unpack('!HH', packet[:4])
    if opcode != DAT:
        raise ValueError(f'Invalid opcode: {opcode}')
    return block_number, packet[4:]
#:

def pack_ack(block_number: int) -> bytes:
    if not 0 <= block_number <= MAX_BLOCK_NUMBER:
        raise ValueError(f'Invalid block number: {block_number}')
    return struct.pack('!HH', ACK, block_number)
#:

def unpack_ack(packet: bytes) -> int:
    if len(packet) > 4:
        raise ValueError(f'Invalid packet length: {len(packet)}')
    opcode, block_number = struct.unpack('!HH', packet)
    if opcode != ACK:
        raise ValueError(f'Invalid opcode: {opcode}')
    return block_number
#:

def pack_err(error_code: int, error_msg: str) -> bytes:
    if error_code not in ERROR_MESSAGES:
        raise ValueError(f'Unknown error code {error_code}')
    
    encoded_error_msg = error_msg.encode() + b'\x00'
    fmt = f'!HH{len(encoded_error_msg)}s'
    return struct.pack(fmt, ERR, error_code, encoded_error_msg)
#:

def unpack_err(packet: bytes) -> tuple[int, str]:
    fmt = f'!HH{len(packet)-4}s'
    opcode, error_num, error_msg = struct.unpack(fmt, packet)
    if opcode != ERR:
        raise ValueError(f'Invalid opcode: {opcode}')
    return error_num, error_msg[:-1].decode()
#:

def unpack_opcode(packet: bytes) -> int:
    opcode = struct.unpack('!H', packet[:2])[0]
    if opcode not in (RRQ, WRQ, DAT, ACK, ERR):
        raise ValueError(f"Invalid opcode {opcode}")
    return opcode
#:

###############################################################
##
##      ERRORS AND EXCEPTIONS
##
###############################################################

class NetworkError(Exception):
    """
    Any network error, like "host not found", timeouts, etc.
    """
#:

class ProtocolError(NetworkError):
    """
    A protocol error like unexpected or invalid opcode, wrong block 
    number, or any other invalid protocol parameter.
    """
#:

class Err(Exception):
    """
    An error sent by the server. It may be caused because a read/write 
    can't be processed. Read and write errors during file transmission 
    also cause this message to be sent, and transmission is then 
    terminated. The error number gives a numeric error code, followed 
    by an ASCII error message that might contain additional, operating 
    system specific information.
    """
    def __init__(self, error_code: int, error_msg: str):
        super().__init__(f'TFTP Error {error_code}')
        self.error_code = error_code
        self.error_msg = error_msg
    #:
#:

################################################################################
##
##      COMMON UTILITIES
##      Mostly related to network tasks
##
################################################################################

def _make_is_valid_hostname():
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    def _is_valid_hostname(hostname):
        """
        From: http://stackoverflow.com/questions/2532053/validate-a-hostname-string
        See also: https://en.wikipedia.org/wiki/Hostname (and the RFC 
        referenced there)
        """
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            # strip exactly one dot from the right, if present
            hostname = hostname[:-1]
        return all(allowed.match(x) for x in hostname.split("."))
    return _is_valid_hostname
#:
is_valid_hostname = _make_is_valid_hostname()


def get_host_info(server_addr: str) -> tuple[str, str]:
    """
    Returns the server ip and hostname for server_addr. This param may
    either be an IP address, in which case this function tries to query
    its hostname, or vice-versa.
    This functions raises a ValueError exception if the host name in
    server_addr is ill-formed, and raises NetworkError if we can't get
    an IP address for that host name.
    TODO: refactor code...
    """
    try:
        ipaddress.ip_address(server_addr)
    except ValueError:
        # server_addr not a valid ip address, then it might be a 
        # valid hostname
        # pylint: disable=raise-missing-from
        if not is_valid_hostname(server_addr):
            raise ValueError(f"Invalid hostname: {server_addr}.")
        server_name = server_addr
        try:
            # gethostbyname_ex returns the following tuple: 
            # (hostname, aliaslist, ipaddrlist)
            server_ip = gethostbyname_ex(server_name)[2][0]
        except gaierror:
            raise NetworkError(f"Unknown server: {server_name}.")
    else:  
        # server_addr is a valid ip address, get the hostname
        # if possible
        server_ip = server_addr
        try:
            # returns a tuple like gethostbyname_ex
            server_name = gethostbyaddr(server_ip)[0]
        except herror:
            server_name = ''
    return server_ip, server_name
#:

def is_ascii_printable(txt: str) -> bool:
    return set(txt).issubset(string.printable)
    # ALTERNATIVA: return not set(txt) - set(string.printable)
#:
