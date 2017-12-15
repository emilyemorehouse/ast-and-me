"""HTTP/1.1 client library

<intro stuff goes here>
<other stuff, too>

HTTPConnection goes through a number of "states", which define when a client
may legally make another request or fetch the response for a particular
request. This diagram details these state transitions:

    (null)
      |
      | HTTPConnection()
      v
    Idle
      |
      | putrequest()
      v
    Request-started
      |
      | ( putheader() )*  endheaders()
      v
    Request-sent
      |\\_____________________________
      |                              | getresponse() raises
      | response = getresponse()     | ConnectionError
      v                              v
    Unread-response                Idle
    [Response-headers-read]
      |\\____________________
      |                     |
      | response.read()     | putrequest()
      v                     v
    Idle                  Req-started-unread-response
                     ______/|
                   /        |
   response.read() |        | ( putheader() )*  endheaders()
                   v        v
       Request-started    Req-sent-unread-response
                            |
                            | response.read()
                            v
                          Request-sent

This diagram presents the following rules:
  -- a second request may not be started until {response-headers-read}
  -- a response [object] cannot be retrieved until {request-sent}
  -- there is no differentiation between an unread response body and a
     partially read response body

Note: this enforcement is applied by the HTTPConnection class. The
      HTTPResponse class does not enforce this state machine, which
      implies sophisticated clients may accelerate the request/response
      pipeline. Caution should be taken, though: accelerating the states
      beyond the above pattern may imply knowledge of the server's
      connection-close behavior for certain requests. For example, it
      is impossible to tell whether the server will close the connection
      UNTIL the response headers have been read; this means that further
      requests cannot be placed into the pipeline until it is known that
      the server will NOT be closing the connection.

Logical State                  __state            __response
-------------                  -------            ----------
Idle                           _CS_IDLE           None
Request-started                _CS_REQ_STARTED    None
Request-sent                   _CS_REQ_SENT       None
Unread-response                _CS_IDLE           <response_class>
Req-started-unread-response    _CS_REQ_STARTED    <response_class>
Req-sent-unread-response       _CS_REQ_SENT       <response_class>
"""
import email.parser
import email.message
import http
import io
import os
import re
import socket
import collections
from urllib.parse import urlsplit
__all__ = ['HTTPResponse', 'HTTPConnection', 'HTTPException',
    'NotConnected', 'UnknownProtocol', 'UnknownTransferEncoding',
    'UnimplementedFileMode', 'IncompleteRead', 'InvalidURL',
    'ImproperConnectionState', 'CannotSendRequest', 'CannotSendHeader',
    'ResponseNotReady', 'BadStatusLine', 'LineTooLong',
    'RemoteDisconnected', 'error', 'responses']
HTTP_PORT = 80
HTTPS_PORT = 443
_UNKNOWN = 'UNKNOWN'
_CS_IDLE = 'Idle'
_CS_REQ_STARTED = 'Request-started'
_CS_REQ_SENT = 'Request-sent'
globals().update(http.HTTPStatus.__members__)
responses = {v: v.phrase for v in http.HTTPStatus.__members__.values()}
MAXAMOUNT = 1048576
_MAXLINE = 65536
_MAXHEADERS = 100
_is_legal_header_name = re.compile(b'[^:\\s][^:\\r\\n]*').fullmatch
_is_illegal_header_value = re.compile(b'\\n(?![ \\t])|\\r(?![ \\t\\n])').search
_METHODS_EXPECTING_BODY = {'PATCH', 'POST', 'PUT'}


def _encode(data, name='data'):
    """Call data.encode("latin-1") but show a better error message."""
    try:
        return data.encode('latin-1')
    except UnicodeEncodeError as err:
        raise UnicodeEncodeError(err.encoding, err.object, err.start, err.
            end, 
            "%s (%.20r) is not valid Latin-1. Use %s.encode('utf-8') if you want to send it encoded in UTF-8."
             % (name.title(), data[err.start:err.end], name)) from None


