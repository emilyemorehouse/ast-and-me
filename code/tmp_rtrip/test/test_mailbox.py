import os
import sys
import time
import stat
import socket
import email
import email.message
import re
import io
import tempfile
from test import support
import unittest
import textwrap
import mailbox
import glob


class TestBase:
    all_mailbox_types = (mailbox.Message, mailbox.MaildirMessage, mailbox.
        mboxMessage, mailbox.MHMessage, mailbox.BabylMessage, mailbox.
        MMDFMessage)

    def _check_sample(self, msg):
        self.assertIsInstance(msg, email.message.Message)
        self.assertIsInstance(msg, mailbox.Message)
        for key, value in _sample_headers.items():
            self.assertIn(value, msg.get_all(key))
        self.assertTrue(msg.is_multipart())
        self.assertEqual(len(msg.get_payload()), len(_sample_payloads))
        for i, payload in enumerate(_sample_payloads):
            part = msg.get_payload(i)
            self.assertIsInstance(part, email.message.Message)
            self.assertNotIsInstance(part, mailbox.Message)
            self.assertEqual(part.get_payload(), payload)

    def _delete_recursively(self, target):
        if os.path.isdir(target):
            support.rmtree(target)
        elif os.path.exists(target):
            support.unlink(target)


class TestMailbox(TestBase):
    maxDiff = None
    _factory = None
    _template = 'From: foo\n\n%s\n'

    def setUp(self):
        self._path = support.TESTFN
        self._delete_recursively(self._path)
        self._box = self._factory(self._path)

    def tearDown(self):
        self._box.close()
        self._delete_recursively(self._path)

    def test_add(self):
        keys = []
        keys.append(self._box.add(self._template % 0))
        self.assertEqual(len(self._box), 1)
        keys.append(self._box.add(mailbox.Message(_sample_message)))
        self.assertEqual(len(self._box), 2)
        keys.append(self._box.add(email.message_from_string(_sample_message)))
        self.assertEqual(len(self._box), 3)
        keys.append(self._box.add(io.BytesIO(_bytes_sample_message)))
        self.assertEqual(len(self._box), 4)
        keys.append(self._box.add(_sample_message))
        self.assertEqual(len(self._box), 5)
        keys.append(self._box.add(_bytes_sample_message))
        self.assertEqual(len(self._box), 6)
        with self.assertWarns(DeprecationWarning):
            keys.append(self._box.add(io.TextIOWrapper(io.BytesIO(
                _bytes_sample_message))))
        self.assertEqual(len(self._box), 7)
        self.assertEqual(self._box.get_string(keys[0]), self._template % 0)
        for i in (1, 2, 3, 4, 5, 6):
            self._check_sample(self._box[keys[i]])
    _nonascii_msg = textwrap.dedent(
        """            From: foo
            Subject: Falinaptár házhozszállítással. Már rendeltél?

            0
            """
        )

    def test_add_invalid_8bit_bytes_header(self):
        key = self._box.add(self._nonascii_msg.encode('latin-1'))
        self.assertEqual(len(self._box), 1)
        self.assertEqual(self._box.get_bytes(key), self._nonascii_msg.
            encode('latin-1'))

    def test_invalid_nonascii_header_as_string(self):
        subj = self._nonascii_msg.splitlines()[1]
        key = self._box.add(subj.encode('latin-1'))
        self.assertEqual(self._box.get_string(key),
            """Subject: =?unknown-8bit?b?RmFsaW5hcHThciBo4Xpob3pzeuFsbO104XNzYWwuIE3hciByZW5kZWx06Ww/?=

"""
            )

    def test_add_nonascii_string_header_raises(self):
        with self.assertRaisesRegex(ValueError, 'ASCII-only'):
            self._box.add(self._nonascii_msg)
        self._box.flush()
        self.assertEqual(len(self._box), 0)
        self.assertMailboxEmpty()

    def test_add_that_raises_leaves_mailbox_empty(self):

        def raiser(*args, **kw):
            raise Exception('a fake error')
        support.patch(self, email.generator.BytesGenerator, 'flatten', raiser)
        with self.assertRaises(Exception):
            self._box.add(email.message_from_string('From: Alphöso'))
        self.assertEqual(len(self._box), 0)
        self._box.close()
        self.assertMailboxEmpty()
    _non_latin_bin_msg = textwrap.dedent(
        """        From: foo@bar.com
        To: báz
        Subject: Maintenant je vous présente mon collègue, le pouf célèbre
        	Jean de Baddie
        Mime-Version: 1.0
        Content-Type: text/plain; charset="utf-8"
        Content-Transfer-Encoding: 8bit

        Да, они летят.
        """
        ).encode('utf-8')

    def test_add_8bit_body(self):
        key = self._box.add(self._non_latin_bin_msg)
        self.assertEqual(self._box.get_bytes(key), self._non_latin_bin_msg)
        with self._box.get_file(key) as f:
            self.assertEqual(f.read(), self._non_latin_bin_msg.replace(
                b'\n', os.linesep.encode()))
        self.assertEqual(self._box[key].get_payload(), 'Да, они летят.\n')

    def test_add_binary_file(self):
        with tempfile.TemporaryFile('wb+') as f:
            f.write(_bytes_sample_message)
            f.seek(0)
            key = self._box.add(f)
        self.assertEqual(self._box.get_bytes(key).split(b'\n'),
            _bytes_sample_message.split(b'\n'))

    def test_add_binary_nonascii_file(self):
        with tempfile.TemporaryFile('wb+') as f:
            f.write(self._non_latin_bin_msg)
            f.seek(0)
            key = self._box.add(f)
        self.assertEqual(self._box.get_bytes(key).split(b'\n'), self.
            _non_latin_bin_msg.split(b'\n'))

    def test_add_text_file_warns(self):
        with tempfile.TemporaryFile('w+') as f:
            f.write(_sample_message)
            f.seek(0)
            with self.assertWarns(DeprecationWarning):
                key = self._box.add(f)
        self.assertEqual(self._box.get_bytes(key).split(b'\n'),
            _bytes_sample_message.split(b'\n'))

    def test_add_StringIO_warns(self):
        with self.assertWarns(DeprecationWarning):
            key = self._box.add(io.StringIO(self._template % '0'))
        self.assertEqual(self._box.get_string(key), self._template % '0')

    def test_add_nonascii_StringIO_raises(self):
        with self.assertWarns(DeprecationWarning):
            with self.assertRaisesRegex(ValueError, 'ASCII-only'):
                self._box.add(io.StringIO(self._nonascii_msg))
        self.assertEqual(len(self._box), 0)
        self._box.close()
        self.assertMailboxEmpty()

    def test_remove(self):
        self._test_remove_or_delitem(self._box.remove)

    def test_delitem(self):
        self._test_remove_or_delitem(self._box.__delitem__)

    def _test_remove_or_delitem(self, method):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(self._template % 1)
        self.assertEqual(len(self._box), 2)
        method(key0)
        self.assertEqual(len(self._box), 1)
        self.assertRaises(KeyError, lambda : self._box[key0])
        self.assertRaises(KeyError, lambda : method(key0))
        self.assertEqual(self._box.get_string(key1), self._template % 1)
        key2 = self._box.add(self._template % 2)
        self.assertEqual(len(self._box), 2)
        method(key2)
        self.assertEqual(len(self._box), 1)
        self.assertRaises(KeyError, lambda : self._box[key2])
        self.assertRaises(KeyError, lambda : method(key2))
        self.assertEqual(self._box.get_string(key1), self._template % 1)
        method(key1)
        self.assertEqual(len(self._box), 0)
        self.assertRaises(KeyError, lambda : self._box[key1])
        self.assertRaises(KeyError, lambda : method(key1))

    def test_discard(self, repetitions=10):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(self._template % 1)
        self.assertEqual(len(self._box), 2)
        self._box.discard(key0)
        self.assertEqual(len(self._box), 1)
        self.assertRaises(KeyError, lambda : self._box[key0])
        self._box.discard(key0)
        self.assertEqual(len(self._box), 1)
        self.assertRaises(KeyError, lambda : self._box[key0])

    def test_get(self):
        key0 = self._box.add(self._template % 0)
        msg = self._box.get(key0)
        self.assertEqual(msg['from'], 'foo')
        self.assertEqual(msg.get_payload(), '0\n')
        self.assertIsNone(self._box.get('foo'))
        self.assertIs(self._box.get('foo', False), False)
        self._box.close()
        self._box = self._factory(self._path)
        key1 = self._box.add(self._template % 1)
        msg = self._box.get(key1)
        self.assertEqual(msg['from'], 'foo')
        self.assertEqual(msg.get_payload(), '1\n')

    def test_getitem(self):
        key0 = self._box.add(self._template % 0)
        msg = self._box[key0]
        self.assertEqual(msg['from'], 'foo')
        self.assertEqual(msg.get_payload(), '0\n')
        self.assertRaises(KeyError, lambda : self._box['foo'])
        self._box.discard(key0)
        self.assertRaises(KeyError, lambda : self._box[key0])

    def test_get_message(self):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(_sample_message)
        msg0 = self._box.get_message(key0)
        self.assertIsInstance(msg0, mailbox.Message)
        self.assertEqual(msg0['from'], 'foo')
        self.assertEqual(msg0.get_payload(), '0\n')
        self._check_sample(self._box.get_message(key1))

    def test_get_bytes(self):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(_sample_message)
        self.assertEqual(self._box.get_bytes(key0), (self._template % 0).
            encode('ascii'))
        self.assertEqual(self._box.get_bytes(key1), _bytes_sample_message)

    def test_get_string(self):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(_sample_message)
        self.assertEqual(self._box.get_string(key0), self._template % 0)
        self.assertEqual(self._box.get_string(key1).split('\n'),
            _sample_message.split('\n'))

    def test_get_file(self):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(_sample_message)
        with self._box.get_file(key0) as file:
            data0 = file.read()
        with self._box.get_file(key1) as file:
            data1 = file.read()
        self.assertEqual(data0.decode('ascii').replace(os.linesep, '\n'), 
            self._template % 0)
        self.assertEqual(data1.decode('ascii').replace(os.linesep, '\n'),
            _sample_message)

    def test_get_file_can_be_closed_twice(self):
        key = self._box.add(_sample_message)
        f = self._box.get_file(key)
        f.close()
        f.close()

    def test_iterkeys(self):
        self._check_iteration(self._box.iterkeys, do_keys=True, do_values=False
            )

    def test_keys(self):
        self._check_iteration(self._box.keys, do_keys=True, do_values=False)

    def test_itervalues(self):
        self._check_iteration(self._box.itervalues, do_keys=False,
            do_values=True)

    def test_iter(self):
        self._check_iteration(self._box.__iter__, do_keys=False, do_values=True
            )

    def test_values(self):
        self._check_iteration(self._box.values, do_keys=False, do_values=True)

    def test_iteritems(self):
        self._check_iteration(self._box.iteritems, do_keys=True, do_values=True
            )

    def test_items(self):
        self._check_iteration(self._box.items, do_keys=True, do_values=True)

    def _check_iteration(self, method, do_keys, do_values, repetitions=10):
        for value in method():
            self.fail('Not empty')
        keys, values = [], []
        for i in range(repetitions):
            keys.append(self._box.add(self._template % i))
            values.append(self._template % i)
        if do_keys and not do_values:
            returned_keys = list(method())
        elif do_values and not do_keys:
            returned_values = list(method())
        else:
            returned_keys, returned_values = [], []
            for key, value in method():
                returned_keys.append(key)
                returned_values.append(value)
        if do_keys:
            self.assertEqual(len(keys), len(returned_keys))
            self.assertEqual(set(keys), set(returned_keys))
        if do_values:
            count = 0
            for value in returned_values:
                self.assertEqual(value['from'], 'foo')
                self.assertLess(int(value.get_payload()), repetitions)
                count += 1
            self.assertEqual(len(values), count)

    def test_contains(self):
        self.assertNotIn('foo', self._box)
        key0 = self._box.add(self._template % 0)
        self.assertIn(key0, self._box)
        self.assertNotIn('foo', self._box)
        key1 = self._box.add(self._template % 1)
        self.assertIn(key1, self._box)
        self.assertIn(key0, self._box)
        self.assertNotIn('foo', self._box)
        self._box.remove(key0)
        self.assertNotIn(key0, self._box)
        self.assertIn(key1, self._box)
        self.assertNotIn('foo', self._box)
        self._box.remove(key1)
        self.assertNotIn(key1, self._box)
        self.assertNotIn(key0, self._box)
        self.assertNotIn('foo', self._box)

    def test_len(self, repetitions=10):
        keys = []
        for i in range(repetitions):
            self.assertEqual(len(self._box), i)
            keys.append(self._box.add(self._template % i))
            self.assertEqual(len(self._box), i + 1)
        for i in range(repetitions):
            self.assertEqual(len(self._box), repetitions - i)
            self._box.remove(keys[i])
            self.assertEqual(len(self._box), repetitions - i - 1)

    def test_set_item(self):
        key0 = self._box.add(self._template % 'original 0')
        self.assertEqual(self._box.get_string(key0), self._template %
            'original 0')
        key1 = self._box.add(self._template % 'original 1')
        self.assertEqual(self._box.get_string(key1), self._template %
            'original 1')
        self._box[key0] = self._template % 'changed 0'
        self.assertEqual(self._box.get_string(key0), self._template %
            'changed 0')
        self._box[key1] = self._template % 'changed 1'
        self.assertEqual(self._box.get_string(key1), self._template %
            'changed 1')
        self._box[key0] = _sample_message
        self._check_sample(self._box[key0])
        self._box[key1] = self._box[key0]
        self._check_sample(self._box[key1])
        self._box[key0] = self._template % 'original 0'
        self.assertEqual(self._box.get_string(key0), self._template %
            'original 0')
        self._check_sample(self._box[key1])
        self.assertRaises(KeyError, lambda : self._box.__setitem__('foo',
            'bar'))
        self.assertRaises(KeyError, lambda : self._box['foo'])
        self.assertEqual(len(self._box), 2)

    def test_clear(self, iterations=10):
        keys = []
        for i in range(iterations):
            self._box.add(self._template % i)
        for i, key in enumerate(keys):
            self.assertEqual(self._box.get_string(key), self._template % i)
        self._box.clear()
        self.assertEqual(len(self._box), 0)
        for i, key in enumerate(keys):
            self.assertRaises(KeyError, lambda : self._box.get_string(key))

    def test_pop(self):
        key0 = self._box.add(self._template % 0)
        self.assertIn(key0, self._box)
        key1 = self._box.add(self._template % 1)
        self.assertIn(key1, self._box)
        self.assertEqual(self._box.pop(key0).get_payload(), '0\n')
        self.assertNotIn(key0, self._box)
        self.assertIn(key1, self._box)
        key2 = self._box.add(self._template % 2)
        self.assertIn(key2, self._box)
        self.assertEqual(self._box.pop(key2).get_payload(), '2\n')
        self.assertNotIn(key2, self._box)
        self.assertIn(key1, self._box)
        self.assertEqual(self._box.pop(key1).get_payload(), '1\n')
        self.assertNotIn(key1, self._box)
        self.assertEqual(len(self._box), 0)

    def test_popitem(self, iterations=10):
        keys = []
        for i in range(10):
            keys.append(self._box.add(self._template % i))
        seen = []
        for i in range(10):
            key, msg = self._box.popitem()
            self.assertIn(key, keys)
            self.assertNotIn(key, seen)
            seen.append(key)
            self.assertEqual(int(msg.get_payload()), keys.index(key))
        self.assertEqual(len(self._box), 0)
        for key in keys:
            self.assertRaises(KeyError, lambda : self._box[key])

    def test_update(self):
        key0 = self._box.add(self._template % 'original 0')
        key1 = self._box.add(self._template % 'original 1')
        key2 = self._box.add(self._template % 'original 2')
        self._box.update({key0: self._template % 'changed 0', key2:
            _sample_message})
        self.assertEqual(len(self._box), 3)
        self.assertEqual(self._box.get_string(key0), self._template %
            'changed 0')
        self.assertEqual(self._box.get_string(key1), self._template %
            'original 1')
        self._check_sample(self._box[key2])
        self._box.update([(key2, self._template % 'changed 2'), (key1, self
            ._template % 'changed 1'), (key0, self._template % 'original 0')])
        self.assertEqual(len(self._box), 3)
        self.assertEqual(self._box.get_string(key0), self._template %
            'original 0')
        self.assertEqual(self._box.get_string(key1), self._template %
            'changed 1')
        self.assertEqual(self._box.get_string(key2), self._template %
            'changed 2')
        self.assertRaises(KeyError, lambda : self._box.update({'foo': 'bar',
            key0: self._template % 'changed 0'}))
        self.assertEqual(len(self._box), 3)
        self.assertEqual(self._box.get_string(key0), self._template %
            'changed 0')
        self.assertEqual(self._box.get_string(key1), self._template %
            'changed 1')
        self.assertEqual(self._box.get_string(key2), self._template %
            'changed 2')

    def test_flush(self):
        self._test_flush_or_close(self._box.flush, True)

    def test_popitem_and_flush_twice(self):
        self._box.add(self._template % 0)
        self._box.add(self._template % 1)
        self._box.flush()
        self._box.popitem()
        self._box.flush()
        self._box.popitem()
        self._box.flush()

    def test_lock_unlock(self):
        self.assertFalse(os.path.exists(self._get_lock_path()))
        self._box.lock()
        self.assertTrue(os.path.exists(self._get_lock_path()))
        self._box.unlock()
        self.assertFalse(os.path.exists(self._get_lock_path()))

    def test_close(self):
        self._test_flush_or_close(self._box.close, False)

    def _test_flush_or_close(self, method, should_call_close):
        contents = [(self._template % i) for i in range(3)]
        self._box.add(contents[0])
        self._box.add(contents[1])
        self._box.add(contents[2])
        oldbox = self._box
        method()
        if should_call_close:
            self._box.close()
        self._box = self._factory(self._path)
        keys = self._box.keys()
        self.assertEqual(len(keys), 3)
        for key in keys:
            self.assertIn(self._box.get_string(key), contents)
        oldbox.close()

    def test_dump_message(self):
        for input in (email.message_from_string(_sample_message),
            _sample_message, io.BytesIO(_bytes_sample_message)):
            output = io.BytesIO()
            self._box._dump_message(input, output)
            self.assertEqual(output.getvalue(), _bytes_sample_message.
                replace(b'\n', os.linesep.encode()))
        output = io.BytesIO()
        self.assertRaises(TypeError, lambda : self._box._dump_message(None,
            output))

    def _get_lock_path(self):
        return self._path + '.lock'


