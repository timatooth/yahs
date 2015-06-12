#!/usr/bin/env python

"""Yet another HTTP Server (YaHS)

Provides simple decorator API to quickly create and test RESTful APIs
"""
__author__ = 'Tim Sullivan'

import sys
import os
import signal
import socket
import threading
import urlparse
import ssl
import logging
import re
import collections
import inspect


class Request:
    """Structure of an incoming HTTP request.

    Requests are created by the running HttpWorker threads and have
    a uri. 'handlers' register for request url patterns they're interested in.
    """
    def __init__(self, method, uri, headers, get_query, address="127.0.0.1"):
        self.method = method  # e.g GET, PUT, HEAD
        self.uri = uri  # e.g /index.html
        self.headers = headers
        self.get_query = get_query  # eg /couches/?orderby=lowestprice should be: {'orderby': 'lowestprice'}
        self.body = None  # if a PUT/POST request this will contain the raw data
        self.remote_address = address

    def __str__(self):
        """
        String representation of a Request
        """
        return "Request: {} {}\nHeaders:\n{}\nQuerystring:\n{}\n".format(
            self.method,
            self.uri,
            self.headers,
            self.get_query)


class Response:
    """Structure of a HTTP Response destined for the client.

    Handlers are responsible for returning a Request to the HttpWorker
    which gets sent to the client.
    """

    def __init__(self):
        self.status_code = 200
        self.status_message = "OK"
        self.headers = {
            'Server': 'YaHS (Yet another HTTP Server) v1.0',
            'Content-Type': "text/html",
        }
        self.body = ""

    def send(self, client_socket):
        """Send the Response to the client socket provided.

        This method is called *Internally* and should not be used directly.
        """
        client_socket.send("HTTP/1.1 {0} {1}\r\n".format(self.status_code, self.status_message))
        self.headers['Content-Length'] = str(len(self.body))
        for header in self.headers:
            client_socket.send(header + ": " + self.headers[header] + "\r\n")
        client_socket.send("\r\n")
        client_socket.send(self.body)


