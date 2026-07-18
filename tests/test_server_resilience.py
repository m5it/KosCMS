#!/usr/bin/env python3
"""
Server resilience test suite.

Sends a variety of malformed and malicious-looking requests to a running
WebCMS server and verifies that the server remains up and continues to
accept normal HTTP requests.

Run the server first, e.g.:

    python -m webcms

Then run this script:

    python tests/test_server_resilience.py

Expected behavior:
- TLS/binary garbage sent to the HTTP port should be silently ignored or
  result in a 400 response. The server must not crash.
- HTTP/2 PRI requests should receive 400 Bad Request.
- Oversized request lines should receive 400 Bad Request.
- Null bytes / control characters in the path should receive 400 Bad Request.
- After each malformed request, a normal GET / must still return 200 OK.
"""

import socket
import sys
import time


HOST = "127.0.0.1"
PORT = 8000
TIMEOUT = 5


def send_raw(data: bytes) -> bytes:
    """Open a TCP connection, send raw bytes, and return whatever is read."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(TIMEOUT)
        sock.connect((HOST, PORT))
        sock.sendall(data)
        try:
            return sock.recv(4096)
        except socket.timeout:
            return b""


def send_then_reset(data: bytes) -> None:
    """Send raw bytes and immediately RST the connection."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.connect((HOST, PORT))
        sock.sendall(data)
        # Set SO_LINGER to 0 so close() sends a RST.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x00\x00\x00\x00")
    finally:
        sock.close()


def normal_get() -> bool:
    """Verify the server still serves a normal GET / request."""
    response = send_raw(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
    return response.startswith(b"HTTP/1.1 200") or response.startswith(b"HTTP/1.0 200")


def test_tls_garbage():
    """TLS ClientHello sent to plain HTTP port."""
    tls_hello = bytes([
        0x16, 0x03, 0x01, 0x00, 0x8c, 0x01, 0x00, 0x00,
        0x88, 0x03, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x2f, 0xc0,
        0x2b, 0xc0, 0x11, 0xc0, 0x07, 0xc0, 0x13, 0xc0,
        0x09, 0xc0, 0x14, 0xc0,
    ])
    response = send_raw(tls_hello)
    print(f"TLS garbage: {response[:60]!r}")
    assert normal_get(), "Server did not recover after TLS garbage"
    print("  -> server recovered")


def test_connection_reset():
    """Connection reset immediately after sending some bytes."""
    send_then_reset(b"GET / HTTP/1.1\r\nHost: localhost\r\n")
    time.sleep(0.1)
    assert normal_get(), "Server did not recover after connection reset"
    print("  -> server recovered")


def test_oversized_request_line():
    """Request line longer than the server should accept."""
    path = "/" + "A" * 9000
    response = send_raw(f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
    print(f"Oversized request line: {response[:60]!r}")
    assert b"400" in response or response == b"", "Expected 400 or closed connection"
    assert normal_get(), "Server did not recover after oversized request line"
    print("  -> server recovered")


def test_http2_pri():
    """HTTP/2 PRI request."""
    response = send_raw(b"PRI * HTTP/2.0\r\n\r\n")
    print(f"HTTP/2 PRI: {response[:60]!r}")
    assert b"400" in response or response == b"", "Expected 400 or closed connection"
    assert normal_get(), "Server did not recover after HTTP/2 PRI"
    print("  -> server recovered")


def test_null_bytes_in_path():
    """Null byte in request path."""
    response = send_raw(b"GET /foo\x00bar HTTP/1.1\r\nHost: localhost\r\n\r\n")
    print(f"Null byte path: {response[:60]!r}")
    assert b"400" in response or response == b"", "Expected 400 or closed connection"
    assert normal_get(), "Server did not recover after null byte path"
    print("  -> server recovered")


def test_invalid_http_version():
    """Invalid SERVER_PROTOCOL string."""
    response = send_raw(b"GET / HTTP/3.0\r\nHost: localhost\r\n\r\n")
    print(f"Invalid HTTP version: {response[:60]!r}")
    assert b"400" in response or response == b"", "Expected 400 or closed connection"
    assert normal_get(), "Server did not recover after invalid HTTP version"
    print("  -> server recovered")


def main():
    print(f"Testing server resilience at {HOST}:{PORT}")
    print("Ensure the WebCMS server is running before continuing.")
    time.sleep(1)

    tests = [
        test_tls_garbage,
        test_connection_reset,
        test_oversized_request_line,
        test_http2_pri,
        test_null_bytes_in_path,
        test_invalid_http_version,
    ]

    for test in tests:
        print(f"\nRunning {test.__name__}...")
        try:
            test()
            print(f"  PASSED")
        except AssertionError as exc:
            print(f"  FAILED: {exc}")
            return 1
        except Exception as exc:
            print(f"  ERROR: {exc}")
            return 1

    print("\nAll resilience tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