class TestMailboxSuperclass(TestBase, unittest.TestCase):

    def test_notimplemented(self):
        box = mailbox.Mailbox('path')
        self.assertRaises(NotImplementedError, lambda : box.add(''))
        self.assertRaises(NotImplementedError, lambda : box.remove(''))
        self.assertRaises(NotImplementedError, lambda : box.__delitem__(''))
        self.assertRaises(NotImplementedError, lambda : box.discard(''))
        self.assertRaises(NotImplementedError, lambda : box.__setitem__('', '')
            )
        self.assertRaises(NotImplementedError, lambda : box.iterkeys())
        self.assertRaises(NotImplementedError, lambda : box.keys())
        self.assertRaises(NotImplementedError, lambda : box.itervalues().
            __next__())
        self.assertRaises(NotImplementedError, lambda : box.__iter__().
            __next__())
        self.assertRaises(NotImplementedError, lambda : box.values())
        self.assertRaises(NotImplementedError, lambda : box.iteritems().
            __next__())
        self.assertRaises(NotImplementedError, lambda : box.items())
        self.assertRaises(NotImplementedError, lambda : box.get(''))
        self.assertRaises(NotImplementedError, lambda : box.__getitem__(''))
        self.assertRaises(NotImplementedError, lambda : box.get_message(''))
        self.assertRaises(NotImplementedError, lambda : box.get_string(''))
        self.assertRaises(NotImplementedError, lambda : box.get_bytes(''))
        self.assertRaises(NotImplementedError, lambda : box.get_file(''))
        self.assertRaises(NotImplementedError, lambda : '' in box)
        self.assertRaises(NotImplementedError, lambda : box.__contains__(''))
        self.assertRaises(NotImplementedError, lambda : box.__len__())
        self.assertRaises(NotImplementedError, lambda : box.clear())
        self.assertRaises(NotImplementedError, lambda : box.pop(''))
        self.assertRaises(NotImplementedError, lambda : box.popitem())
        self.assertRaises(NotImplementedError, lambda : box.update((('', ''),))
            )
        self.assertRaises(NotImplementedError, lambda : box.flush())
        self.assertRaises(NotImplementedError, lambda : box.lock())
        self.assertRaises(NotImplementedError, lambda : box.unlock())
        self.assertRaises(NotImplementedError, lambda : box.close())


