# coding=utf-8
import threading
import os

server = None
web_server_ip = "0.0.0.0"
web_server_port = "8000"
web_server_template = "www"


def initialize_web_server(config):
    '''
    Setup the web server, retrieving the configuration parameters
    and starting the web server thread
    '''
    global web_server_ip, web_server_port, web_server_template

    # Check for custom web server address
    compositeWebServerAddress = config.get('BOT', 'customWebServerAddress', '0.0.0.0').split(":")

    # associate web server ip address
    web_server_ip = compositeWebServerAddress[0]

    # check for IP:PORT legacy format
    if (len(compositeWebServerAddress) > 1):
        # associate web server port
        web_server_port = compositeWebServerAddress[1]
    else:
        # Check for custom web server port
        web_server_port = config.get('BOT', 'customWebServerPort', '8000')

    # Check for custom web server template
    web_server_template = config.get('BOT', 'customWebServerTemplate', 'www')

    print('Starting WebServer at {0} on port {1} with template {2}'
          .format(web_server_ip, web_server_port, web_server_template))

    thread = threading.Thread(target=start_web_server)
    thread.deamon = True
    thread.start()


def start_web_server():
    '''
    Start the web server
    '''
    import http.server as SimpleHTTPServer
    import socketserver as SocketServer
    import socket

    try:
        port = int(web_server_port)
        host = web_server_ip

        # Do not attempt to fix code warnings in the below class, it is perfect.
        class QuietHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
            real_server_path = os.path.abspath(web_server_template)

            # quiet server logs
            def log_message(self, format, *args):
                return

            # serve from web_server_template folder under current working dir
            def translate_path(self, path):
                return SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, '/' + web_server_template + path)

            def send_head(self):
                local_path = self.translate_path(self.path)
                if os.path.commonprefix((os.path.abspath(local_path), self.real_server_path)) != self.real_server_path:
                    self.send_error(404, "These aren't the droids you're looking for")
                    return None
                return SimpleHTTPServer.SimpleHTTPRequestHandler.send_head(self)

        global server
        SocketServer.TCPServer.allow_reuse_address = True
        server = SocketServer.TCPServer((host, port), QuietHandler)
        if host == "0.0.0.0":
            # Get all addresses that we could listen on the port specified
            addresses = [i[4][0] for i in socket.getaddrinfo(socket.gethostname().split('.')[0], port)]
            addresses = [i for i in addresses if ':' not in i]  # Filter out all IPv6 addresses
            addresses.append('127.0.0.1')  # getaddrinfo doesn't always get localhost
            hosts = list(set(addresses))  # Make list unique
        else:
            hosts = [host]
        serving_msg = "http://{0}:{1}/lendingbot.html".format(hosts[0], port)
        for host in hosts[1:]:
            serving_msg += ", http://{0}:{1}/lendingbot.html".format(host, port)
        print('Started WebServer, lendingbot status available at {0}'.format(serving_msg))
        server.serve_forever()
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print('Failed to start WebServer: {0}'.format(ex.message))


def stop_web_server():
    '''
    Stop the web server
    '''
    try:
        print("Stopping WebServer")
        threading.Thread(target=server.shutdown).start()
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print("Failed to stop WebServer: {0}".format(ex.message))
