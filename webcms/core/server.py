"""
Hardened WSGI server components.

Provides request handler and server classes that gracefully handle
malformed requests, TLS garbage sent to HTTP ports, connection resets,
and other low-level socket errors without crashing the server.
"""

import logging
import sys
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer


logger = logging.getLogger("webcms.server")


class HardenedWSGIRequestHandler(WSGIRequestHandler):
    """
    WSGI request handler that silently survives malformed requests and
    connection resets instead of printing full tracebacks to stderr.
    """

    # Do not emit default GET /path log lines for every request.
    # Security-relevant events are logged explicitly below.
    def log_message(self, format, *args):
        logger.debug("%s - %s", self.address_string(), format % args)

    def log_error(self, format, *args):
        logger.debug("Request error from %s: %s", self.address_string(), format % args)

    def handle(self):
        """Handle a single connection, swallowing expected socket errors."""
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as exc:
            logger.debug("Connection reset/closed by %s: %s", self.address_string(), exc)
        except OSError as exc:
            logger.debug("OS error handling request from %s: %s", self.address_string(), exc)
        except Exception as exc:
            logger.warning("Unexpected error handling request from %s: %s", self.address_string(), exc)

    def handle_one_request(self):
        """Process one HTTP request, returning 400 for malformed input."""
        try:
            return super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return False
        except OSError:
            return False
        except ValueError as exc:
            # wsgiref raises ValueError for malformed request lines/versions.
            logger.debug("Malformed request from %s: %s", self.address_string(), exc)
            self.send_error(400, "Bad Request")
            self.close_connection = True
            return False
        except Exception as exc:
            logger.warning("Error processing request from %s: %s", self.address_string(), exc)
            self.send_error(400, "Bad Request")
            self.close_connection = True
            return False

    def parse_request(self):
        """Parse request line, returning False on malformed input."""
        try:
            return super().parse_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return False
        except OSError:
            return False
        except ValueError as exc:
            logger.debug("Bad request syntax from %s: %s", self.address_string(), exc)
            self.send_error(400, "Bad Request")
            self.close_connection = True
            return False
        except Exception as exc:
            logger.debug("Could not parse request from %s: %s", self.address_string(), exc)
            self.send_error(400, "Bad Request")
            self.close_connection = True
            return False

    def _read_request_line(self):
        """Read the request line, tolerating short/closed connections."""
        try:
            return self.rfile.readline(65537)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return b""
        except OSError:
            return b""


class HardenedWSGIServer(WSGIServer):
    """
    WSGI server that uses HardenedWSGIRequestHandler by default and
    handles connection-level errors gracefully.
    """

    request_timeout = 30
    allow_reuse_address = True

    def __init__(self, server_address, app, handler_class=None):
        # Default to hardened handler if not provided.
        if handler_class is None:
            handler_class = HardenedWSGIRequestHandler
        super().__init__(server_address, app, handler_class)

    def handle_error(self, request, client_address):
        """
        Override BaseServer.handle_error to suppress noisy tracebacks for
        routine socket errors.
        """
        exc_type, exc_value = sys.exc_info()[:2]
        if exc_type and issubclass(
            exc_type,
            (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError, TimeoutError),
        ):
            logger.debug("Suppressed socket error from %s: %s", client_address, exc_value)
            return
        logger.warning("Server error processing request from %s", client_address, exc_info=True)

    def get_request(self):
        """Accept a connection with a socket timeout to defend slowloris."""
        conn, client_address = super().get_request()
        try:
            conn.settimeout(self.request_timeout)
        except OSError:
            pass
        return conn, client_address


def make_hardened_server(host, port, app, handler_class=None, timeout=30):
    """
    Factory for a hardened WSGI development server.

    Args:
        host: Interface to bind to.
        port: Port to listen on.
        app: WSGI application callable.
        handler_class: Optional custom request handler class.
        timeout: Socket timeout in seconds.

    Returns:
        HardenedWSGIServer instance.
    """
    handler_class = handler_class or HardenedWSGIRequestHandler
    server = HardenedWSGIServer((host, port), app, handler_class)
    server.request_timeout = timeout
    return server