class HTTPMessage(email.message.Message):

    def getallmatchingheaders(self, name):
        """Find all header lines matching a given header name.

        Look through the list of headers and find all lines matching a given
        header name (and their continuation lines).  A list of the lines is
        returned, without interpretation.  If the header does not occur, an
        empty list is returned.  If the header occurs multiple times, all
        occurrences are returned.  Case is not important in the header name.

        """
        name = name.lower() + ':'
        n = len(name)
        lst = []
        hit = 0
        for line in self.keys():
            if line[:n].lower() == name:
                hit = 1
            elif not line[:1].isspace():
                hit = 0
            if hit:
                lst.append(line)
        return lst


def parse_headers(fp, _class=HTTPMessage):
    """Parses only RFC2822 headers from a file pointer.

    email Parser wants to see strings rather than bytes.
    But a TextIOWrapper around self.rfile would buffer too many bytes
    from the stream, bytes which we later need to read as bytes.
    So we read the correct bytes here, as bytes, for email Parser
    to parse.

    """
    headers = []
    while True:
        line = fp.readline(_MAXLINE + 1)
        if len(line) > _MAXLINE:
            raise LineTooLong('header line')
        headers.append(line)
        if len(headers) > _MAXHEADERS:
            raise HTTPException('got more than %d headers' % _MAXHEADERS)
        if line in (b'\r\n', b'\n', b''):
            break
    hstring = b''.join(headers).decode('iso-8859-1')
    return email.parser.Parser(_class=_class).parsestr(hstring)


