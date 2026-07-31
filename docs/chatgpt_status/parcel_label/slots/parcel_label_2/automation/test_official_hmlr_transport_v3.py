from __future__ import annotations

import importlib.util
import socket
import ssl
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transport_v3", HERE / "official_hmlr_transport_v3.py")
assert spec and spec.loader
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class FakeSocket:
    def __init__(self) -> None:
        self.options = []
        self.closed = False

    def setsockopt(self, *args) -> None:
        self.options.append(args)

    def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self) -> None:
        self.calls = []

    def wrap_socket(self, sock, *, server_hostname):
        self.calls.append((sock, server_hostname))
        return ("tls", sock, server_hostname)


class PublicDNSTests(unittest.TestCase):
    def test_accept_public_ipv4(self):
        self.assertEqual(transport.validate_public_addresses(["8.8.8.8"]), ["8.8.8.8"])

    def test_accept_public_ipv6(self):
        self.assertEqual(transport.validate_public_addresses(["2606:4700:4700::1111"]), ["2606:4700:4700::1111"])

    def test_deduplicate_canonical_addresses(self):
        value = transport.validate_public_addresses(["8.8.8.8", "8.8.8.8", "2606:4700:4700:0:0:0:0:1111"])
        self.assertEqual(value, ["8.8.8.8", "2606:4700:4700::1111"])

    def test_reject_mixed_public_private(self):
        with self.assertRaisesRegex(RuntimeError, "NON_PUBLIC"):
            transport.validate_public_addresses(["8.8.8.8", "10.0.0.1"])

    def test_reject_empty_result(self):
        with self.assertRaisesRegex(RuntimeError, "NO_PUBLIC"):
            transport.validate_public_addresses([])

    def test_reject_invalid_address(self):
        with self.assertRaisesRegex(RuntimeError, "ADDRESS_INVALID"):
            transport.validate_public_addresses(["not-an-ip"])

    def test_reject_empty_address(self):
        with self.assertRaisesRegex(RuntimeError, "NON_PUBLIC"):
            transport.validate_public_addresses([""])

    def test_reject_non_global_address_classes(self):
        rejected = [
            "0.0.0.0", "10.0.0.1", "100.64.0.1", "127.0.0.1", "169.254.1.1",
            "172.16.0.1", "192.168.1.1", "192.0.2.1", "224.0.0.1", "240.0.0.1",
            "::", "::1", "fc00::1", "fe80::1", "ff02::1", "2001:db8::1",
        ]
        for address in rejected:
            with self.subTest(address=address), self.assertRaisesRegex(RuntimeError, "NON_PUBLIC"):
                transport.validate_public_addresses([address])

    def test_resolver_filters_and_deduplicates(self):
        records = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 443)),
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("2606:4700:4700::1111", 443, 0, 0)),
        ]
        with mock.patch.object(socket, "getaddrinfo", return_value=records) as resolver:
            result = transport.resolve_public_addresses("example.test", 443)
        self.assertEqual(result, ["8.8.8.8", "2606:4700:4700::1111"])
        resolver.assert_called_once_with("example.test", 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

    def test_resolver_wraps_gaierror(self):
        with mock.patch.object(socket, "getaddrinfo", side_effect=socket.gaierror(-3, "temporary")):
            with self.assertRaisesRegex(RuntimeError, "DNS_RESOLUTION_FAILED"):
                transport.resolve_public_addresses("example.test", 443)

    def test_connection_pins_ip_and_preserves_sni(self):
        fake_socket = FakeSocket()
        fake_context = FakeContext()
        resolver = mock.Mock(return_value=["8.8.8.8"])
        connection = transport.PublicDNSHTTPSConnection("official.example", context=fake_context, resolver=resolver, timeout=4)
        with mock.patch.object(socket, "create_connection", return_value=fake_socket) as creator:
            connection.connect()
        resolver.assert_called_once_with("official.example", 443)
        creator.assert_called_once_with(("8.8.8.8", 443), 4, None)
        self.assertEqual(connection.sock, ("tls", fake_socket, "official.example"))
        self.assertEqual(fake_context.calls[0][1], "official.example")

    def test_connection_rejects_proxy_tunnel(self):
        connection = transport.PublicDNSHTTPSConnection("official.example", context=FakeContext(), resolver=lambda *_: ["8.8.8.8"])
        connection._tunnel_host = "proxy.example"
        with self.assertRaisesRegex(RuntimeError, "PROXY_TUNNEL_FORBIDDEN"):
            connection.connect()

    def test_connection_tries_next_public_address(self):
        fake_socket = FakeSocket()
        connection = transport.PublicDNSHTTPSConnection("official.example", context=FakeContext(), resolver=lambda *_: ["8.8.8.8", "1.1.1.1"])
        with mock.patch.object(socket, "create_connection", side_effect=[OSError("first"), fake_socket]) as creator:
            connection.connect()
        self.assertEqual(creator.call_count, 2)
        self.assertEqual(connection.sock[2], "official.example")

    def test_connection_reports_all_failures(self):
        connection = transport.PublicDNSHTTPSConnection("official.example", context=FakeContext(), resolver=lambda *_: ["8.8.8.8", "1.1.1.1"])
        with mock.patch.object(socket, "create_connection", side_effect=[OSError("first"), OSError("second")]):
            with self.assertRaisesRegex(OSError, "PUBLIC_ADDRESS_CONNECT_FAILED"):
                connection.connect()

    def test_https_handler_uses_public_connection(self):
        handler = transport.PublicDNSHTTPSHandler(resolver=lambda *_: ["8.8.8.8"], context=ssl.create_default_context())
        request = types.SimpleNamespace()
        with mock.patch.object(handler, "do_open", return_value="ok") as do_open:
            self.assertEqual(handler.https_open(request), "ok")
        self.assertIs(do_open.call_args.args[0].func, transport.PublicDNSHTTPSConnection)

    def test_opener_disables_environment_proxy(self):
        import urllib.request
        opener, _, proxy, https = transport.build_public_dns_opener(urllib.request.HTTPRedirectHandler(), resolver=lambda *_: ["8.8.8.8"])
        self.assertEqual(proxy.proxies, {})
        self.assertFalse(any(isinstance(handler, urllib.request.ProxyHandler) for handler in opener.handlers))
        self.assertIn(https, opener.handlers)

    def test_opener_preserves_supplied_cookie_jar(self):
        import http.cookiejar
        import urllib.request
        jar = http.cookiejar.CookieJar()
        opener, returned, _, _ = transport.build_public_dns_opener(urllib.request.HTTPRedirectHandler(), cookie_jar=jar, resolver=lambda *_: ["8.8.8.8"])
        self.assertIs(returned, jar)
        processors = [handler for handler in opener.handlers if isinstance(handler, urllib.request.HTTPCookieProcessor)]
        self.assertEqual(len(processors), 1)
        self.assertIs(processors[0].cookiejar, jar)


if __name__ == "__main__":
    unittest.main(verbosity=2)