class HttpWorker(threading.Thread):
    """Process all the HTTP protocol work here in a Thread.
    :param: args expects (client_socket, client_address) from socket.accept() call
    """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        # call 'super' constructor to init thread
        super(HttpWorker, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)

        # management fields
        self.keep_running = True
        self.client_socket = args[0]
        self.client_address = args[1]

    def run(self):
        """Process each client connection.

        Parses the request to create a Request object,
        gets a Response by finding a request handler that matches a regex.
        The response is then sent and the connection closed.
        This is run in a new thread for each request
        """
        # parse http. Result is a new Request object
        request = self.parse_request()
        # generate a response by calling the handler which does the magic
        response = self.handle_request(request)
        # log the request and the response status to console
        self.audit_log(request, response)
        # send the response back to the client
        response.send(self.client_socket)

        # we're done...
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()

    def parse_request(self):
        """Reads the tcp client socket to make a Request.

        :return: a Request object
        """
        request = ""
        data = ""  # if we had PUT or POST data build it here
        post_flag = False
        http_request = None

        while True:
            got_bytes = 0
            new_data = self.client_socket.recv(8192)
            if len(new_data) == 0:
                break  # got EOF meh

            # if the request has just started
            if not post_flag:
                for line in new_data.split("\n"):
                    request += line + "\n"  # add linebreak back helps
                    got_bytes += len(line) + 1

                    if len(line) <= 1:  # assumed to reach /r/n/r/n
                        request_lines = request.split('\r\n')
                        request_speci = request_lines[0].split()  # eg ['GET', '/', 'HTTP/1.1']

                        request_headers = {}
                        for header in request_lines[1:]:
                            try:
                                (var, val) = header.split(': ')  # split header key/value pairs into 2 components
                                request_headers[var] = val
                            except ValueError:
                                pass

                        # process querystring in request if any eg GET /?status=new&cake=lie
                        # resulting uri variable should then have the querystring chopped off.
                        # true keeps any blank values e.g /?egg
                        get_query = urlparse.parse_qs(request_speci[1].replace("/?", ''), True)
                        # chop off querystring, e.g: /?status=new&cake=lie becomes /
                        uri = request_speci[1].split("?")[0]

                        # create an instance of a Request object
                        http_request = Request(request_speci[0], uri, request_headers, get_query,
                                               address=self.client_address)

                        if request_speci[0] == 'POST' or request_speci[0] == 'PUT':
                            post_flag = True
                            data += new_data[got_bytes:]

                            if len(data) == int(http_request.headers['Content-Length']):
                                logging.debug("Finished reading POST request")
                                http_request.body = data
                                return http_request
                            else:
                                # exit for, post flag is set, will continue reading post later on
                                break

                        else:
                            return http_request
            else:
                # we have more POST/PUT data to process
                data += new_data
                if len(data) == int(http_request.headers['Content-Length']):
                    http_request.body = data
                    logging.debug("Finished reading large file")
                    break
                elif len(data) >= int(http_request.headers['Content-Length']):
                    logging.warning("Got more data from client than specified in Content-Length")
                    # should return a bad request

        return http_request

    def handle_request(self, request):
        """Search the list of registered Request handlers which match an expression.

        Calls handler if found otherwise should send 404
        request incoming Request object
        returns a Response destined for the client
        """
        if request is None:
            logging.warning("Tried to handle a None Request")
            response = Response()
            response.status_code = 400
            response.status_message = "Bad Request None Got It"
            return response

        logging.debug(request)

        # first check if we support that request method type i.e any registered handlers for it
        if request.method not in Server.handlers:
            response = Response()
            response.status_code = 400
            response.status_message = 'Bad Request'
            response.body = "<h1>400 Bad Request</h1><p>The server could support your request</p>"
            return response

        # spin over the registered get handlers and call a match. O(n) where n is number of registered method handlers
        for urlpattern in Server.handlers[request.method]:
            match = urlpattern.match(request.uri)
            if match is not None:
                # found matching urlpatten. Get named regex back-reference values as args
                args = match.groupdict()
                # call our registered handler for that url with unpacked args
                func = Server.handlers[request.method][urlpattern]  # awesomeness
                res = func(request, **args)
                if type(res) is str:
                    response = Response()
                    response.body = res
                    return response
                elif res is None:
                    response = Response()
                    response.status_code = 204
                    response.status_message = 'No Content'
                    logging.debug("Got a None response back from handler check return response exists?")
                    return response

                return res

        # If we reached here then it's time for a 404
        response = Response()
        response.status_code = 404
        response.status_message = 'Not Found'
        response.body = "<h1>404 Not Found</h1><p>The server could not find a resource matching your request :(</p>"
        return response

    @staticmethod
    def audit_log(request, response):
        """Logs request and Response http status code destined for the client
        request The original Request they made
        response The actual Response destined for the client
        """
        logging.info("{} {} Response: {}".format(request.method, request.uri, response.status_code))

class ListenerThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        """
        Create the server socket listener thread.
        args is required with (hostname, port, https_enabled)
        """
        # call 'super' constructor to init thread
        super(ListenerThread, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)

        self.hostname = args[0]
        self.port = args[1]
        self.secure = args[2]
        self.socket = None

        self.setup_listening()

    def setup_listening(self):
        logging.info("Starting ListenerThread on {0}:{1}".format(self.hostname, self.port))
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.hostname, self.port))
        server_socket.listen(5)
        self.socket = server_socket

        if self.secure:
            self.wrap_ssl()

    def run(self):
        logging.debug("Entering http server loop")
        while True:
            try:
                (client_socket, address) = self.socket.accept()
                logging.debug("Accepted connection from %s", address)
                # create a HttpWorker thread, passing in the client socket
                http_thread = HttpWorker(args=(client_socket, address))
                http_thread.start()
            except ssl.SSLEOFError:
                # find this happening when browser issues warning and ends tcp stream
                logging.debug("Reached EOF when SSL connection was being accepted")
                continue
            except ssl.SSLError, err:
                logging.warning("Got a {} error: {}".format(err['library'], err['reason']))
                continue

    def wrap_ssl(self):
        # Wrap socket in SSL. TODO look into using ssl.SSLContexts for better support of browsers
        try:
            logging.debug("Attempting to load private key at %s", self.key_file)
            logging.debug("Attempting to load certificates at %s", self.certificate_file)
            self.socket = ssl.wrap_socket(self.socket,
                                          server_side=True,
                                          certfile=self.certificate_file,
                                          keyfile=self.key_file)
            logging.debug("Certificates and server key loaded")
        except IOError as err:
            logging.warning("Could not find SSL certificate or private key file. Not starting ssl")
            logging.warning(err)
            self.socket.close()
            return