class TestMaildir(TestMailbox, unittest.TestCase):
    _factory = lambda self, path, factory=None: mailbox.Maildir(path, factory)

    def setUp(self):
        TestMailbox.setUp(self)
        if os.name == 'nt' or sys.platform == 'cygwin':
            self._box.colon = '!'

    def assertMailboxEmpty(self):
        self.assertEqual(os.listdir(os.path.join(self._path, 'tmp')), [])

    def test_add_MM(self):
        msg = mailbox.MaildirMessage(self._template % 0)
        msg.set_subdir('cur')
        msg.set_info('foo')
        key = self._box.add(msg)
        self.assertTrue(os.path.exists(os.path.join(self._path, 'cur', 
            '%s%sfoo' % (key, self._box.colon))))

    def test_get_MM(self):
        msg = mailbox.MaildirMessage(self._template % 0)
        msg.set_subdir('cur')
        msg.set_flags('RF')
        key = self._box.add(msg)
        msg_returned = self._box.get_message(key)
        self.assertIsInstance(msg_returned, mailbox.MaildirMessage)
        self.assertEqual(msg_returned.get_subdir(), 'cur')
        self.assertEqual(msg_returned.get_flags(), 'FR')

    def test_set_MM(self):
        msg0 = mailbox.MaildirMessage(self._template % 0)
        msg0.set_flags('TP')
        key = self._box.add(msg0)
        msg_returned = self._box.get_message(key)
        self.assertEqual(msg_returned.get_subdir(), 'new')
        self.assertEqual(msg_returned.get_flags(), 'PT')
        msg1 = mailbox.MaildirMessage(self._template % 1)
        self._box[key] = msg1
        msg_returned = self._box.get_message(key)
        self.assertEqual(msg_returned.get_subdir(), 'new')
        self.assertEqual(msg_returned.get_flags(), '')
        self.assertEqual(msg_returned.get_payload(), '1\n')
        msg2 = mailbox.MaildirMessage(self._template % 2)
        msg2.set_info('2,S')
        self._box[key] = msg2
        self._box[key] = self._template % 3
        msg_returned = self._box.get_message(key)
        self.assertEqual(msg_returned.get_subdir(), 'new')
        self.assertEqual(msg_returned.get_flags(), 'S')
        self.assertEqual(msg_returned.get_payload(), '3\n')

    def test_consistent_factory(self):
        msg = mailbox.MaildirMessage(self._template % 0)
        msg.set_subdir('cur')
        msg.set_flags('RF')
        key = self._box.add(msg)


        class FakeMessage(mailbox.MaildirMessage):
            pass
        box = mailbox.Maildir(self._path, factory=FakeMessage)
        box.colon = self._box.colon
        msg2 = box.get_message(key)
        self.assertIsInstance(msg2, FakeMessage)

    def test_initialize_new(self):
        self.tearDown()
        self._box = mailbox.Maildir(self._path)
        self._check_basics()
        self._delete_recursively(self._path)
        self._box = self._factory(self._path, factory=None)
        self._check_basics()

    def test_initialize_existing(self):
        self.tearDown()
        for subdir in ('', 'tmp', 'new', 'cur'):
            os.mkdir(os.path.normpath(os.path.join(self._path, subdir)))
        self._box = mailbox.Maildir(self._path)
        self._check_basics()

    def _check_basics(self, factory=None):
        self.assertEqual(self._box._path, os.path.abspath(self._path))
        self.assertEqual(self._box._factory, factory)
        for subdir in ('', 'tmp', 'new', 'cur'):
            path = os.path.join(self._path, subdir)
            mode = os.stat(path)[stat.ST_MODE]
            self.assertTrue(stat.S_ISDIR(mode), "Not a directory: '%s'" % path)

    def test_list_folders(self):
        self._box.add_folder('one')
        self._box.add_folder('two')
        self._box.add_folder('three')
        self.assertEqual(len(self._box.list_folders()), 3)
        self.assertEqual(set(self._box.list_folders()), set(('one', 'two',
            'three')))

    def test_get_folder(self):
        self._box.add_folder('foo.bar')
        folder0 = self._box.get_folder('foo.bar')
        folder0.add(self._template % 'bar')
        self.assertTrue(os.path.isdir(os.path.join(self._path, '.foo.bar')))
        folder1 = self._box.get_folder('foo.bar')
        self.assertEqual(folder1.get_string(folder1.keys()[0]), self.
            _template % 'bar')

    def test_add_and_remove_folders(self):
        self._box.add_folder('one')
        self._box.add_folder('two')
        self.assertEqual(len(self._box.list_folders()), 2)
        self.assertEqual(set(self._box.list_folders()), set(('one', 'two')))
        self._box.remove_folder('one')
        self.assertEqual(len(self._box.list_folders()), 1)
        self.assertEqual(set(self._box.list_folders()), set(('two',)))
        self._box.add_folder('three')
        self.assertEqual(len(self._box.list_folders()), 2)
        self.assertEqual(set(self._box.list_folders()), set(('two', 'three')))
        self._box.remove_folder('three')
        self.assertEqual(len(self._box.list_folders()), 1)
        self.assertEqual(set(self._box.list_folders()), set(('two',)))
        self._box.remove_folder('two')
        self.assertEqual(len(self._box.list_folders()), 0)
        self.assertEqual(self._box.list_folders(), [])

    def test_clean(self):
        foo_path = os.path.join(self._path, 'tmp', 'foo')
        bar_path = os.path.join(self._path, 'tmp', 'bar')
        with open(foo_path, 'w') as f:
            f.write('@')
        with open(bar_path, 'w') as f:
            f.write('@')
        self._box.clean()
        self.assertTrue(os.path.exists(foo_path))
        self.assertTrue(os.path.exists(bar_path))
        foo_stat = os.stat(foo_path)
        os.utime(foo_path, (time.time() - 129600 - 2, foo_stat.st_mtime))
        self._box.clean()
        self.assertFalse(os.path.exists(foo_path))
        self.assertTrue(os.path.exists(bar_path))

    def test_create_tmp(self, repetitions=10):
        hostname = socket.gethostname()
        if '/' in hostname:
            hostname = hostname.replace('/', '\\057')
        if ':' in hostname:
            hostname = hostname.replace(':', '\\072')
        pid = os.getpid()
        pattern = re.compile(
            '(?P<time>\\d+)\\.M(?P<M>\\d{1,6})P(?P<P>\\d+)Q(?P<Q>\\d+)\\.(?P<host>[^:/]+)'
            )
        previous_groups = None
        for x in range(repetitions):
            tmp_file = self._box._create_tmp()
            head, tail = os.path.split(tmp_file.name)
            self.assertEqual(head, os.path.abspath(os.path.join(self._path,
                'tmp')), "File in wrong location: '%s'" % head)
            match = pattern.match(tail)
            self.assertIsNotNone(match, "Invalid file name: '%s'" % tail)
            groups = match.groups()
            if previous_groups is not None:
                self.assertGreaterEqual(int(groups[0]), int(previous_groups
                    [0]), "Non-monotonic seconds: '%s' before '%s'" % (
                    previous_groups[0], groups[0]))
                if int(groups[0]) == int(previous_groups[0]):
                    self.assertGreaterEqual(int(groups[1]), int(
                        previous_groups[1]), 
                        "Non-monotonic milliseconds: '%s' before '%s'" % (
                        previous_groups[1], groups[1]))
                self.assertEqual(int(groups[2]), pid, 
                    "Process ID mismatch: '%s' should be '%s'" % (groups[2],
                    pid))
                self.assertEqual(int(groups[3]), int(previous_groups[3]) + 
                    1, "Non-sequential counter: '%s' before '%s'" % (
                    previous_groups[3], groups[3]))
                self.assertEqual(groups[4], hostname, 
                    "Host name mismatch: '%s' should be '%s'" % (groups[4],
                    hostname))
            previous_groups = groups
            tmp_file.write(_bytes_sample_message)
            tmp_file.seek(0)
            self.assertEqual(tmp_file.read(), _bytes_sample_message)
            tmp_file.close()
        file_count = len(os.listdir(os.path.join(self._path, 'tmp')))
        self.assertEqual(file_count, repetitions, 
            "Wrong file count: '%s' should be '%s'" % (file_count, repetitions)
            )

    def test_refresh(self):
        self.assertEqual(self._box._toc, {})
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(self._template % 1)
        self.assertEqual(self._box._toc, {})
        self._box._refresh()
        self.assertEqual(self._box._toc, {key0: os.path.join('new', key0),
            key1: os.path.join('new', key1)})
        key2 = self._box.add(self._template % 2)
        self.assertEqual(self._box._toc, {key0: os.path.join('new', key0),
            key1: os.path.join('new', key1)})
        self._box._refresh()
        self.assertEqual(self._box._toc, {key0: os.path.join('new', key0),
            key1: os.path.join('new', key1), key2: os.path.join('new', key2)})

    def test_refresh_after_safety_period(self):
        key0 = self._box.add(self._template % 0)
        key1 = self._box.add(self._template % 1)
        self._box = self._factory(self._path)
        self.assertEqual(self._box._toc, {})
        self._box._skewfactor = -3
        self._box._refresh()
        self.assertEqual(sorted(self._box._toc.keys()), sorted([key0, key1]))

    def test_lookup(self):
        self.assertRaises(KeyError, lambda : self._box._lookup('foo'))
        key0 = self._box.add(self._template % 0)
        self.assertEqual(self._box._lookup(key0), os.path.join('new', key0))
        os.remove(os.path.join(self._path, 'new', key0))
        self.assertEqual(self._box._toc, {key0: os.path.join('new', key0)})
        self._box.flush()
        self.assertRaises(KeyError, lambda : self._box._lookup(key0))
        self.assertEqual(self._box._toc, {})

    def test_lock_unlock(self):
        self._box.lock()
        self._box.unlock()

    def test_folder(self):

        def dummy_factory(s):
            return None
        box = self._factory(self._path, factory=dummy_factory)
        folder = box.add_folder('folder1')
        self.assertIs(folder._factory, dummy_factory)
        folder1_alias = box.get_folder('folder1')
        self.assertIs(folder1_alias._factory, dummy_factory)

    def test_directory_in_folder(self):
        for i in range(10):
            self._box.add(mailbox.Message(_sample_message))
        os.mkdir(os.path.join(self._path, 'cur', 'stray-dir'))
        for msg in self._box:
            pass

    @unittest.skipUnless(hasattr(os, 'umask'), 'test needs os.umask()')
    @unittest.skipUnless(hasattr(os, 'stat'), 'test needs os.stat()')
    def test_file_permissions(self):
        msg = mailbox.MaildirMessage(self._template % 0)
        orig_umask = os.umask(0)
        try:
            key = self._box.add(msg)
        finally:
            os.umask(orig_umask)
        path = os.path.join(self._path, self._box._lookup(key))
        mode = os.stat(path).st_mode
        self.assertFalse(mode & 73)

    @unittest.skipUnless(hasattr(os, 'umask'), 'test needs os.umask()')
    @unittest.skipUnless(hasattr(os, 'stat'), 'test needs os.stat()')
    def test_folder_file_perms(self):
        orig_umask = os.umask(0)
        try:
            subfolder = self._box.add_folder('subfolder')
        finally:
            os.umask(orig_umask)
        path = os.path.join(subfolder._path, 'maildirfolder')
        st = os.stat(path)
        perms = st.st_mode
        self.assertFalse(perms & 73)

    def test_reread(self):
        self._box._refresh()
        for subdir in ('cur', 'new'):
            os.utime(os.path.join(self._box._path, subdir), (time.time() - 
                5,) * 2)
        self._box._skewfactor = -3
        orig_toc = self._box._toc

        def refreshed():
            return self._box._toc is not orig_toc
        self._box._refresh()
        self.assertFalse(refreshed())
        filename = os.path.join(self._path, 'cur', 'stray-file')
        support.create_empty_file(filename)
        os.unlink(filename)
        self._box._refresh()
        self.assertTrue(refreshed())