class HTTPResponse(io.BufferedIOBase):

    def __init__(self, sock, debuglevel=0, method=None, url=None):
        self.fp = sock.makefile('rb')
        self.debuglevel = debuglevel
        self._method = method
        self.headers = self.msg = None
        self.version = _UNKNOWN
        self.status = _UNKNOWN
        self.reason = _UNKNOWN
        self.chunked = _UNKNOWN
        self.chunk_left = _UNKNOWN
        self.length = _UNKNOWN
        self.will_close = _UNKNOWN

    def _read_status(self):
        line = str(self.fp.readline(_MAXLINE + 1), 'iso-8859-1')
        if len(line) > _MAXLINE:
            raise LineTooLong('status line')
        if self.debuglevel > 0:
            print('reply:', repr(line))
        if not line:
            raise RemoteDisconnected(
                'Remote end closed connection without response')
        try:
            version, status, reason = line.split(None, 2)
        except ValueError:
            try:
                version, status = line.split(None, 1)
                reason = ''
            except ValueError:
                version = ''
        if not version.startswith('HTTP/'):
            self._close_conn()
            raise BadStatusLine(line)
        try:
            status = int(status)
            if status < 100 or status > 999:
                raise BadStatusLine(line)
        except ValueError:
            raise BadStatusLine(line)
        return version, status, reason

    def begin(self):
        if self.headers is not None:
            return
        while True:
            version, status, reason = self._read_status()
            if status != CONTINUE:
                break
            while True:
                skip = self.fp.readline(_MAXLINE + 1)
                if len(skip) > _MAXLINE:
                    raise LineTooLong('header line')
                skip = skip.strip()
                if not skip:
                    break
                if self.debuglevel > 0:
                    print('header:', skip)
        self.code = self.status = status
        self.reason = reason.strip()
        if version in ('HTTP/1.0', 'HTTP/0.9'):
            self.version = 10
        elif version.startswith('HTTP/1.'):
            self.version = 11
        else:
            raise UnknownProtocol(version)
        self.headers = self.msg = parse_headers(self.fp)
        if self.debuglevel > 0:
            for hdr in self.headers:
                print('header:', hdr, end=' ')
        tr_enc = self.headers.get('transfer-encoding')
        if tr_enc and tr_enc.lower() == 'chunked':
            self.chunked = True
            self.chunk_left = None
        else:
            self.chunked = False
        self.will_close = self._check_close()
        self.length = None
        length = self.headers.get('content-length')
        tr_enc = self.headers.get('transfer-encoding')
        if length and not self.chunked:
            try:
                self.length = int(length)
            except ValueError:
                self.length = None
            else:
                if self.length < 0:
                    self.length = None
        else:
            self.length = None
        if (status == NO_CONTENT or status == NOT_MODIFIED or 100 <= status <
            200 or self._method == 'HEAD'):
            self.length = 0
        if not self.will_close and not self.chunked and self.length is None:
            self.will_close = True

    def _check_close(self):
        conn = self.headers.get('connection')
        if self.version == 11:
            conn = self.headers.get('connection')
            if conn and 'close' in conn.lower():
                return True
            return False
        if self.headers.get('keep-alive'):
            return False
        if conn and 'keep-alive' in conn.lower():
            return False
        pconn = self.headers.get('proxy-connection')
        if pconn and 'keep-alive' in pconn.lower():
            return False
        return True

    def _close_conn(self):
        fp = self.fp
        self.fp = None
        fp.close()

    def close(self):
        try:
            super().close()
        finally:
            if self.fp:
                self._close_conn()

    def flush(self):
        super().flush()
        if self.fp:
            self.fp.flush()

    def readable(self):
        """Always returns True"""
        return True

    def isclosed(self):
        """True if the connection is closed."""
        return self.fp is None

    def read(self, amt=None):
        if self.fp is None:
            return b''
        if self._method == 'HEAD':
            self._close_conn()
            return b''
        if amt is not None:
            b = bytearray(amt)
            n = self.readinto(b)
            return memoryview(b)[:n].tobytes()
        else:
            if self.chunked:
                return self._readall_chunked()
            if self.length is None:
                s = self.fp.read()
            else:
                try:
                    s = self._safe_read(self.length)
                except IncompleteRead:
                    self._close_conn()
                    raise
                self.length = 0
            self._close_conn()
            return s

    def readinto(self, b):
        """Read up to len(b) bytes into bytearray b and return the number
        of bytes read.
        """
        if self.fp is None:
            return 0
        if self._method == 'HEAD':
            self._close_conn()
            return 0
        if self.chunked:
            return self._readinto_chunked(b)
        if self.length is not None:
            if len(b) > self.length:
                b = memoryview(b)[0:self.length]
        n = self.fp.readinto(b)
        if not n and b:
            self._close_conn()
        elif self.length is not None:
            self.length -= n
            if not self.length:
                self._close_conn()
        return n

    def _read_next_chunk_size(self):
        line = self.fp.readline(_MAXLINE + 1)
        if len(line) > _MAXLINE:
            raise LineTooLong('chunk size')
        i = line.find(b';')
        if i >= 0:
            line = line[:i]
        try:
            return int(line, 16)
        except ValueError:
            self._close_conn()
            raise

    def _read_and_discard_trailer(self):
        while True:
            line = self.fp.readline(_MAXLINE + 1)
            if len(line) > _MAXLINE:
                raise LineTooLong('trailer line')
            if not line:
                break
            if line in (b'\r\n', b'\n', b''):
                break

    def _get_chunk_left(self):
        chunk_left = self.chunk_left
        if not chunk_left:
            if chunk_left is not None:
                self._safe_read(2)
            try:
                chunk_left = self._read_next_chunk_size()
            except ValueError:
                raise IncompleteRead(b'')
            if chunk_left == 0:
                self._read_and_discard_trailer()
                self._close_conn()
                chunk_left = None
            self.chunk_left = chunk_left
        return chunk_left

    def _readall_chunked(self):
        assert self.chunked != _UNKNOWN
        value = []
        try:
            while True:
                chunk_left = self._get_chunk_left()
                if chunk_left is None:
                    break
                value.append(self._safe_read(chunk_left))
                self.chunk_left = 0
            return b''.join(value)
        except IncompleteRead:
            raise IncompleteRead(b''.join(value))

    def _readinto_chunked(self, b):
        assert self.chunked != _UNKNOWN
        total_bytes = 0
        mvb = memoryview(b)
        try:
            while True:
                chunk_left = self._get_chunk_left()
                if chunk_left is None:
                    return total_bytes
                if len(mvb) <= chunk_left:
                    n = self._safe_readinto(mvb)
                    self.chunk_left = chunk_left - n
                    return total_bytes + n
                temp_mvb = mvb[:chunk_left]
                n = self._safe_readinto(temp_mvb)
                mvb = mvb[n:]
                total_bytes += n
                self.chunk_left = 0
        except IncompleteRead:
            raise IncompleteRead(bytes(b[0:total_bytes]))

    def _safe_read(self, amt):
        """Read the number of bytes requested, compensating for partial reads.

        Normally, we have a blocking socket, but a read() can be interrupted
        by a signal (resulting in a partial read).

        Note that we cannot distinguish between EOF and an interrupt when zero
        bytes have been read. IncompleteRead() will be raised in this
        situation.

        This function should be used when <amt> bytes "should" be present for
        reading. If the bytes are truly not available (due to EOF), then the
        IncompleteRead exception can be used to detect the problem.
        """
        s = []
        while amt > 0:
            chunk = self.fp.read(min(amt, MAXAMOUNT))
            if not chunk:
                raise IncompleteRead(b''.join(s), amt)
            s.append(chunk)
            amt -= len(chunk)
        return b''.join(s)

    def _safe_readinto(self, b):
        """Same as _safe_read, but for reading into a buffer."""
        total_bytes = 0
        mvb = memoryview(b)
        while total_bytes < len(b):
            if MAXAMOUNT < len(mvb):
                temp_mvb = mvb[0:MAXAMOUNT]
                n = self.fp.readinto(temp_mvb)
            else:
                n = self.fp.readinto(mvb)
            if not n:
                raise IncompleteRead(bytes(mvb[0:total_bytes]), len(b))
            mvb = mvb[n:]
            total_bytes += n
        return total_bytes

    def read1(self, n=-1):
        """Read with at most one underlying system call.  If at least one
        byte is buffered, return that instead.
        """
        if self.fp is None or self._method == 'HEAD':
            return b''
        if self.chunked:
            return self._read1_chunked(n)
        if self.length is not None and (n < 0 or n > self.length):
            n = self.length
        try:
            result = self.fp.read1(n)
        except ValueError:
            if n >= 0:
                raise
            result = self.fp.read1(16 * 1024)
        if not result and n:
            self._close_conn()
        elif self.length is not None:
            self.length -= len(result)
        return result

    def peek(self, n=-1):
        if self.fp is None or self._method == 'HEAD':
            return b''
        if self.chunked:
            return self._peek_chunked(n)
        return self.fp.peek(n)

    def readline(self, limit=-1):
        if self.fp is None or self._method == 'HEAD':
            return b''
        if self.chunked:
            return super().readline(limit)
        if self.length is not None and (limit < 0 or limit > self.length):
            limit = self.length
        result = self.fp.readline(limit)
        if not result and limit:
            self._close_conn()
        elif self.length is not None:
            self.length -= len(result)
        return result

    def _read1_chunked(self, n):
        chunk_left = self._get_chunk_left()
        if chunk_left is None or n == 0:
            return b''
        if not 0 <= n <= chunk_left:
            n = chunk_left
        read = self.fp.read1(n)
        self.chunk_left -= len(read)
        if not read:
            raise IncompleteRead(b'')
        return read

    def _peek_chunked(self, n):
        try:
            chunk_left = self._get_chunk_left()
        except IncompleteRead:
            return b''
        if chunk_left is None:
            return b''
        return self.fp.peek(chunk_left)[:chunk_left]

    def fileno(self):
        return self.fp.fileno()

    def getheader(self, name, default=None):
        """Returns the value of the header matching *name*.

        If there are multiple matching headers, the values are
        combined into a single string separated by commas and spaces.

        If no matching header is found, returns *default* or None if
        the *default* is not specified.

        If the headers are unknown, raises http.client.ResponseNotReady.

        """
        if self.headers is None:
            raise ResponseNotReady()
        headers = self.headers.get_all(name) or default
        if isinstance(headers, str) or not hasattr(headers, '__iter__'):
            return headers
        else:
            return ', '.join(headers)

    def getheaders(self):
        """Return list of (header, value) tuples."""
        if self.headers is None:
            raise ResponseNotReady()
        return list(self.headers.items())

    def __iter__(self):
        return self

    def info(self):
        """Returns an instance of the class mimetools.Message containing
        meta-information associated with the URL.

        When the method is HTTP, these headers are those returned by
        the server at the head of the retrieved HTML page (including
        Content-Length and Content-Type).

        When the method is FTP, a Content-Length header will be
        present if (as is now usual) the server passed back a file
        length in response to the FTP retrieval request. A
        Content-Type header will be present if the MIME type can be
        guessed.

        When the method is local-file, returned headers will include
        a Date representing the file's last-modified time, a
        Content-Length giving file size, and a Content-Type
        containing a guess at the file's type. See also the
        description of the mimetools module.

        """
        return self.headers

    def geturl(self):
        """Return the real URL of the page.

        In some cases, the HTTP server redirects a client to another
        URL. The urlopen() function handles this transparently, but in
        some cases the caller needs to know which URL the client was
        redirected to. The geturl() method can be used to get at this
        redirected URL.

        """
        return self.url

    def getcode(self):
        """Return the HTTP status code that was sent with the response,
        or None if the URL is not an HTTP URL.

        """
        return self.status