class Server:
    """Server listens for secure and non-secure sockets.

    Spawns HttpWorker threads to handle the HTTP/1.1 protocol.
    handlers Dictionary mapping url patten regular expressions to event handler functions
    """

    # Event Handling Structure for requests
    handlers = {}

    @staticmethod
    def handle(method, uri):
        """Decorator for registering Request handlers

        Takes a HTTP method as string such as 'GET'
        Takes a regex string to compile and register for events

        """
        def request_handler_decorator(func):
            # build regular expression
            uri_expression = re.compile(uri)

            # update global handler dict dynamically as http methods are registered
            if method not in Server.handlers:
                logging.debug("Creating new handler structure for %s method type.", method)
                Server.handlers[method] = collections.OrderedDict()  # order of regex key insertion matters

            Server.handlers[method][uri_expression] = func  # add new function mapped to url regex
            return func

        return request_handler_decorator

    def __init__(self, hostname='localhost', port=4321, secure=False):
        """Create a live running http server instance to go

        It will start listening on the specified port but won't run yet until start() is called.
        """
        self.base_port = port
        self.hostname = hostname
        self.secure = secure
        self.key_file = os.path.join(os.path.dirname(__file__), "server.key")
        self.certificate_file = os.path.join(os.path.dirname(__file__), "certificate-chain.crt")

        # Bind the signal handler: SIGINT is send to the process when CTRL-C is pressed
        signal.signal(signal.SIGINT, self.handle_shutdown)

        self.listener = ListenerThread(args=('localhost', self.base_port, False))
        self.listener.daemon = True

    def handle_shutdown(self, signal_unused, frame_unused):
        """If the server receives a signal (e.g. Ctrl-C/Ctrl-Break), terminate gracefully
        """
        logging.info("SIGINT Signal received; exiting gracefully...")
        sys.exit(0)

    def start(self):
        """Start the server mainloop.

        By now the server should have been inited and ready to enter the run loop.
        """

        self.listener.start()

        if self.secure:
            secure_listener = ListenerThread(args=('localhost', self.base_port, True))
            secure_listener.daemon = True
            secure_listener.start()

        return self

    def wait(self):
        """Helper to block main thread to keep process running.
        """
        logging.info('Waiting for connections...')
        while self.listener.is_alive:
            self.listener.join(1)

@Server.handle('GET', r'^/$')
@Server.handle('GET', r'^/yahs/api/?$')
def api_index(request):
    """Display the API index page for browsing loaded Request handlers.

    In conclusion, this is quite awesome.
    """
    response = Response()
    body = "<h1>Welcome to YaHS! API Index</h1>"

    for method in Server.handlers:
        body += "<h2 style='color: #555;'>{}</h2>".format(method)
        for regex in Server.handlers[method]:
            body += "<ul>"
            func = Server.handlers[method][regex]
            module = inspect.getmodule(func)
            var_names = func.func_code.co_varnames[:func.func_code.co_argcount]
            body += "<li><strong>{}</strong> <pre>{}: <span style='color: #00a;'>def</span> {}{}</pre><em>{}</em></li>".format(
                regex.pattern,
                module.__name__,
                func.__name__,
                var_names,
                func.__doc__)
            body += "</ul>"

    response.body = body
    return response


@Server.handle("GET", r'^/yahs/reload/?$')
def reload_server(request):
    """Re-Load the server event handling module
    """
    logging.warning("Reloading event handler modules")
    reloaded_modules = []
    for method in Server.handlers:
        for regex in Server.handlers[method]:
            func = Server.handlers[method][regex]
            module = inspect.getmodule(func)

            if module.__name__ != "yahs":
                if module not in reloaded_modules:
                    logging.info("Reloading {} module.".format(module.__name__))
                    reload(module)
                    reloaded_modules.append(module)

    res = Response()
    res.body = "Server reloaded"
    return res


@Server.handle('OPTIONS', '.')
def handle_cors(request):
    """Ruthlessly handle anything that looks like a Cross Origin request.

    Just repeats back what the browser requested granting all.
    """
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
    response.headers['Access-Control-Allow-Method'] = request.headers['Access-Control-Request-Method']
    response.headers['Access-Control-Allow-Headers'] = request.headers['Access-Control-Request-Headers']
    return response

# main :)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        tcp_port = int(sys.argv[1])
        server = Server(port=tcp_port)
    else:
        server = Server()  # defaults to http://localhost:4321, https://localhost:4322

    server.start().wait()
