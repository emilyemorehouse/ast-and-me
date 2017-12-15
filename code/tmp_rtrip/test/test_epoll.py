"""
Tests for epoll wrapper.
"""
import errno
import os
import select
import socket
import time
import unittest
if not hasattr(select, 'epoll'):
    raise unittest.SkipTest('test works only on Linux 2.6')
try:
    select.epoll()
except OSError as e:
    if e.errno == errno.ENOSYS:
        raise unittest.SkipTest("kernel doesn't support epoll()")
    raise


class TestEPoll(unittest.TestCase):

    def setUp(self):
        self.serverSocket = socket.socket()
        self.serverSocket.bind(('127.0.0.1', 0))
        self.serverSocket.listen()
        self.connections = [self.serverSocket]

    def tearDown(self):
        for skt in self.connections:
            skt.close()

    def _connected_pair(self):
        client = socket.socket()
        client.setblocking(False)
        try:
            client.connect(('127.0.0.1', self.serverSocket.getsockname()[1]))
        except OSError as e:
            self.assertEqual(e.args[0], errno.EINPROGRESS)
        else:
            raise AssertionError('Connect should have raised EINPROGRESS')
        server, addr = self.serverSocket.accept()
        self.connections.extend((client, server))
        return client, server

    def test_create(self):
        try:
            ep = select.epoll(16)
        except OSError as e:
            raise AssertionError(str(e))
        self.assertTrue(ep.fileno() > 0, ep.fileno())
        self.assertTrue(not ep.closed)
        ep.close()
        self.assertTrue(ep.closed)
        self.assertRaises(ValueError, ep.fileno)
        if hasattr(select, 'EPOLL_CLOEXEC'):
            select.epoll(select.EPOLL_CLOEXEC).close()
            self.assertRaises(OSError, select.epoll, flags=12356)

    def test_badcreate(self):
        self.assertRaises(TypeError, select.epoll, 1, 2, 3)
        self.assertRaises(TypeError, select.epoll, 'foo')
        self.assertRaises(TypeError, select.epoll, None)
        self.assertRaises(TypeError, select.epoll, ())
        self.assertRaises(TypeError, select.epoll, ['foo'])
        self.assertRaises(TypeError, select.epoll, {})

    def test_context_manager(self):
        with select.epoll(16) as ep:
            self.assertGreater(ep.fileno(), 0)
            self.assertFalse(ep.closed)
        self.assertTrue(ep.closed)
        self.assertRaises(ValueError, ep.fileno)

    def test_add(self):
        server, client = self._connected_pair()
        ep = select.epoll(2)
        try:
            ep.register(server.fileno(), select.EPOLLIN | select.EPOLLOUT)
            ep.register(client.fileno(), select.EPOLLIN | select.EPOLLOUT)
        finally:
            ep.close()
        ep = select.epoll(2)
        try:
            ep.register(server, select.EPOLLIN | select.EPOLLOUT)
            ep.register(client, select.EPOLLIN | select.EPOLLOUT)
        finally:
            ep.close()
        ep = select.epoll(2)
        try:
            self.assertRaises(TypeError, ep.register, object(), select.
                EPOLLIN | select.EPOLLOUT)
            self.assertRaises(TypeError, ep.register, None, select.EPOLLIN |
                select.EPOLLOUT)
            self.assertRaises(ValueError, ep.register, -1, select.EPOLLIN |
                select.EPOLLOUT)
            self.assertRaises(OSError, ep.register, 10000, select.EPOLLIN |
                select.EPOLLOUT)
            ep.register(server, select.EPOLLIN | select.EPOLLOUT)
            self.assertRaises(OSError, ep.register, server, select.EPOLLIN |
                select.EPOLLOUT)
        finally:
            ep.close()

    def test_fromfd(self):
        server, client = self._connected_pair()
        ep = select.epoll(2)
        ep2 = select.epoll.fromfd(ep.fileno())
        ep2.register(server.fileno(), select.EPOLLIN | select.EPOLLOUT)
        ep2.register(client.fileno(), select.EPOLLIN | select.EPOLLOUT)
        events = ep.poll(1, 4)
        events2 = ep2.poll(0.9, 4)
        self.assertEqual(len(events), 2)
        self.assertEqual(len(events2), 2)
        ep.close()
        try:
            ep2.poll(1, 4)
        except OSError as e:
            self.assertEqual(e.args[0], errno.EBADF, e)
        else:
            self.fail("epoll on closed fd didn't raise EBADF")

    def test_control_and_wait(self):
        client, server = self._connected_pair()
        ep = select.epoll(16)
        ep.register(server.fileno(), select.EPOLLIN | select.EPOLLOUT |
            select.EPOLLET)
        ep.register(client.fileno(), select.EPOLLIN | select.EPOLLOUT |
            select.EPOLLET)
        now = time.monotonic()
        events = ep.poll(1, 4)
        then = time.monotonic()
        self.assertFalse(then - now > 0.1, then - now)
        events.sort()
        expected = [(client.fileno(), select.EPOLLOUT), (server.fileno(),
            select.EPOLLOUT)]
        expected.sort()
        self.assertEqual(events, expected)
        events = ep.poll(timeout=2.1, maxevents=4)
        self.assertFalse(events)
        client.send(b'Hello!')
        server.send(b'world!!!')
        now = time.monotonic()
        events = ep.poll(1, 4)
        then = time.monotonic()
        self.assertFalse(then - now > 0.01)
        events.sort()
        expected = [(client.fileno(), select.EPOLLIN | select.EPOLLOUT), (
            server.fileno(), select.EPOLLIN | select.EPOLLOUT)]
        expected.sort()
        self.assertEqual(events, expected)
        ep.unregister(client.fileno())
        ep.modify(server.fileno(), select.EPOLLOUT)
        now = time.monotonic()
        events = ep.poll(1, 4)
        then = time.monotonic()
        self.assertFalse(then - now > 0.01)
        expected = [(server.fileno(), select.EPOLLOUT)]
        self.assertEqual(events, expected)

    def test_errors(self):
        self.assertRaises(ValueError, select.epoll, -2)
        self.assertRaises(ValueError, select.epoll().register, -1, select.
            EPOLLIN)

    def test_unregister_closed(self):
        server, client = self._connected_pair()
        fd = server.fileno()
        ep = select.epoll(16)
        ep.register(server)
        now = time.monotonic()
        events = ep.poll(1, 4)
        then = time.monotonic()
        self.assertFalse(then - now > 0.01)
        server.close()
        ep.unregister(fd)

    def test_close(self):
        open_file = open(__file__, 'rb')
        self.addCleanup(open_file.close)
        fd = open_file.fileno()
        epoll = select.epoll()
        self.assertIsInstance(epoll.fileno(), int)
        self.assertFalse(epoll.closed)
        epoll.close()
        self.assertTrue(epoll.closed)
        self.assertRaises(ValueError, epoll.fileno)
        epoll.close()
        self.assertRaises(ValueError, epoll.modify, fd, select.EPOLLIN)
        self.assertRaises(ValueError, epoll.poll, 1.0)
        self.assertRaises(ValueError, epoll.register, fd, select.EPOLLIN)
        self.assertRaises(ValueError, epoll.unregister, fd)

    def test_fd_non_inheritable(self):
        epoll = select.epoll()
        self.addCleanup(epoll.close)
        self.assertEqual(os.get_inheritable(epoll.fileno()), False)


if __name__ == '__main__':
    unittest.main()