class _TestSingleFile(TestMailbox):
    """Common tests for single-file mailboxes"""

    def test_add_doesnt_rewrite(self):
        inode_before = os.stat(self._path).st_ino
        self._box.add(self._template % 0)
        self._box.flush()
        inode_after = os.stat(self._path).st_ino
        self.assertEqual(inode_before, inode_after)
        self._box.close()
        self._box = self._factory(self._path)
        self.assertEqual(len(self._box), 1)

    def test_permissions_after_flush(self):
        mode = os.stat(self._path).st_mode | 438
        os.chmod(self._path, mode)
        self._box.add(self._template % 0)
        i = self._box.add(self._template % 1)
        self._box.remove(i)
        self._box.flush()
        self.assertEqual(os.stat(self._path).st_mode, mode)


class _TestMboxMMDF(_TestSingleFile):

    def tearDown(self):
        super().tearDown()
        self._box.close()
        self._delete_recursively(self._path)
        for lock_remnant in glob.glob(self._path + '.*'):
            support.unlink(lock_remnant)

    def assertMailboxEmpty(self):
        with open(self._path) as f:
            self.assertEqual(f.readlines(), [])

    def test_add_from_string(self):
        key = self._box.add('From foo@bar blah\nFrom: foo\n\n0\n')
        self.assertEqual(self._box[key].get_from(), 'foo@bar blah')
        self.assertEqual(self._box[key].get_payload(), '0\n')

    def test_add_from_bytes(self):
        key = self._box.add(b'From foo@bar blah\nFrom: foo\n\n0\n')
        self.assertEqual(self._box[key].get_from(), 'foo@bar blah')
        self.assertEqual(self._box[key].get_payload(), '0\n')

    def test_add_mbox_or_mmdf_message(self):
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg = class_('From foo@bar blah\nFrom: foo\n\n0\n')
            key = self._box.add(msg)

    def test_open_close_open(self):
        values = [(self._template % i) for i in range(3)]
        for value in values:
            self._box.add(value)
        self._box.close()
        mtime = os.path.getmtime(self._path)
        self._box = self._factory(self._path)
        self.assertEqual(len(self._box), 3)
        for key in self._box.iterkeys():
            self.assertIn(self._box.get_string(key), values)
        self._box.close()
        self.assertEqual(mtime, os.path.getmtime(self._path))

    def test_add_and_close(self):
        self._box.add(_sample_message)
        for i in range(3):
            self._box.add(self._template % i)
        self._box.add(_sample_message)
        self._box._file.flush()
        self._box._file.seek(0)
        contents = self._box._file.read()
        self._box.close()
        with open(self._path, 'rb') as f:
            self.assertEqual(contents, f.read())
        self._box = self._factory(self._path)

    @unittest.skipUnless(hasattr(os, 'fork'), 'Test needs fork().')
    @unittest.skipUnless(hasattr(socket, 'socketpair'),
        'Test needs socketpair().')
    def test_lock_conflict(self):
        c, p = socket.socketpair()
        self.addCleanup(c.close)
        self.addCleanup(p.close)
        pid = os.fork()
        if pid == 0:
            try:
                self._box.lock()
                c.send(b'c')
                c.recv(1)
                self._box.unlock()
            finally:
                os._exit(0)
        p.recv(1)
        try:
            self.assertRaises(mailbox.ExternalClashError, self._box.lock)
        finally:
            p.send(b'p')
            exited_pid, status = os.waitpid(pid, 0)
        self._box.lock()
        self._box.unlock()

    def test_relock(self):
        msg = 'Subject: sub\n\nbody\n'
        key1 = self._box.add(msg)
        self._box.flush()
        self._box.close()
        self._box = self._factory(self._path)
        self._box.lock()
        key2 = self._box.add(msg)
        self._box.flush()
        self.assertTrue(self._box._locked)
        self._box.close()


class TestMbox(_TestMboxMMDF, unittest.TestCase):
    _factory = lambda self, path, factory=None: mailbox.mbox(path, factory)

    @unittest.skipUnless(hasattr(os, 'umask'), 'test needs os.umask()')
    @unittest.skipUnless(hasattr(os, 'stat'), 'test needs os.stat()')
    def test_file_perms(self):
        try:
            old_umask = os.umask(63)
            self._box.close()
            os.unlink(self._path)
            self._box = mailbox.mbox(self._path, create=True)
            self._box.add('')
            self._box.close()
        finally:
            os.umask(old_umask)
        st = os.stat(self._path)
        perms = st.st_mode
        self.assertFalse(perms & 73)

    def test_terminating_newline(self):
        message = email.message.Message()
        message['From'] = 'john@example.com'
        message.set_payload('No newline at the end')
        i = self._box.add(message)
        message = self._box.get(i)
        self.assertEqual(message.get_payload(), 'No newline at the end\n')

    def test_message_separator(self):
        self._box.add('From: foo\n\n0')
        with open(self._path) as f:
            data = f.read()
            self.assertEqual(data[-3:], '0\n\n')
        self._box.add('From: foo\n\n0\n')
        with open(self._path) as f:
            data = f.read()
            self.assertEqual(data[-3:], '0\n\n')


class TestMMDF(_TestMboxMMDF, unittest.TestCase):
    _factory = lambda self, path, factory=None: mailbox.MMDF(path, factory)


class TestMH(TestMailbox, unittest.TestCase):
    _factory = lambda self, path, factory=None: mailbox.MH(path, factory)

    def assertMailboxEmpty(self):
        self.assertEqual(os.listdir(self._path), ['.mh_sequences'])

    def test_list_folders(self):
        self._box.add_folder('one')
        self._box.add_folder('two')
        self._box.add_folder('three')
        self.assertEqual(len(self._box.list_folders()), 3)
        self.assertEqual(set(self._box.list_folders()), set(('one', 'two',
            'three')))

    def test_get_folder(self):

        def dummy_factory(s):
            return None
        self._box = self._factory(self._path, dummy_factory)
        new_folder = self._box.add_folder('foo.bar')
        folder0 = self._box.get_folder('foo.bar')
        folder0.add(self._template % 'bar')
        self.assertTrue(os.path.isdir(os.path.join(self._path, 'foo.bar')))
        folder1 = self._box.get_folder('foo.bar')
        self.assertEqual(folder1.get_string(folder1.keys()[0]), self.
            _template % 'bar')
        self.assertIs(new_folder._factory, self._box._factory)
        self.assertIs(folder0._factory, self._box._factory)

    def test_add_and_remove_folders(self):
        self._box.add_folder('one')
        self._box.add_folder('two')
        self.assertEqual(len(self._box.list_folders()), 2)
        self.assertEqual(set(self._box.list_folders()), set(('one', 'two')))
        self._box.remove_folder('one')
        self.assertEqual(len(self._box.list_folders()), 1)
        self.assertEqual(set(self._box.list_folders()), set(('two',)))
        self._box.add_folder('three')
        self.assertEqual(len(self._box.list_folders()), 2)
        self.assertEqual(set(self._box.list_folders()), set(('two', 'three')))
        self._box.remove_folder('three')
        self.assertEqual(len(self._box.list_folders()), 1)
        self.assertEqual(set(self._box.list_folders()), set(('two',)))
        self._box.remove_folder('two')
        self.assertEqual(len(self._box.list_folders()), 0)
        self.assertEqual(self._box.list_folders(), [])

    def test_sequences(self):
        self.assertEqual(self._box.get_sequences(), {})
        msg0 = mailbox.MHMessage(self._template % 0)
        msg0.add_sequence('foo')
        key0 = self._box.add(msg0)
        self.assertEqual(self._box.get_sequences(), {'foo': [key0]})
        msg1 = mailbox.MHMessage(self._template % 1)
        msg1.set_sequences(['bar', 'replied', 'foo'])
        key1 = self._box.add(msg1)
        self.assertEqual(self._box.get_sequences(), {'foo': [key0, key1],
            'bar': [key1], 'replied': [key1]})
        msg0.set_sequences(['flagged'])
        self._box[key0] = msg0
        self.assertEqual(self._box.get_sequences(), {'foo': [key1], 'bar':
            [key1], 'replied': [key1], 'flagged': [key0]})
        self._box.remove(key1)
        self.assertEqual(self._box.get_sequences(), {'flagged': [key0]})

    def test_issue2625(self):
        msg0 = mailbox.MHMessage(self._template % 0)
        msg0.add_sequence('foo')
        key0 = self._box.add(msg0)
        refmsg0 = self._box.get_message(key0)

    def test_issue7627(self):
        msg0 = mailbox.MHMessage(self._template % 0)
        key0 = self._box.add(msg0)
        self._box.lock()
        self._box.remove(key0)
        self._box.unlock()

    def test_pack(self):
        msg0 = mailbox.MHMessage(self._template % 0)
        msg1 = mailbox.MHMessage(self._template % 1)
        msg2 = mailbox.MHMessage(self._template % 2)
        msg3 = mailbox.MHMessage(self._template % 3)
        msg0.set_sequences(['foo', 'unseen'])
        msg1.set_sequences(['foo'])
        msg2.set_sequences(['foo', 'flagged'])
        msg3.set_sequences(['foo', 'bar', 'replied'])
        key0 = self._box.add(msg0)
        key1 = self._box.add(msg1)
        key2 = self._box.add(msg2)
        key3 = self._box.add(msg3)
        self.assertEqual(self._box.get_sequences(), {'foo': [key0, key1,
            key2, key3], 'unseen': [key0], 'flagged': [key2], 'bar': [key3],
            'replied': [key3]})
        self._box.remove(key2)
        self.assertEqual(self._box.get_sequences(), {'foo': [key0, key1,
            key3], 'unseen': [key0], 'bar': [key3], 'replied': [key3]})
        self._box.pack()
        self.assertEqual(self._box.keys(), [1, 2, 3])
        key0 = key0
        key1 = key0 + 1
        key2 = key1 + 1
        self.assertEqual(self._box.get_sequences(), {'foo': [1, 2, 3],
            'unseen': [1], 'bar': [3], 'replied': [3]})
        key0 = self._box.add(msg1)
        key1 = self._box.add(msg1)
        key2 = self._box.add(msg1)
        key3 = self._box.add(msg1)
        self._box.remove(key0)
        self._box.remove(key2)
        self._box.lock()
        self._box.pack()
        self._box.unlock()
        self.assertEqual(self._box.get_sequences(), {'foo': [1, 2, 3, 4, 5],
            'unseen': [1], 'bar': [3], 'replied': [3]})

    def _get_lock_path(self):
        return os.path.join(self._path, '.mh_sequences.lock')