class HTTPConnection:
    _http_vsn = 11
    _http_vsn_str = 'HTTP/1.1'
    response_class = HTTPResponse
    default_port = HTTP_PORT
    auto_open = 1
    debuglevel = 0

    @staticmethod
    def _is_textIO(stream):
        """Test whether a file-like object is a text or a binary stream.
        """
        return isinstance(stream, io.TextIOBase)

    @staticmethod
    def _get_content_length(body, method):
        """Get the content-length based on the body.

        If the body is None, we set Content-Length: 0 for methods that expect
        a body (RFC 7230, Section 3.3.2). We also set the Content-Length for
        any method if the body is a str or bytes-like object and not a file.
        """
        if body is None:
            if method.upper() in _METHODS_EXPECTING_BODY:
                return 0
            else:
                return None
        if hasattr(body, 'read'):
            return None
        try:
            mv = memoryview(body)
            return mv.nbytes
        except TypeError:
            pass
        if isinstance(body, str):
            return len(body)
        return None

    def __init__(self, host, port=None, timeout=socket.
        _GLOBAL_DEFAULT_TIMEOUT, source_address=None):
        self.timeout = timeout
        self.source_address = source_address
        self.sock = None
        self._buffer = []
        self.__response = None
        self.__state = _CS_IDLE
        self._method = None
        self._tunnel_host = None
        self._tunnel_port = None
        self._tunnel_headers = {}
        self.host, self.port = self._get_hostport(host, port)
        self._create_connection = socket.create_connection

    def set_tunnel(self, host, port=None, headers=None):
        """Set up host and port for HTTP CONNECT tunnelling.

        In a connection that uses HTTP CONNECT tunneling, the host passed to the
        constructor is used as a proxy server that relays all communication to
        the endpoint passed to `set_tunnel`. This done by sending an HTTP
        CONNECT request to the proxy server when the connection is established.

        This method must be called before the HTML connection has been
        established.

        The headers argument should be a mapping of extra HTTP headers to send
        with the CONNECT request.
        """
        if self.sock:
            raise RuntimeError("Can't set up tunnel for established connection"
                )
        self._tunnel_host, self._tunnel_port = self._get_hostport(host, port)
        if headers:
            self._tunnel_headers = headers
        else:
            self._tunnel_headers.clear()

    def _get_hostport(self, host, port):
        if port is None:
            i = host.rfind(':')
            j = host.rfind(']')
            if i > j:
                try:
                    port = int(host[i + 1:])
                except ValueError:
                    if host[i + 1:] == '':
                        port = self.default_port
                    else:
                        raise InvalidURL("nonnumeric port: '%s'" % host[i + 1:]
                            )
                host = host[:i]
            else:
                port = self.default_port
            if host and host[0] == '[' and host[-1] == ']':
                host = host[1:-1]
        return host, port

    def set_debuglevel(self, level):
        self.debuglevel = level

    def _tunnel(self):
        connect_str = 'CONNECT %s:%d HTTP/1.0\r\n' % (self._tunnel_host,
            self._tunnel_port)
        connect_bytes = connect_str.encode('ascii')
        self.send(connect_bytes)
        for header, value in self._tunnel_headers.items():
            header_str = '%s: %s\r\n' % (header, value)
            header_bytes = header_str.encode('latin-1')
            self.send(header_bytes)
        self.send(b'\r\n')
        response = self.response_class(self.sock, method=self._method)
        version, code, message = response._read_status()
        if code != http.HTTPStatus.OK:
            self.close()
            raise OSError('Tunnel connection failed: %d %s' % (code,
                message.strip()))
        while True:
            line = response.fp.readline(_MAXLINE + 1)
            if len(line) > _MAXLINE:
                raise LineTooLong('header line')
            if not line:
                break
            if line in (b'\r\n', b'\n', b''):
                break
            if self.debuglevel > 0:
                print('header:', line.decode())

    def connect(self):
        """Connect to the host and port specified in __init__."""
        self.sock = self._create_connection((self.host, self.port), self.
            timeout, self.source_address)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if self._tunnel_host:
            self._tunnel()

    def close(self):
        """Close the connection to the HTTP server."""
        self.__state = _CS_IDLE
        try:
            sock = self.sock
            if sock:
                self.sock = None
                sock.close()
        finally:
            response = self.__response
            if response:
                self.__response = None
                response.close()

    def send(self, data):
        """Send `data' to the server.
        ``data`` can be a string object, a bytes object, an array object, a
        file-like object that supports a .read() method, or an iterable object.
        """
        if self.sock is None:
            if self.auto_open:
                self.connect()
            else:
                raise NotConnected()
        if self.debuglevel > 0:
            print('send:', repr(data))
        blocksize = 8192
        if hasattr(data, 'read'):
            if self.debuglevel > 0:
                print('sendIng a read()able')
            encode = self._is_textIO(data)
            if encode and self.debuglevel > 0:
                print('encoding file using iso-8859-1')
            while 1:
                datablock = data.read(blocksize)
                if not datablock:
                    break
                if encode:
                    datablock = datablock.encode('iso-8859-1')
                self.sock.sendall(datablock)
            return
        try:
            self.sock.sendall(data)
        except TypeError:
            if isinstance(data, collections.Iterable):
                for d in data:
                    self.sock.sendall(d)
            else:
                raise TypeError(
                    'data should be a bytes-like object or an iterable, got %r'
                     % type(data))

    def _output(self, s):
        """Add a line of output to the current request buffer.

        Assumes that the line does *not* end with \\r\\n.
        """
        self._buffer.append(s)

    def _read_readable(self, readable):
        blocksize = 8192
        if self.debuglevel > 0:
            print('sendIng a read()able')
        encode = self._is_textIO(readable)
        if encode and self.debuglevel > 0:
            print('encoding file using iso-8859-1')
        while True:
            datablock = readable.read(blocksize)
            if not datablock:
                break
            if encode:
                datablock = datablock.encode('iso-8859-1')
            yield datablock

    def _send_output(self, message_body=None, encode_chunked=False):
        """Send the currently buffered request and clear the buffer.

        Appends an extra \\r\\n to the buffer.
        A message_body may be specified, to be appended to the request.
        """
        self._buffer.extend((b'', b''))
        msg = b'\r\n'.join(self._buffer)
        del self._buffer[:]
        self.send(msg)
        if message_body is not None:
            if hasattr(message_body, 'read'):
                chunks = self._read_readable(message_body)
            else:
                try:
                    memoryview(message_body)
                except TypeError:
                    try:
                        chunks = iter(message_body)
                    except TypeError:
                        raise TypeError(
                            'message_body should be a bytes-like object or an iterable, got %r'
                             % type(message_body))
                else:
                    chunks = message_body,
            for chunk in chunks:
                if not chunk:
                    if self.debuglevel > 0:
                        print('Zero length chunk ignored')
                    continue
                if encode_chunked and self._http_vsn == 11:
                    chunk = f'{len(chunk):X}\r\n'.encode('ascii'
                        ) + chunk + b'\r\n'
                self.send(chunk)
            if encode_chunked and self._http_vsn == 11:
                self.send(b'0\r\n\r\n')

    def putrequest(self, method, url, skip_host=False, skip_accept_encoding
        =False):
        """Send a request to the server.

        `method' specifies an HTTP request method, e.g. 'GET'.
        `url' specifies the object being requested, e.g. '/index.html'.
        `skip_host' if True does not add automatically a 'Host:' header
        `skip_accept_encoding' if True does not add automatically an
           'Accept-Encoding:' header
        """
        if self.__response and self.__response.isclosed():
            self.__response = None
        if self.__state == _CS_IDLE:
            self.__state = _CS_REQ_STARTED
        else:
            raise CannotSendRequest(self.__state)
        self._method = method
        if not url:
            url = '/'
        request = '%s %s %s' % (method, url, self._http_vsn_str)
        self._output(request.encode('ascii'))
        if self._http_vsn == 11:
            if not skip_host:
                netloc = ''
                if url.startswith('http'):
                    nil, netloc, nil, nil, nil = urlsplit(url)
                if netloc:
                    try:
                        netloc_enc = netloc.encode('ascii')
                    except UnicodeEncodeError:
                        netloc_enc = netloc.encode('idna')
                    self.putheader('Host', netloc_enc)
                else:
                    if self._tunnel_host:
                        host = self._tunnel_host
                        port = self._tunnel_port
                    else:
                        host = self.host
                        port = self.port
                    try:
                        host_enc = host.encode('ascii')
                    except UnicodeEncodeError:
                        host_enc = host.encode('idna')
                    if host.find(':') >= 0:
                        host_enc = b'[' + host_enc + b']'
                    if port == self.default_port:
                        self.putheader('Host', host_enc)
                    else:
                        host_enc = host_enc.decode('ascii')
                        self.putheader('Host', '%s:%s' % (host_enc, port))
            if not skip_accept_encoding:
                self.putheader('Accept-Encoding', 'identity')
        else:
            pass

    def putheader(self, header, *values):
        """Send a request header line to the server.

        For example: h.putheader('Accept', 'text/html')
        """
        if self.__state != _CS_REQ_STARTED:
            raise CannotSendHeader()
        if hasattr(header, 'encode'):
            header = header.encode('ascii')
        if not _is_legal_header_name(header):
            raise ValueError('Invalid header name %r' % (header,))
        values = list(values)
        for i, one_value in enumerate(values):
            if hasattr(one_value, 'encode'):
                values[i] = one_value.encode('latin-1')
            elif isinstance(one_value, int):
                values[i] = str(one_value).encode('ascii')
            if _is_illegal_header_value(values[i]):
                raise ValueError('Invalid header value %r' % (values[i],))
        value = b'\r\n\t'.join(values)
        header = header + b': ' + value
        self._output(header)

    def endheaders(self, message_body=None, *, encode_chunked=False):
        """Indicate that the last header line has been sent to the server.

        This method sends the request to the server.  The optional message_body
        argument can be used to pass a message body associated with the
        request.
        """
        if self.__state == _CS_REQ_STARTED:
            self.__state = _CS_REQ_SENT
        else:
            raise CannotSendHeader()
        self._send_output(message_body, encode_chunked=encode_chunked)

    def request(self, method, url, body=None, headers={}, *, encode_chunked
        =False):
        """Send a complete request to the server."""
        self._send_request(method, url, body, headers, encode_chunked)

    def _send_request(self, method, url, body, headers, encode_chunked):
        header_names = frozenset(k.lower() for k in headers)
        skips = {}
        if 'host' in header_names:
            skips['skip_host'] = 1
        if 'accept-encoding' in header_names:
            skips['skip_accept_encoding'] = 1
        self.putrequest(method, url, **skips)
        if 'content-length' not in header_names:
            if 'transfer-encoding' not in header_names:
                encode_chunked = False
                content_length = self._get_content_length(body, method)
                if content_length is None:
                    if body is not None:
                        if self.debuglevel > 0:
                            print('Unable to determine size of %r' % body)
                        encode_chunked = True
                        self.putheader('Transfer-Encoding', 'chunked')
                else:
                    self.putheader('Content-Length', str(content_length))
        else:
            encode_chunked = False
        for hdr, value in headers.items():
            self.putheader(hdr, value)
        if isinstance(body, str):
            body = _encode(body, 'body')
        self.endheaders(body, encode_chunked=encode_chunked)

    def getresponse(self):
        """Get the response from the server.

        If the HTTPConnection is in the correct state, returns an
        instance of HTTPResponse or of whatever object is returned by
        the response_class variable.

        If a request has not been sent or if a previous response has
        not be handled, ResponseNotReady is raised.  If the HTTP
        response indicates that the connection should be closed, then
        it will be closed before the response is returned.  When the
        connection is closed, the underlying socket is closed.
        """
        if self.__response and self.__response.isclosed():
            self.__response = None
        if self.__state != _CS_REQ_SENT or self.__response:
            raise ResponseNotReady(self.__state)
        if self.debuglevel > 0:
            response = self.response_class(self.sock, self.debuglevel,
                method=self._method)
        else:
            response = self.response_class(self.sock, method=self._method)
        try:
            try:
                response.begin()
            except ConnectionError:
                self.close()
                raise
            assert response.will_close != _UNKNOWN
            self.__state = _CS_IDLE
            if response.will_close:
                self.close()
            else:
                self.__response = response
            return response
        except:
            response.close()
            raise


