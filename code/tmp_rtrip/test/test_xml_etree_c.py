import struct
from test import support
from test.support import import_fresh_module
import types
import unittest
cET = import_fresh_module('xml.etree.ElementTree', fresh=['_elementtree'])
cET_alias = import_fresh_module('xml.etree.cElementTree', fresh=[
    '_elementtree', 'xml.etree'])


@unittest.skipUnless(cET, 'requires _elementtree')
class MiscTests(unittest.TestCase):

    @support.bigmemtest(size=support._2G + 100, memuse=1, dry_run=False)
    def test_length_overflow(self, size):
        data = b'x' * size
        parser = cET.XMLParser()
        try:
            self.assertRaises(OverflowError, parser.feed, data)
        finally:
            data = None

    def test_del_attribute(self):
        element = cET.Element('tag')
        element.tag = 'TAG'
        with self.assertRaises(AttributeError):
            del element.tag
        self.assertEqual(element.tag, 'TAG')
        with self.assertRaises(AttributeError):
            del element.text
        self.assertIsNone(element.text)
        element.text = 'TEXT'
        with self.assertRaises(AttributeError):
            del element.text
        self.assertEqual(element.text, 'TEXT')
        with self.assertRaises(AttributeError):
            del element.tail
        self.assertIsNone(element.tail)
        element.tail = 'TAIL'
        with self.assertRaises(AttributeError):
            del element.tail
        self.assertEqual(element.tail, 'TAIL')
        with self.assertRaises(AttributeError):
            del element.attrib
        self.assertEqual(element.attrib, {})
        element.attrib = {'A': 'B', 'C': 'D'}
        with self.assertRaises(AttributeError):
            del element.attrib
        self.assertEqual(element.attrib, {'A': 'B', 'C': 'D'})

    def test_trashcan(self):
        e = root = cET.Element('root')
        for i in range(200000):
            e = cET.SubElement(e, 'x')
        del e
        del root
        support.gc_collect()


@unittest.skipUnless(cET, 'requires _elementtree')
class TestAliasWorking(unittest.TestCase):

    def test_alias_working(self):
        e = cET_alias.Element('foo')
        self.assertEqual(e.tag, 'foo')


@unittest.skipUnless(cET, 'requires _elementtree')
@support.cpython_only
class TestAcceleratorImported(unittest.TestCase):

    def test_correct_import_cET(self):
        self.assertEqual(cET.SubElement.__module__, '_elementtree')

    def test_correct_import_cET_alias(self):
        self.assertEqual(cET_alias.SubElement.__module__, '_elementtree')

    def test_parser_comes_from_C(self):
        self.assertNotIsInstance(cET.Element.__init__, types.FunctionType)


@unittest.skipUnless(cET, 'requires _elementtree')
@support.cpython_only
class SizeofTest(unittest.TestCase):

    def setUp(self):
        self.elementsize = support.calcobjsize('5P')
        self.extra = struct.calcsize('PnnP4P')
    check_sizeof = support.check_sizeof

    def test_element(self):
        e = cET.Element('a')
        self.check_sizeof(e, self.elementsize)

    def test_element_with_attrib(self):
        e = cET.Element('a', href='about:')
        self.check_sizeof(e, self.elementsize + self.extra)

    def test_element_with_children(self):
        e = cET.Element('a')
        for i in range(5):
            cET.SubElement(e, 'span')
        self.check_sizeof(e, self.elementsize + self.extra + struct.
            calcsize('8P'))


def test_main():
    from test import test_xml_etree
    support.run_unittest(MiscTests, TestAliasWorking,
        TestAcceleratorImported, SizeofTest)
    test_xml_etree.test_main(module=cET)


if __name__ == '__main__':
    test_main()