class TestBabyl(_TestSingleFile, unittest.TestCase):
    _factory = lambda self, path, factory=None: mailbox.Babyl(path, factory)

    def assertMailboxEmpty(self):
        with open(self._path) as f:
            self.assertEqual(f.readlines(), [])

    def tearDown(self):
        super().tearDown()
        self._box.close()
        self._delete_recursively(self._path)
        for lock_remnant in glob.glob(self._path + '.*'):
            support.unlink(lock_remnant)

    def test_labels(self):
        self.assertEqual(self._box.get_labels(), [])
        msg0 = mailbox.BabylMessage(self._template % 0)
        msg0.add_label('foo')
        key0 = self._box.add(msg0)
        self.assertEqual(self._box.get_labels(), ['foo'])
        msg1 = mailbox.BabylMessage(self._template % 1)
        msg1.set_labels(['bar', 'answered', 'foo'])
        key1 = self._box.add(msg1)
        self.assertEqual(set(self._box.get_labels()), set(['foo', 'bar']))
        msg0.set_labels(['blah', 'filed'])
        self._box[key0] = msg0
        self.assertEqual(set(self._box.get_labels()), set(['foo', 'bar',
            'blah']))
        self._box.remove(key1)
        self.assertEqual(set(self._box.get_labels()), set(['blah']))


class FakeFileLikeObject:

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeMailBox(mailbox.Mailbox):

    def __init__(self):
        mailbox.Mailbox.__init__(self, '', lambda file: None)
        self.files = [FakeFileLikeObject() for i in range(10)]

    def get_file(self, key):
        return self.files[key]


class TestFakeMailBox(unittest.TestCase):

    def test_closing_fd(self):
        box = FakeMailBox()
        for i in range(10):
            self.assertFalse(box.files[i].closed)
        for i in range(10):
            box[i]
        for i in range(10):
            self.assertTrue(box.files[i].closed)


class TestMessage(TestBase, unittest.TestCase):
    _factory = mailbox.Message

    def setUp(self):
        self._path = support.TESTFN

    def tearDown(self):
        self._delete_recursively(self._path)

    def test_initialize_with_eMM(self):
        eMM = email.message_from_string(_sample_message)
        msg = self._factory(eMM)
        self._post_initialize_hook(msg)
        self._check_sample(msg)

    def test_initialize_with_string(self):
        msg = self._factory(_sample_message)
        self._post_initialize_hook(msg)
        self._check_sample(msg)

    def test_initialize_with_file(self):
        with open(self._path, 'w+') as f:
            f.write(_sample_message)
            f.seek(0)
            msg = self._factory(f)
            self._post_initialize_hook(msg)
            self._check_sample(msg)

    def test_initialize_with_binary_file(self):
        with open(self._path, 'wb+') as f:
            f.write(_bytes_sample_message)
            f.seek(0)
            msg = self._factory(f)
            self._post_initialize_hook(msg)
            self._check_sample(msg)

    def test_initialize_with_nothing(self):
        msg = self._factory()
        self._post_initialize_hook(msg)
        self.assertIsInstance(msg, email.message.Message)
        self.assertIsInstance(msg, mailbox.Message)
        self.assertIsInstance(msg, self._factory)
        self.assertEqual(msg.keys(), [])
        self.assertFalse(msg.is_multipart())
        self.assertIsNone(msg.get_payload())

    def test_initialize_incorrectly(self):
        self.assertRaises(TypeError, lambda : self._factory(object()))

    def test_all_eMM_attribues_exist(self):
        eMM = email.message_from_string(_sample_message)
        msg = self._factory(_sample_message)
        for attr in eMM.__dict__:
            self.assertIn(attr, msg.__dict__, '{} attribute does not exist'
                .format(attr))

    def test_become_message(self):
        eMM = email.message_from_string(_sample_message)
        msg = self._factory()
        msg._become_message(eMM)
        self._check_sample(msg)

    def test_explain_to(self):
        msg = self._factory()
        for class_ in self.all_mailbox_types:
            other_msg = class_()
            msg._explain_to(other_msg)
        other_msg = email.message.Message()
        self.assertRaises(TypeError, lambda : msg._explain_to(other_msg))

    def _post_initialize_hook(self, msg):
        pass


class TestMaildirMessage(TestMessage, unittest.TestCase):
    _factory = mailbox.MaildirMessage

    def _post_initialize_hook(self, msg):
        self.assertEqual(msg._subdir, 'new')
        self.assertEqual(msg._info, '')

    def test_subdir(self):
        msg = mailbox.MaildirMessage(_sample_message)
        self.assertEqual(msg.get_subdir(), 'new')
        msg.set_subdir('cur')
        self.assertEqual(msg.get_subdir(), 'cur')
        msg.set_subdir('new')
        self.assertEqual(msg.get_subdir(), 'new')
        self.assertRaises(ValueError, lambda : msg.set_subdir('tmp'))
        self.assertEqual(msg.get_subdir(), 'new')
        msg.set_subdir('new')
        self.assertEqual(msg.get_subdir(), 'new')
        self._check_sample(msg)

    def test_flags(self):
        msg = mailbox.MaildirMessage(_sample_message)
        self.assertEqual(msg.get_flags(), '')
        self.assertEqual(msg.get_subdir(), 'new')
        msg.set_flags('F')
        self.assertEqual(msg.get_subdir(), 'new')
        self.assertEqual(msg.get_flags(), 'F')
        msg.set_flags('SDTP')
        self.assertEqual(msg.get_flags(), 'DPST')
        msg.add_flag('FT')
        self.assertEqual(msg.get_flags(), 'DFPST')
        msg.remove_flag('TDRP')
        self.assertEqual(msg.get_flags(), 'FS')
        self.assertEqual(msg.get_subdir(), 'new')
        self._check_sample(msg)

    def test_date(self):
        msg = mailbox.MaildirMessage(_sample_message)
        self.assertLess(abs(msg.get_date() - time.time()), 60)
        msg.set_date(0.0)
        self.assertEqual(msg.get_date(), 0.0)

    def test_info(self):
        msg = mailbox.MaildirMessage(_sample_message)
        self.assertEqual(msg.get_info(), '')
        msg.set_info('1,foo=bar')
        self.assertEqual(msg.get_info(), '1,foo=bar')
        self.assertRaises(TypeError, lambda : msg.set_info(None))
        self._check_sample(msg)

    def test_info_and_flags(self):
        msg = mailbox.MaildirMessage(_sample_message)
        self.assertEqual(msg.get_info(), '')
        msg.set_flags('SF')
        self.assertEqual(msg.get_flags(), 'FS')
        self.assertEqual(msg.get_info(), '2,FS')
        msg.set_info('1,')
        self.assertEqual(msg.get_flags(), '')
        self.assertEqual(msg.get_info(), '1,')
        msg.remove_flag('RPT')
        self.assertEqual(msg.get_flags(), '')
        self.assertEqual(msg.get_info(), '1,')
        msg.add_flag('D')
        self.assertEqual(msg.get_flags(), 'D')
        self.assertEqual(msg.get_info(), '2,D')
        self._check_sample(msg)


class _TestMboxMMDFMessage:
    _factory = mailbox._mboxMMDFMessage

    def _post_initialize_hook(self, msg):
        self._check_from(msg)

    def test_initialize_with_unixfrom(self):
        msg = mailbox.Message(_sample_message)
        msg.set_unixfrom('From foo@bar blah')
        msg = mailbox.mboxMessage(msg)
        self.assertEqual(msg.get_from(), 'foo@bar blah', msg.get_from())

    def test_from(self):
        msg = mailbox.mboxMessage(_sample_message)
        self._check_from(msg)
        msg.set_from('foo bar')
        self.assertEqual(msg.get_from(), 'foo bar')
        msg.set_from('foo@bar', True)
        self._check_from(msg, 'foo@bar')
        msg.set_from('blah@temp', time.localtime())
        self._check_from(msg, 'blah@temp')

    def test_flags(self):
        msg = mailbox.mboxMessage(_sample_message)
        self.assertEqual(msg.get_flags(), '')
        msg.set_flags('F')
        self.assertEqual(msg.get_flags(), 'F')
        msg.set_flags('XODR')
        self.assertEqual(msg.get_flags(), 'RODX')
        msg.add_flag('FA')
        self.assertEqual(msg.get_flags(), 'RODFAX')
        msg.remove_flag('FDXA')
        self.assertEqual(msg.get_flags(), 'RO')
        self._check_sample(msg)

    def _check_from(self, msg, sender=None):
        if sender is None:
            sender = 'MAILER-DAEMON'
        self.assertIsNotNone(re.match(sender +
            ' \\w{3} \\w{3} [\\d ]\\d [\\d ]\\d:\\d{2}:\\d{2} \\d{4}', msg.
            get_from()))