try:
    import ssl
except ImportError:
    pass
else:


    class HTTPSConnection(HTTPConnection):
        """This class allows communication via SSL."""
        default_port = HTTPS_PORT

        def __init__(self, host, port=None, key_file=None, cert_file=None,
            timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, *,
            context=None, check_hostname=None):
            super(HTTPSConnection, self).__init__(host, port, timeout,
                source_address)
            if (key_file is not None or cert_file is not None or 
                check_hostname is not None):
                import warnings
                warnings.warn(
                    'key_file, cert_file and check_hostname are deprecated, use a custom context instead.'
                    , DeprecationWarning, 2)
            self.key_file = key_file
            self.cert_file = cert_file
            if context is None:
                context = ssl._create_default_https_context()
            will_verify = context.verify_mode != ssl.CERT_NONE
            if check_hostname is None:
                check_hostname = context.check_hostname
            if check_hostname and not will_verify:
                raise ValueError(
                    'check_hostname needs a SSL context with either CERT_OPTIONAL or CERT_REQUIRED'
                    )
            if key_file or cert_file:
                context.load_cert_chain(cert_file, key_file)
            self._context = context
            self._check_hostname = check_hostname

        def connect(self):
            """Connect to a host on a given (SSL) port."""
            super().connect()
            if self._tunnel_host:
                server_hostname = self._tunnel_host
            else:
                server_hostname = self.host
            self.sock = self._context.wrap_socket(self.sock,
                server_hostname=server_hostname)
            if not self._context.check_hostname and self._check_hostname:
                try:
                    ssl.match_hostname(self.sock.getpeercert(), server_hostname
                        )
                except Exception:
                    self.sock.shutdown(socket.SHUT_RDWR)
                    self.sock.close()
                    raise
    __all__.append('HTTPSConnection')


