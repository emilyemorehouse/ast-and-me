import unittest.mock
from test import support
import builtins
import io
import os
import shutil
import subprocess
import uuid


def importable(name):
    try:
        __import__(name)
        return True
    except:
        return False


class TestUUID(unittest.TestCase):

    def test_UUID(self):
        equal = self.assertEqual
        ascending = []
        for string, curly, hex, bytes, bytes_le, fields, integer, urn, time, clock_seq, variant, version in [
            ('00000000-0000-0000-0000-000000000000',
            '{00000000-0000-0000-0000-000000000000}',
            '00000000000000000000000000000000',
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            ,
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            , (0, 0, 0, 0, 0, 0), 0,
            'urn:uuid:00000000-0000-0000-0000-000000000000', 0, 0, uuid.
            RESERVED_NCS, None), ('00010203-0405-0607-0809-0a0b0c0d0e0f',
            '{00010203-0405-0607-0809-0a0b0c0d0e0f}',
            '000102030405060708090a0b0c0d0e0f',
            b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f',
            b'\x03\x02\x01\x00\x05\x04\x07\x06\x08\t\n\x0b\x0c\r\x0e\x0f',
            (66051, 1029, 1543, 8, 9, 11042563100175), 
            5233100606242806050955395731361295,
            'urn:uuid:00010203-0405-0607-0809-0a0b0c0d0e0f', 
            434320308585955843, 2057, uuid.RESERVED_NCS, None), (
            '02d9e6d5-9467-382e-8f9b-9300a64ac3cd',
            '{02d9e6d5-9467-382e-8f9b-9300a64ac3cd}',
            '02d9e6d59467382e8f9b9300a64ac3cd',
            b'\x02\xd9\xe6\xd5\x94g8.\x8f\x9b\x93\x00\xa6J\xc3\xcd',
            b'\xd5\xe6\xd9\x02g\x94.8\x8f\x9b\x93\x00\xa6J\xc3\xcd', (
            47834837, 37991, 14382, 143, 155, 161630999200717), 
            3789866285607910888100818383505376205,
            'urn:uuid:02d9e6d5-9467-382e-8f9b-9300a64ac3cd', 
            589571771382490837, 3995, uuid.RFC_4122, 3), (
            '12345678-1234-5678-1234-567812345678',
            '{12345678-1234-5678-1234-567812345678}',
            '12345678123456781234567812345678', b'\x124Vx' * 4,
            b'xV4\x124\x12xV\x124Vx\x124Vx', (305419896, 4660, 22136, 18, 
            52, 95073701484152), 24197857161011715162171839636988778104,
            'urn:uuid:12345678-1234-5678-1234-567812345678', 
            466142576285865592, 4660, uuid.RESERVED_NCS, None), (
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
            '{6ba7b810-9dad-11d1-80b4-00c04fd430c8}',
            '6ba7b8109dad11d180b400c04fd430c8',
            b'k\xa7\xb8\x10\x9d\xad\x11\xd1\x80\xb4\x00\xc0O\xd40\xc8',
            b'\x10\xb8\xa7k\xad\x9d\xd1\x11\x80\xb4\x00\xc0O\xd40\xc8', (
            1806153744, 40365, 4561, 128, 180, 825973027016), 
            143098242404177361603877621312831893704,
            'urn:uuid:6ba7b810-9dad-11d1-80b4-00c04fd430c8', 
            131059232331511824, 180, uuid.RFC_4122, 1), (
            '6ba7b811-9dad-11d1-80b4-00c04fd430c8',
            '{6ba7b811-9dad-11d1-80b4-00c04fd430c8}',
            '6ba7b8119dad11d180b400c04fd430c8',
            b'k\xa7\xb8\x11\x9d\xad\x11\xd1\x80\xb4\x00\xc0O\xd40\xc8',
            b'\x11\xb8\xa7k\xad\x9d\xd1\x11\x80\xb4\x00\xc0O\xd40\xc8', (
            1806153745, 40365, 4561, 128, 180, 825973027016), 
            143098242483405524118141958906375844040,
            'urn:uuid:6ba7b811-9dad-11d1-80b4-00c04fd430c8', 
            131059232331511825, 180, uuid.RFC_4122, 1), (
            '6ba7b812-9dad-11d1-80b4-00c04fd430c8',
            '{6ba7b812-9dad-11d1-80b4-00c04fd430c8}',
            '6ba7b8129dad11d180b400c04fd430c8',
            b'k\xa7\xb8\x12\x9d\xad\x11\xd1\x80\xb4\x00\xc0O\xd40\xc8',
            b'\x12\xb8\xa7k\xad\x9d\xd1\x11\x80\xb4\x00\xc0O\xd40\xc8', (
            1806153746, 40365, 4561, 128, 180, 825973027016), 
            143098242562633686632406296499919794376,
            'urn:uuid:6ba7b812-9dad-11d1-80b4-00c04fd430c8', 
            131059232331511826, 180, uuid.RFC_4122, 1), (
            '6ba7b814-9dad-11d1-80b4-00c04fd430c8',
            '{6ba7b814-9dad-11d1-80b4-00c04fd430c8}',
            '6ba7b8149dad11d180b400c04fd430c8',
            b'k\xa7\xb8\x14\x9d\xad\x11\xd1\x80\xb4\x00\xc0O\xd40\xc8',
            b'\x14\xb8\xa7k\xad\x9d\xd1\x11\x80\xb4\x00\xc0O\xd40\xc8', (
            1806153748, 40365, 4561, 128, 180, 825973027016), 
            143098242721090011660934971687007695048,
            'urn:uuid:6ba7b814-9dad-11d1-80b4-00c04fd430c8', 
            131059232331511828, 180, uuid.RFC_4122, 1), (
            '7d444840-9dc0-11d1-b245-5ffdce74fad2',
            '{7d444840-9dc0-11d1-b245-5ffdce74fad2}',
            '7d4448409dc011d1b2455ffdce74fad2',
            b'}DH@\x9d\xc0\x11\xd1\xb2E_\xfd\xcet\xfa\xd2',
            b'@HD}\xc0\x9d\xd1\x11\xb2E_\xfd\xcet\xfa\xd2', (2101626944, 
            40384, 4561, 178, 69, 105543695137490), 
            166508041112410060672666770310773930706,
            'urn:uuid:7d444840-9dc0-11d1-b245-5ffdce74fad2', 
            131059314231363648, 12869, uuid.RFC_4122, 1), (
            'e902893a-9d22-3c7e-a7b8-d6e313b71d9f',
            '{e902893a-9d22-3c7e-a7b8-d6e313b71d9f}',
            'e902893a9d223c7ea7b8d6e313b71d9f',
            b'\xe9\x02\x89:\x9d"<~\xa7\xb8\xd6\xe3\x13\xb7\x1d\x9f',
            b':\x89\x02\xe9"\x9d~<\xa7\xb8\xd6\xe3\x13\xb7\x1d\x9f', (
            3909257530, 40226, 15486, 167, 184, 236270776688031), 
            309723290945582129846206211755626405279,
            'urn:uuid:e902893a-9d22-3c7e-a7b8-d6e313b71d9f', 
            900329748784384314, 10168, uuid.RFC_4122, 3), (
            'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf',
            '{eb424026-6f54-4ef8-a4d0-bb658a1fc6cf}',
            'eb4240266f544ef8a4d0bb658a1fc6cf',
            b'\xebB@&oTN\xf8\xa4\xd0\xbbe\x8a\x1f\xc6\xcf',
            b'&@B\xebTo\xf8N\xa4\xd0\xbbe\x8a\x1f\xc6\xcf', (3946987558, 
            28500, 20216, 164, 208, 206044783429327), 
            312712571721458096795100956955942831823,
            'urn:uuid:eb424026-6f54-4ef8-a4d0-bb658a1fc6cf', 
            1078734521270157350, 9424, uuid.RFC_4122, 4), (
            'f81d4fae-7dec-11d0-a765-00a0c91e6bf6',
            '{f81d4fae-7dec-11d0-a765-00a0c91e6bf6}',
            'f81d4fae7dec11d0a76500a0c91e6bf6',
            b'\xf8\x1dO\xae}\xec\x11\xd0\xa7e\x00\xa0\xc9\x1ek\xf6',
            b'\xaeO\x1d\xf8\xec}\xd0\x11\xa7e\x00\xa0\xc9\x1ek\xf6', (
            4162670510, 32236, 4560, 167, 101, 690568981494), 
            329800735698586629295641978511506172918,
            'urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6', 
            130742845922168750, 10085, uuid.RFC_4122, 1), (
            'fffefdfc-fffe-fffe-fffe-fffefdfcfbfa',
            '{fffefdfc-fffe-fffe-fffe-fffefdfcfbfa}',
            'fffefdfcfffefffefffefffefdfcfbfa',
            b'\xff\xfe\xfd\xfc\xff\xfe\xff\xfe\xff\xfe\xff\xfe\xfd\xfc\xfb\xfa'
            ,
            b'\xfc\xfd\xfe\xff\xfe\xff\xfe\xff\xff\xfe\xff\xfe\xfd\xfc\xfb\xfa'
            , (4294901244, 65534, 65534, 255, 254, 281470647991290), 
            340277133821575024845345576078114880506,
            'urn:uuid:fffefdfc-fffe-fffe-fffe-fffefdfcfbfa', 
            1152640025335102972, 16382, uuid.RESERVED_FUTURE, None), (
            'ffffffff-ffff-ffff-ffff-ffffffffffff',
            '{ffffffff-ffff-ffff-ffff-ffffffffffff}',
            'ffffffffffffffffffffffffffffffff', b'\xff' * 16, b'\xff' * 16,
            (4294967295, 65535, 65535, 255, 255, 281474976710655), 
            340282366920938463463374607431768211455,
            'urn:uuid:ffffffff-ffff-ffff-ffff-ffffffffffff', 
            1152921504606846975, 16383, uuid.RESERVED_FUTURE, None)]:
            equivalents = []
            for u in [uuid.UUID(string), uuid.UUID(curly), uuid.UUID(hex),
                uuid.UUID(bytes=bytes), uuid.UUID(bytes_le=bytes_le), uuid.
                UUID(fields=fields), uuid.UUID(int=integer), uuid.UUID(urn)]:
                equal(str(u), string)
                equal(int(u), integer)
                equal(u.bytes, bytes)
                equal(u.bytes_le, bytes_le)
                equal(u.fields, fields)
                equal(u.time_low, fields[0])
                equal(u.time_mid, fields[1])
                equal(u.time_hi_version, fields[2])
                equal(u.clock_seq_hi_variant, fields[3])
                equal(u.clock_seq_low, fields[4])
                equal(u.node, fields[5])
                equal(u.hex, hex)
                equal(u.int, integer)
                equal(u.urn, urn)
                equal(u.time, time)
                equal(u.clock_seq, clock_seq)
                equal(u.variant, variant)
                equal(u.version, version)
                equivalents.append(u)
            for u in equivalents:
                for v in equivalents:
                    equal(u, v)
            equal(type(u.bytes), builtins.bytes)
            equal(type(u.bytes_le), builtins.bytes)
            ascending.append(u)
        for i in range(len(ascending)):
            for j in range(len(ascending)):
                equal(i < j, ascending[i] < ascending[j])
                equal(i <= j, ascending[i] <= ascending[j])
                equal(i == j, ascending[i] == ascending[j])
                equal(i > j, ascending[i] > ascending[j])
                equal(i >= j, ascending[i] >= ascending[j])
                equal(i != j, ascending[i] != ascending[j])
        resorted = ascending[:]
        resorted.reverse()
        resorted.sort()
        equal(ascending, resorted)

    def test_exceptions(self):
        badvalue = lambda f: self.assertRaises(ValueError, f)
        badtype = lambda f: self.assertRaises(TypeError, f)
        badvalue(lambda : uuid.UUID(''))
        badvalue(lambda : uuid.UUID('abc'))
        badvalue(lambda : uuid.UUID('1234567812345678123456781234567'))
        badvalue(lambda : uuid.UUID('123456781234567812345678123456789'))
        badvalue(lambda : uuid.UUID('123456781234567812345678z2345678'))
        badvalue(lambda : uuid.UUID(bytes='abc'))
        badvalue(lambda : uuid.UUID(bytes='\x00' * 15))
        badvalue(lambda : uuid.UUID(bytes='\x00' * 17))
        badvalue(lambda : uuid.UUID(bytes_le='abc'))
        badvalue(lambda : uuid.UUID(bytes_le='\x00' * 15))
        badvalue(lambda : uuid.UUID(bytes_le='\x00' * 17))
        badvalue(lambda : uuid.UUID(fields=(1,)))
        badvalue(lambda : uuid.UUID(fields=(1, 2, 3, 4, 5)))
        badvalue(lambda : uuid.UUID(fields=(1, 2, 3, 4, 5, 6, 7)))
        badvalue(lambda : uuid.UUID(fields=(-1, 0, 0, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(4294967296, 0, 0, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, -1, 0, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 65536, 0, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, -1, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 65536, 0, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, -1, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, 256, 0, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, 0, -1, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, 0, 256, 0)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, 0, 0, -1)))
        badvalue(lambda : uuid.UUID(fields=(0, 0, 0, 0, 0, 281474976710656)))
        badvalue(lambda : uuid.UUID('00' * 16, version=0))
        badvalue(lambda : uuid.UUID('00' * 16, version=6))
        badvalue(lambda : uuid.UUID(int=-1))
        badvalue(lambda : uuid.UUID(int=1 << 128))
        h, b, f, i = '00' * 16, b'\x00' * 16, (0, 0, 0, 0, 0, 0), 0
        uuid.UUID(h)
        uuid.UUID(hex=h)
        uuid.UUID(bytes=b)
        uuid.UUID(bytes_le=b)
        uuid.UUID(fields=f)
        uuid.UUID(int=i)
        badtype(lambda : uuid.UUID())
        badtype(lambda : uuid.UUID(h, b))
        badtype(lambda : uuid.UUID(h, b, b))
        badtype(lambda : uuid.UUID(h, b, b, f))
        badtype(lambda : uuid.UUID(h, b, b, f, i))
        for hh in [[], [('hex', h)]]:
            for bb in [[], [('bytes', b)]]:
                for bble in [[], [('bytes_le', b)]]:
                    for ii in [[], [('int', i)]]:
                        for ff in [[], [('fields', f)]]:
                            args = dict(hh + bb + bble + ii + ff)
                            if len(args) != 0:
                                badtype(lambda : uuid.UUID(h, **args))
                            if len(args) != 1:
                                badtype(lambda : uuid.UUID(**args))
        u = uuid.UUID(h)
        badtype(lambda : setattr(u, 'hex', h))
        badtype(lambda : setattr(u, 'bytes', b))
        badtype(lambda : setattr(u, 'bytes_le', b))
        badtype(lambda : setattr(u, 'fields', f))
        badtype(lambda : setattr(u, 'int', i))
        badtype(lambda : setattr(u, 'time_low', 0))
        badtype(lambda : setattr(u, 'time_mid', 0))
        badtype(lambda : setattr(u, 'time_hi_version', 0))
        badtype(lambda : setattr(u, 'time_hi_version', 0))
        badtype(lambda : setattr(u, 'clock_seq_hi_variant', 0))
        badtype(lambda : setattr(u, 'clock_seq_low', 0))
        badtype(lambda : setattr(u, 'node', 0))
        badtype(lambda : u < object())
        badtype(lambda : u > object())

    def test_getnode(self):
        node1 = uuid.getnode()
        self.assertTrue(0 < node1 < 1 << 48, '%012x' % node1)
        node2 = uuid.getnode()
        self.assertEqual(node1, node2, '%012x != %012x' % (node1, node2))

    @unittest.skipUnless(importable('ctypes'), 'requires ctypes')
    def test_uuid1(self):
        equal = self.assertEqual
        for u in [uuid.uuid1() for i in range(10)]:
            equal(u.variant, uuid.RFC_4122)
            equal(u.version, 1)
        uuids = {}
        for u in [uuid.uuid1() for i in range(1000)]:
            uuids[u] = 1
        equal(len(uuids.keys()), 1000)
        u = uuid.uuid1(0)
        equal(u.node, 0)
        u = uuid.uuid1(20015998343868)
        equal(u.node, 20015998343868)
        u = uuid.uuid1(281474976710655)
        equal(u.node, 281474976710655)
        u = uuid.uuid1(20015998343868, 0)
        equal(u.node, 20015998343868)
        equal((u.clock_seq_hi_variant & 63) << 8 | u.clock_seq_low, 0)
        u = uuid.uuid1(20015998343868, 4660)
        equal(u.node, 20015998343868)
        equal((u.clock_seq_hi_variant & 63) << 8 | u.clock_seq_low, 4660)
        u = uuid.uuid1(20015998343868, 16383)
        equal(u.node, 20015998343868)
        equal((u.clock_seq_hi_variant & 63) << 8 | u.clock_seq_low, 16383)

    def test_uuid3(self):
        equal = self.assertEqual
        for u, v in [(uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'),
            '6fa459ea-ee8a-3ca4-894e-db77e160355e'), (uuid.uuid3(uuid.
            NAMESPACE_URL, 'http://python.org/'),
            '9fe8e8c4-aaa8-32a9-a55c-4535a88b748d'), (uuid.uuid3(uuid.
            NAMESPACE_OID, '1.3.6.1'),
            'dd1a1cef-13d5-368a-ad82-eca71acd4cd1'), (uuid.uuid3(uuid.
            NAMESPACE_X500, 'c=ca'), '658d3002-db6b-3040-a1d1-8ddd7d189a4d')]:
            equal(u.variant, uuid.RFC_4122)
            equal(u.version, 3)
            equal(u, uuid.UUID(v))
            equal(str(u), v)

    def test_uuid4(self):
        equal = self.assertEqual
        for u in [uuid.uuid4() for i in range(10)]:
            equal(u.variant, uuid.RFC_4122)
            equal(u.version, 4)
        uuids = {}
        for u in [uuid.uuid4() for i in range(1000)]:
            uuids[u] = 1
        equal(len(uuids.keys()), 1000)

    def test_uuid5(self):
        equal = self.assertEqual
        for u, v in [(uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org'),
            '886313e1-3b8a-5372-9b90-0c9aee199e5d'), (uuid.uuid5(uuid.
            NAMESPACE_URL, 'http://python.org/'),
            '4c565f0d-3f5a-5890-b41b-20cf47701c5e'), (uuid.uuid5(uuid.
            NAMESPACE_OID, '1.3.6.1'),
            '1447fa61-5277-5fef-a9b3-fbc6e44f4af3'), (uuid.uuid5(uuid.
            NAMESPACE_X500, 'c=ca'), 'cc957dd1-a972-5349-98cd-874190002798')]:
            equal(u.variant, uuid.RFC_4122)
            equal(u.version, 5)
            equal(u, uuid.UUID(v))
            equal(str(u), v)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def testIssue8621(self):
        fds = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(fds[0])
            value = uuid.uuid4()
            os.write(fds[1], value.hex.encode('latin-1'))
            os._exit(0)
        else:
            os.close(fds[1])
            self.addCleanup(os.close, fds[0])
            parent_value = uuid.uuid4().hex
            os.waitpid(pid, 0)
            child_value = os.read(fds[0], 100).decode('latin-1')
            self.assertNotEqual(parent_value, child_value)