class TestMboxMessage(_TestMboxMMDFMessage, TestMessage):
    _factory = mailbox.mboxMessage


class TestMHMessage(TestMessage, unittest.TestCase):
    _factory = mailbox.MHMessage

    def _post_initialize_hook(self, msg):
        self.assertEqual(msg._sequences, [])

    def test_sequences(self):
        msg = mailbox.MHMessage(_sample_message)
        self.assertEqual(msg.get_sequences(), [])
        msg.set_sequences(['foobar'])
        self.assertEqual(msg.get_sequences(), ['foobar'])
        msg.set_sequences([])
        self.assertEqual(msg.get_sequences(), [])
        msg.add_sequence('unseen')
        self.assertEqual(msg.get_sequences(), ['unseen'])
        msg.add_sequence('flagged')
        self.assertEqual(msg.get_sequences(), ['unseen', 'flagged'])
        msg.add_sequence('flagged')
        self.assertEqual(msg.get_sequences(), ['unseen', 'flagged'])
        msg.remove_sequence('unseen')
        self.assertEqual(msg.get_sequences(), ['flagged'])
        msg.add_sequence('foobar')
        self.assertEqual(msg.get_sequences(), ['flagged', 'foobar'])
        msg.remove_sequence('replied')
        self.assertEqual(msg.get_sequences(), ['flagged', 'foobar'])
        msg.set_sequences(['foobar', 'replied'])
        self.assertEqual(msg.get_sequences(), ['foobar', 'replied'])


class TestBabylMessage(TestMessage, unittest.TestCase):
    _factory = mailbox.BabylMessage

    def _post_initialize_hook(self, msg):
        self.assertEqual(msg._labels, [])

    def test_labels(self):
        msg = mailbox.BabylMessage(_sample_message)
        self.assertEqual(msg.get_labels(), [])
        msg.set_labels(['foobar'])
        self.assertEqual(msg.get_labels(), ['foobar'])
        msg.set_labels([])
        self.assertEqual(msg.get_labels(), [])
        msg.add_label('filed')
        self.assertEqual(msg.get_labels(), ['filed'])
        msg.add_label('resent')
        self.assertEqual(msg.get_labels(), ['filed', 'resent'])
        msg.add_label('resent')
        self.assertEqual(msg.get_labels(), ['filed', 'resent'])
        msg.remove_label('filed')
        self.assertEqual(msg.get_labels(), ['resent'])
        msg.add_label('foobar')
        self.assertEqual(msg.get_labels(), ['resent', 'foobar'])
        msg.remove_label('unseen')
        self.assertEqual(msg.get_labels(), ['resent', 'foobar'])
        msg.set_labels(['foobar', 'answered'])
        self.assertEqual(msg.get_labels(), ['foobar', 'answered'])

    def test_visible(self):
        msg = mailbox.BabylMessage(_sample_message)
        visible = msg.get_visible()
        self.assertEqual(visible.keys(), [])
        self.assertIsNone(visible.get_payload())
        visible['User-Agent'] = 'FooBar 1.0'
        visible['X-Whatever'] = 'Blah'
        self.assertEqual(msg.get_visible().keys(), [])
        msg.set_visible(visible)
        visible = msg.get_visible()
        self.assertEqual(visible.keys(), ['User-Agent', 'X-Whatever'])
        self.assertEqual(visible['User-Agent'], 'FooBar 1.0')
        self.assertEqual(visible['X-Whatever'], 'Blah')
        self.assertIsNone(visible.get_payload())
        msg.update_visible()
        self.assertEqual(visible.keys(), ['User-Agent', 'X-Whatever'])
        self.assertIsNone(visible.get_payload())
        visible = msg.get_visible()
        self.assertEqual(visible.keys(), ['User-Agent', 'Date', 'From',
            'To', 'Subject'])
        for header in ('User-Agent', 'Date', 'From', 'To', 'Subject'):
            self.assertEqual(visible[header], msg[header])


class TestMMDFMessage(_TestMboxMMDFMessage, TestMessage):
    _factory = mailbox.MMDFMessage