class HTTPException(Exception):
    pass


class NotConnected(HTTPException):
    pass


class InvalidURL(HTTPException):
    pass


class UnknownProtocol(HTTPException):

    def __init__(self, version):
        self.args = version,
        self.version = version


class UnknownTransferEncoding(HTTPException):
    pass


class UnimplementedFileMode(HTTPException):
    pass


class IncompleteRead(HTTPException):

    def __init__(self, partial, expected=None):
        self.args = partial,
        self.partial = partial
        self.expected = expected

    def __repr__(self):
        if self.expected is not None:
            e = ', %i more expected' % self.expected
        else:
            e = ''
        return '%s(%i bytes read%s)' % (self.__class__.__name__, len(self.
            partial), e)

    def __str__(self):
        return repr(self)


class ImproperConnectionState(HTTPException):
    pass


class CannotSendRequest(ImproperConnectionState):
    pass


class CannotSendHeader(ImproperConnectionState):
    pass


class ResponseNotReady(ImproperConnectionState):
    pass


class BadStatusLine(HTTPException):

    def __init__(self, line):
        if not line:
            line = repr(line)
        self.args = line,
        self.line = line


class LineTooLong(HTTPException):

    def __init__(self, line_type):
        HTTPException.__init__(self, 
            'got more than %d bytes when reading %s' % (_MAXLINE, line_type))


class RemoteDisconnected(ConnectionResetError, BadStatusLine):

    def __init__(self, *pos, **kw):
        BadStatusLine.__init__(self, '')
        ConnectionResetError.__init__(self, *pos, **kw)


error = HTTPException