class TestInternals(unittest.TestCase):

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_find_mac(self):
        data = """
fake hwaddr
cscotun0  Link encap:UNSPEC  HWaddr 00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00
eth0      Link encap:Ethernet  HWaddr 12:34:56:78:90:ab
"""
        popen = unittest.mock.MagicMock()
        popen.stdout = io.BytesIO(data.encode())
        with unittest.mock.patch.object(shutil, 'which', return_value=
            '/sbin/ifconfig'):
            with unittest.mock.patch.object(subprocess, 'Popen',
                return_value=popen):
                mac = uuid._find_mac(command='ifconfig', args='',
                    hw_identifiers=[b'hwaddr'], get_index=lambda x: x + 1)
        self.assertEqual(mac, 20015998341291)

    def check_node(self, node, requires=None, network=False):
        if requires and node is None:
            self.skipTest('requires ' + requires)
        hex = '%012x' % node
        if support.verbose >= 2:
            print(hex, end=' ')
        if network:
            self.assertFalse(node & 1099511627776, hex)
        self.assertTrue(0 < node < 1 << 48, '%s is not an RFC 4122 node ID' %
            hex)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_ifconfig_getnode(self):
        node = uuid._ifconfig_getnode()
        self.check_node(node, 'ifconfig', True)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_ip_getnode(self):
        node = uuid._ip_getnode()
        self.check_node(node, 'ip', True)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_arp_getnode(self):
        node = uuid._arp_getnode()
        self.check_node(node, 'arp', True)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_lanscan_getnode(self):
        node = uuid._lanscan_getnode()
        self.check_node(node, 'lanscan', True)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    def test_netstat_getnode(self):
        node = uuid._netstat_getnode()
        self.check_node(node, 'netstat', True)

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_ipconfig_getnode(self):
        node = uuid._ipconfig_getnode()
        self.check_node(node, 'ipconfig', True)

    @unittest.skipUnless(importable('win32wnet'), 'requires win32wnet')
    @unittest.skipUnless(importable('netbios'), 'requires netbios')
    def test_netbios_getnode(self):
        node = uuid._netbios_getnode()
        self.check_node(node, network=True)

    def test_random_getnode(self):
        node = uuid._random_getnode()
        self.assertTrue(node & 1099511627776, '%012x' % node)
        self.check_node(node)

    @unittest.skipUnless(os.name == 'posix', 'requires Posix')
    @unittest.skipUnless(importable('ctypes'), 'requires ctypes')
    def test_unixdll_getnode(self):
        try:
            node = uuid._unixdll_getnode()
        except TypeError:
            self.skipTest('requires uuid_generate_time')
        self.check_node(node)

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    @unittest.skipUnless(importable('ctypes'), 'requires ctypes')
    def test_windll_getnode(self):
        node = uuid._windll_getnode()
        self.check_node(node)


if __name__ == '__main__':
    unittest.main()
