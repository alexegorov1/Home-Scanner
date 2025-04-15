import socket

def sweep_host_ports(ip, ports):
    open_ports = []
    for port in ports:
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((ip, port))
            open_ports.append(port)
            s.close()
        except:
            continue
    return open_ports