class TestMessageConversion(TestBase, unittest.TestCase):

    def test_plain_to_x(self):
        for class_ in self.all_mailbox_types:
            msg_plain = mailbox.Message(_sample_message)
            msg = class_(msg_plain)
            self._check_sample(msg)

    def test_x_to_plain(self):
        for class_ in self.all_mailbox_types:
            msg = class_(_sample_message)
            msg_plain = mailbox.Message(msg)
            self._check_sample(msg_plain)

    def test_x_from_bytes(self):
        for class_ in self.all_mailbox_types:
            msg = class_(_bytes_sample_message)
            self._check_sample(msg)

    def test_x_to_invalid(self):
        for class_ in self.all_mailbox_types:
            self.assertRaises(TypeError, lambda : class_(False))

    def test_type_specific_attributes_removed_on_conversion(self):
        reference = {class_: class_(_sample_message).__dict__ for class_ in
            self.all_mailbox_types}
        for class1 in self.all_mailbox_types:
            for class2 in self.all_mailbox_types:
                if class1 is class2:
                    continue
                source = class1(_sample_message)
                target = class2(source)
                type_specific = [a for a in reference[class1] if a not in
                    reference[class2]]
                for attr in type_specific:
                    self.assertNotIn(attr, target.__dict__,
                        'while converting {} to {}'.format(class1, class2))

    def test_maildir_to_maildir(self):
        msg_maildir = mailbox.MaildirMessage(_sample_message)
        msg_maildir.set_flags('DFPRST')
        msg_maildir.set_subdir('cur')
        date = msg_maildir.get_date()
        msg = mailbox.MaildirMessage(msg_maildir)
        self._check_sample(msg)
        self.assertEqual(msg.get_flags(), 'DFPRST')
        self.assertEqual(msg.get_subdir(), 'cur')
        self.assertEqual(msg.get_date(), date)

    def test_maildir_to_mboxmmdf(self):
        pairs = ('D', ''), ('F', 'F'), ('P', ''), ('R', 'A'), ('S', 'R'), ('T',
            'D'), ('DFPRST', 'RDFA')
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg_maildir = mailbox.MaildirMessage(_sample_message)
            msg_maildir.set_date(0.0)
            for setting, result in pairs:
                msg_maildir.set_flags(setting)
                msg = class_(msg_maildir)
                self.assertEqual(msg.get_flags(), result)
                self.assertEqual(msg.get_from(), 'MAILER-DAEMON %s' % time.
                    asctime(time.gmtime(0.0)))
            msg_maildir.set_subdir('cur')
            self.assertEqual(class_(msg_maildir).get_flags(), 'RODFA')

    def test_maildir_to_mh(self):
        msg_maildir = mailbox.MaildirMessage(_sample_message)
        pairs = ('D', ['unseen']), ('F', ['unseen', 'flagged']), ('P', [
            'unseen']), ('R', ['unseen', 'replied']), ('S', []), ('T', [
            'unseen']), ('DFPRST', ['replied', 'flagged'])
        for setting, result in pairs:
            msg_maildir.set_flags(setting)
            self.assertEqual(mailbox.MHMessage(msg_maildir).get_sequences(),
                result)

    def test_maildir_to_babyl(self):
        msg_maildir = mailbox.MaildirMessage(_sample_message)
        pairs = ('D', ['unseen']), ('F', ['unseen']), ('P', ['unseen',
            'forwarded']), ('R', ['unseen', 'answered']), ('S', []), ('T',
            ['unseen', 'deleted']), ('DFPRST', ['deleted', 'answered',
            'forwarded'])
        for setting, result in pairs:
            msg_maildir.set_flags(setting)
            self.assertEqual(mailbox.BabylMessage(msg_maildir).get_labels(),
                result)

    def test_mboxmmdf_to_maildir(self):
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg_mboxMMDF = class_(_sample_message)
            msg_mboxMMDF.set_from('foo@bar', time.gmtime(0.0))
            pairs = ('R', 'S'), ('O', ''), ('D', 'T'), ('F', 'F'), ('A', 'R'
                ), ('RODFA', 'FRST')
            for setting, result in pairs:
                msg_mboxMMDF.set_flags(setting)
                msg = mailbox.MaildirMessage(msg_mboxMMDF)
                self.assertEqual(msg.get_flags(), result)
                self.assertEqual(msg.get_date(), 0.0)
            msg_mboxMMDF.set_flags('O')
            self.assertEqual(mailbox.MaildirMessage(msg_mboxMMDF).
                get_subdir(), 'cur')

    def test_mboxmmdf_to_mboxmmdf(self):
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg_mboxMMDF = class_(_sample_message)
            msg_mboxMMDF.set_flags('RODFA')
            msg_mboxMMDF.set_from('foo@bar')
            for class2_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
                msg2 = class2_(msg_mboxMMDF)
                self.assertEqual(msg2.get_flags(), 'RODFA')
                self.assertEqual(msg2.get_from(), 'foo@bar')

    def test_mboxmmdf_to_mh(self):
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg_mboxMMDF = class_(_sample_message)
            pairs = ('R', []), ('O', ['unseen']), ('D', ['unseen']), ('F',
                ['unseen', 'flagged']), ('A', ['unseen', 'replied']), ('RODFA',
                ['replied', 'flagged'])
            for setting, result in pairs:
                msg_mboxMMDF.set_flags(setting)
                self.assertEqual(mailbox.MHMessage(msg_mboxMMDF).
                    get_sequences(), result)

    def test_mboxmmdf_to_babyl(self):
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            msg = class_(_sample_message)
            pairs = ('R', []), ('O', ['unseen']), ('D', ['unseen', 'deleted']
                ), ('F', ['unseen']), ('A', ['unseen', 'answered']), ('RODFA',
                ['deleted', 'answered'])
            for setting, result in pairs:
                msg.set_flags(setting)
                self.assertEqual(mailbox.BabylMessage(msg).get_labels(), result
                    )

    def test_mh_to_maildir(self):
        pairs = ('unseen', ''), ('replied', 'RS'), ('flagged', 'FS')
        for setting, result in pairs:
            msg = mailbox.MHMessage(_sample_message)
            msg.add_sequence(setting)
            self.assertEqual(mailbox.MaildirMessage(msg).get_flags(), result)
            self.assertEqual(mailbox.MaildirMessage(msg).get_subdir(), 'cur')
        msg = mailbox.MHMessage(_sample_message)
        msg.add_sequence('unseen')
        msg.add_sequence('replied')
        msg.add_sequence('flagged')
        self.assertEqual(mailbox.MaildirMessage(msg).get_flags(), 'FR')
        self.assertEqual(mailbox.MaildirMessage(msg).get_subdir(), 'cur')

    def test_mh_to_mboxmmdf(self):
        pairs = ('unseen', 'O'), ('replied', 'ROA'), ('flagged', 'ROF')
        for setting, result in pairs:
            msg = mailbox.MHMessage(_sample_message)
            msg.add_sequence(setting)
            for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
                self.assertEqual(class_(msg).get_flags(), result)
        msg = mailbox.MHMessage(_sample_message)
        msg.add_sequence('unseen')
        msg.add_sequence('replied')
        msg.add_sequence('flagged')
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            self.assertEqual(class_(msg).get_flags(), 'OFA')

    def test_mh_to_mh(self):
        msg = mailbox.MHMessage(_sample_message)
        msg.add_sequence('unseen')
        msg.add_sequence('replied')
        msg.add_sequence('flagged')
        self.assertEqual(mailbox.MHMessage(msg).get_sequences(), ['unseen',
            'replied', 'flagged'])

    def test_mh_to_babyl(self):
        pairs = ('unseen', ['unseen']), ('replied', ['answered']), ('flagged',
            [])
        for setting, result in pairs:
            msg = mailbox.MHMessage(_sample_message)
            msg.add_sequence(setting)
            self.assertEqual(mailbox.BabylMessage(msg).get_labels(), result)
        msg = mailbox.MHMessage(_sample_message)
        msg.add_sequence('unseen')
        msg.add_sequence('replied')
        msg.add_sequence('flagged')
        self.assertEqual(mailbox.BabylMessage(msg).get_labels(), ['unseen',
            'answered'])

    def test_babyl_to_maildir(self):
        pairs = ('unseen', ''), ('deleted', 'ST'), ('filed', 'S'), ('answered',
            'RS'), ('forwarded', 'PS'), ('edited', 'S'), ('resent', 'PS')
        for setting, result in pairs:
            msg = mailbox.BabylMessage(_sample_message)
            msg.add_label(setting)
            self.assertEqual(mailbox.MaildirMessage(msg).get_flags(), result)
            self.assertEqual(mailbox.MaildirMessage(msg).get_subdir(), 'cur')
        msg = mailbox.BabylMessage(_sample_message)
        for label in ('unseen', 'deleted', 'filed', 'answered', 'forwarded',
            'edited', 'resent'):
            msg.add_label(label)
        self.assertEqual(mailbox.MaildirMessage(msg).get_flags(), 'PRT')
        self.assertEqual(mailbox.MaildirMessage(msg).get_subdir(), 'cur')

    def test_babyl_to_mboxmmdf(self):
        pairs = ('unseen', 'O'), ('deleted', 'ROD'), ('filed', 'RO'), (
            'answered', 'ROA'), ('forwarded', 'RO'), ('edited', 'RO'), (
            'resent', 'RO')
        for setting, result in pairs:
            for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
                msg = mailbox.BabylMessage(_sample_message)
                msg.add_label(setting)
                self.assertEqual(class_(msg).get_flags(), result)
        msg = mailbox.BabylMessage(_sample_message)
        for label in ('unseen', 'deleted', 'filed', 'answered', 'forwarded',
            'edited', 'resent'):
            msg.add_label(label)
        for class_ in (mailbox.mboxMessage, mailbox.MMDFMessage):
            self.assertEqual(class_(msg).get_flags(), 'ODA')

    def test_babyl_to_mh(self):
        pairs = ('unseen', ['unseen']), ('deleted', []), ('filed', []), (
            'answered', ['replied']), ('forwarded', []), ('edited', []), (
            'resent', [])
        for setting, result in pairs:
            msg = mailbox.BabylMessage(_sample_message)
            msg.add_label(setting)
            self.assertEqual(mailbox.MHMessage(msg).get_sequences(), result)
        msg = mailbox.BabylMessage(_sample_message)
        for label in ('unseen', 'deleted', 'filed', 'answered', 'forwarded',
            'edited', 'resent'):
            msg.add_label(label)
        self.assertEqual(mailbox.MHMessage(msg).get_sequences(), ['unseen',
            'replied'])

    def test_babyl_to_babyl(self):
        msg = mailbox.BabylMessage(_sample_message)
        msg.update_visible()
        for label in ('unseen', 'deleted', 'filed', 'answered', 'forwarded',
            'edited', 'resent'):
            msg.add_label(label)
        msg2 = mailbox.BabylMessage(msg)
        self.assertEqual(msg2.get_labels(), ['unseen', 'deleted', 'filed',
            'answered', 'forwarded', 'edited', 'resent'])
        self.assertEqual(msg.get_visible().keys(), msg2.get_visible().keys())
        for key in msg.get_visible().keys():
            self.assertEqual(msg.get_visible()[key], msg2.get_visible()[key])


class TestProxyFileBase(TestBase):

    def _test_read(self, proxy):
        proxy.seek(0)
        self.assertEqual(proxy.read(), b'bar')
        proxy.seek(1)
        self.assertEqual(proxy.read(), b'ar')
        proxy.seek(0)
        self.assertEqual(proxy.read(2), b'ba')
        proxy.seek(1)
        self.assertEqual(proxy.read(-1), b'ar')
        proxy.seek(2)
        self.assertEqual(proxy.read(1000), b'r')

    def _test_readline(self, proxy):
        linesep = os.linesep.encode()
        proxy.seek(0)
        self.assertEqual(proxy.readline(), b'foo' + linesep)
        self.assertEqual(proxy.readline(), b'bar' + linesep)
        self.assertEqual(proxy.readline(), b'fred' + linesep)
        self.assertEqual(proxy.readline(), b'bob')
        proxy.seek(2)
        self.assertEqual(proxy.readline(), b'o' + linesep)
        proxy.seek(6 + 2 * len(os.linesep))
        self.assertEqual(proxy.readline(), b'fred' + linesep)
        proxy.seek(6 + 2 * len(os.linesep))
        self.assertEqual(proxy.readline(2), b'fr')
        self.assertEqual(proxy.readline(-10), b'ed' + linesep)

    def _test_readlines(self, proxy):
        linesep = os.linesep.encode()
        proxy.seek(0)
        self.assertEqual(proxy.readlines(), [b'foo' + linesep, b'bar' +
            linesep, b'fred' + linesep, b'bob'])
        proxy.seek(0)
        self.assertEqual(proxy.readlines(2), [b'foo' + linesep])
        proxy.seek(3 + len(linesep))
        self.assertEqual(proxy.readlines(4 + len(linesep)), [b'bar' +
            linesep, b'fred' + linesep])
        proxy.seek(3)
        self.assertEqual(proxy.readlines(1000), [linesep, b'bar' + linesep,
            b'fred' + linesep, b'bob'])

    def _test_iteration(self, proxy):
        linesep = os.linesep.encode()
        proxy.seek(0)
        iterator = iter(proxy)
        self.assertEqual(next(iterator), b'foo' + linesep)
        self.assertEqual(next(iterator), b'bar' + linesep)
        self.assertEqual(next(iterator), b'fred' + linesep)
        self.assertEqual(next(iterator), b'bob')
        self.assertRaises(StopIteration, next, iterator)

    def _test_seek_and_tell(self, proxy):
        linesep = os.linesep.encode()
        proxy.seek(3)
        self.assertEqual(proxy.tell(), 3)
        self.assertEqual(proxy.read(len(linesep)), linesep)
        proxy.seek(2, 1)
        self.assertEqual(proxy.read(1 + len(linesep)), b'r' + linesep)
        proxy.seek(-3 - len(linesep), 2)
        self.assertEqual(proxy.read(3), b'bar')
        proxy.seek(2, 0)
        self.assertEqual(proxy.read(), b'o' + linesep + b'bar' + linesep)
        proxy.seek(100)
        self.assertFalse(proxy.read())

    def _test_close(self, proxy):
        self.assertFalse(proxy.closed)
        proxy.close()
        self.assertTrue(proxy.closed)
        proxy.close()
        self.assertTrue(proxy.closed)


class TestProxyFile(TestProxyFileBase, unittest.TestCase):

    def setUp(self):
        self._path = support.TESTFN
        self._file = open(self._path, 'wb+')

    def tearDown(self):
        self._file.close()
        self._delete_recursively(self._path)

    def test_initialize(self):
        self._file.write(b'foo')
        pos = self._file.tell()
        proxy0 = mailbox._ProxyFile(self._file)
        self.assertEqual(proxy0.tell(), pos)
        self.assertEqual(self._file.tell(), pos)
        proxy1 = mailbox._ProxyFile(self._file, 0)
        self.assertEqual(proxy1.tell(), 0)
        self.assertEqual(self._file.tell(), pos)

    def test_read(self):
        self._file.write(b'bar')
        self._test_read(mailbox._ProxyFile(self._file))

    def test_readline(self):
        self._file.write(bytes('foo%sbar%sfred%sbob' % (os.linesep, os.
            linesep, os.linesep), 'ascii'))
        self._test_readline(mailbox._ProxyFile(self._file))

    def test_readlines(self):
        self._file.write(bytes('foo%sbar%sfred%sbob' % (os.linesep, os.
            linesep, os.linesep), 'ascii'))
        self._test_readlines(mailbox._ProxyFile(self._file))

    def test_iteration(self):
        self._file.write(bytes('foo%sbar%sfred%sbob' % (os.linesep, os.
            linesep, os.linesep), 'ascii'))
        self._test_iteration(mailbox._ProxyFile(self._file))

    def test_seek_and_tell(self):
        self._file.write(bytes('foo%sbar%s' % (os.linesep, os.linesep),
            'ascii'))
        self._test_seek_and_tell(mailbox._ProxyFile(self._file))

    def test_close(self):
        self._file.write(bytes('foo%sbar%s' % (os.linesep, os.linesep),
            'ascii'))
        self._test_close(mailbox._ProxyFile(self._file))


class TestPartialFile(TestProxyFileBase, unittest.TestCase):

    def setUp(self):
        self._path = support.TESTFN
        self._file = open(self._path, 'wb+')

    def tearDown(self):
        self._file.close()
        self._delete_recursively(self._path)

    def test_initialize(self):
        self._file.write(bytes('foo' + os.linesep + 'bar', 'ascii'))
        pos = self._file.tell()
        proxy = mailbox._PartialFile(self._file, 2, 5)
        self.assertEqual(proxy.tell(), 0)
        self.assertEqual(self._file.tell(), pos)

    def test_read(self):
        self._file.write(bytes('***bar***', 'ascii'))
        self._test_read(mailbox._PartialFile(self._file, 3, 6))

    def test_readline(self):
        self._file.write(bytes('!!!!!foo%sbar%sfred%sbob!!!!!' % (os.
            linesep, os.linesep, os.linesep), 'ascii'))
        self._test_readline(mailbox._PartialFile(self._file, 5, 18 + 3 *
            len(os.linesep)))

    def test_readlines(self):
        self._file.write(bytes('foo%sbar%sfred%sbob?????' % (os.linesep, os
            .linesep, os.linesep), 'ascii'))
        self._test_readlines(mailbox._PartialFile(self._file, 0, 13 + 3 *
            len(os.linesep)))

    def test_iteration(self):
        self._file.write(bytes('____foo%sbar%sfred%sbob####' % (os.linesep,
            os.linesep, os.linesep), 'ascii'))
        self._test_iteration(mailbox._PartialFile(self._file, 4, 17 + 3 *
            len(os.linesep)))

    def test_seek_and_tell(self):
        self._file.write(bytes('(((foo%sbar%s$$$' % (os.linesep, os.linesep
            ), 'ascii'))
        self._test_seek_and_tell(mailbox._PartialFile(self._file, 3, 9 + 2 *
            len(os.linesep)))

    def test_close(self):
        self._file.write(bytes('&foo%sbar%s^' % (os.linesep, os.linesep),
            'ascii'))
        self._test_close(mailbox._PartialFile(self._file, 1, 6 + 3 * len(os
            .linesep)))


FROM_ = 'From some.body@dummy.domain  Sat Jul 24 13:43:35 2004\n'
DUMMY_MESSAGE = """From: some.body@dummy.domain
To: me@my.domain
Subject: Simple Test

This is a dummy message.
"""


class MaildirTestCase(unittest.TestCase):

    def setUp(self):
        self._dir = support.TESTFN
        if os.path.isdir(self._dir):
            support.rmtree(self._dir)
        elif os.path.isfile(self._dir):
            support.unlink(self._dir)
        os.mkdir(self._dir)
        os.mkdir(os.path.join(self._dir, 'cur'))
        os.mkdir(os.path.join(self._dir, 'tmp'))
        os.mkdir(os.path.join(self._dir, 'new'))
        self._counter = 1
        self._msgfiles = []

    def tearDown(self):
        list(map(os.unlink, self._msgfiles))
        support.rmdir(os.path.join(self._dir, 'cur'))
        support.rmdir(os.path.join(self._dir, 'tmp'))
        support.rmdir(os.path.join(self._dir, 'new'))
        support.rmdir(self._dir)

    def createMessage(self, dir, mbox=False):
        t = int(time.time() % 1000000)
        pid = self._counter
        self._counter += 1
        filename = '.'.join((str(t), str(pid), 'myhostname', 'mydomain'))
        tmpname = os.path.join(self._dir, 'tmp', filename)
        newname = os.path.join(self._dir, dir, filename)
        with open(tmpname, 'w') as fp:
            self._msgfiles.append(tmpname)
            if mbox:
                fp.write(FROM_)
            fp.write(DUMMY_MESSAGE)
        try:
            os.link(tmpname, newname)
        except (AttributeError, PermissionError):
            with open(newname, 'w') as fp:
                fp.write(DUMMY_MESSAGE)
        self._msgfiles.append(newname)
        return tmpname

    def test_empty_maildir(self):
        """Test an empty maildir mailbox"""
        self.mbox = mailbox.Maildir(support.TESTFN)
        self.assertIsNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())

    def test_nonempty_maildir_cur(self):
        self.createMessage('cur')
        self.mbox = mailbox.Maildir(support.TESTFN)
        self.assertIsNotNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())

    def test_nonempty_maildir_new(self):
        self.createMessage('new')
        self.mbox = mailbox.Maildir(support.TESTFN)
        self.assertIsNotNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())

    def test_nonempty_maildir_both(self):
        self.createMessage('cur')
        self.createMessage('new')
        self.mbox = mailbox.Maildir(support.TESTFN)
        self.assertIsNotNone(self.mbox.next())
        self.assertIsNotNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())
        self.assertIsNone(self.mbox.next())


_sample_message = """Return-Path: <gkj@gregorykjohnson.com>
X-Original-To: gkj+person@localhost
Delivered-To: gkj+person@localhost
Received: from localhost (localhost [127.0.0.1])
        by andy.gregorykjohnson.com (Postfix) with ESMTP id 356ED9DD17
        for <gkj+person@localhost>; Wed, 13 Jul 2005 17:23:16 -0400 (EDT)
Delivered-To: gkj@sundance.gregorykjohnson.com
Received: from localhost [127.0.0.1]
        by localhost with POP3 (fetchmail-6.2.5)
        for gkj+person@localhost (single-drop); Wed, 13 Jul 2005 17:23:16 -0400 (EDT)
Received: from andy.gregorykjohnson.com (andy.gregorykjohnson.com [64.32.235.228])
        by sundance.gregorykjohnson.com (Postfix) with ESMTP id 5B056316746
        for <gkj@gregorykjohnson.com>; Wed, 13 Jul 2005 17:23:11 -0400 (EDT)
Received: by andy.gregorykjohnson.com (Postfix, from userid 1000)
        id 490CD9DD17; Wed, 13 Jul 2005 17:23:11 -0400 (EDT)
Date: Wed, 13 Jul 2005 17:23:11 -0400
From: "Gregory K. Johnson" <gkj@gregorykjohnson.com>
To: gkj@gregorykjohnson.com
Subject: Sample message
Message-ID: <20050713212311.GC4701@andy.gregorykjohnson.com>
Mime-Version: 1.0
Content-Type: multipart/mixed; boundary="NMuMz9nt05w80d4+"
Content-Disposition: inline
User-Agent: Mutt/1.5.9i


--NMuMz9nt05w80d4+
Content-Type: text/plain; charset=us-ascii
Content-Disposition: inline

This is a sample message.

--
Gregory K. Johnson

--NMuMz9nt05w80d4+
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="text.gz"
Content-Transfer-Encoding: base64

H4sICM2D1UIAA3RleHQAC8nILFYAokSFktSKEoW0zJxUPa7wzJIMhZLyfIWczLzUYj0uAHTs
3FYlAAAA

--NMuMz9nt05w80d4+--
"""
_bytes_sample_message = _sample_message.encode('ascii')
_sample_headers = {'Return-Path': '<gkj@gregorykjohnson.com>',
    'X-Original-To': 'gkj+person@localhost', 'Delivered-To':
    'gkj+person@localhost', 'Received':
    """from localhost (localhost [127.0.0.1])
        by andy.gregorykjohnson.com (Postfix) with ESMTP id 356ED9DD17
        for <gkj+person@localhost>; Wed, 13 Jul 2005 17:23:16 -0400 (EDT)"""
    , 'Delivered-To': 'gkj@sundance.gregorykjohnson.com', 'Received':
    """from localhost [127.0.0.1]
        by localhost with POP3 (fetchmail-6.2.5)
        for gkj+person@localhost (single-drop); Wed, 13 Jul 2005 17:23:16 -0400 (EDT)"""
    , 'Received':
    """from andy.gregorykjohnson.com (andy.gregorykjohnson.com [64.32.235.228])
        by sundance.gregorykjohnson.com (Postfix) with ESMTP id 5B056316746
        for <gkj@gregorykjohnson.com>; Wed, 13 Jul 2005 17:23:11 -0400 (EDT)"""
    , 'Received':
    """by andy.gregorykjohnson.com (Postfix, from userid 1000)
        id 490CD9DD17; Wed, 13 Jul 2005 17:23:11 -0400 (EDT)"""
    , 'Date': 'Wed, 13 Jul 2005 17:23:11 -0400', 'From':
    '"Gregory K. Johnson" <gkj@gregorykjohnson.com>', 'To':
    'gkj@gregorykjohnson.com', 'Subject': 'Sample message', 'Mime-Version':
    '1.0', 'Content-Type': 'multipart/mixed; boundary="NMuMz9nt05w80d4+"',
    'Content-Disposition': 'inline', 'User-Agent': 'Mutt/1.5.9i'}
_sample_payloads = """This is a sample message.

--
Gregory K. Johnson
""", """H4sICM2D1UIAA3RleHQAC8nILFYAokSFktSKEoW0zJxUPa7wzJIMhZLyfIWczLzUYj0uAHTs
3FYlAAAA
"""


class MiscTestCase(unittest.TestCase):

    def test__all__(self):
        blacklist = {'linesep', 'fcntl'}
        support.check__all__(self, mailbox, blacklist=blacklist)


def test_main():
    tests = (TestMailboxSuperclass, TestMaildir, TestMbox, TestMMDF, TestMH,
        TestBabyl, TestMessage, TestMaildirMessage, TestMboxMessage,
        TestMHMessage, TestBabylMessage, TestMMDFMessage,
        TestMessageConversion, TestProxyFile, TestPartialFile,
        MaildirTestCase, TestFakeMailBox, MiscTestCase)
    support.run_unittest(*tests)
    support.reap_children()


if __name__ == '__main__':
    test_main()
