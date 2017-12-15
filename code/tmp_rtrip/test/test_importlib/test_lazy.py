import importlib
from importlib import abc
from importlib import util
import sys
import types
import unittest
from . import util as test_util


class CollectInit:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def exec_module(self, module):
        return self


class LazyLoaderFactoryTests(unittest.TestCase):

    def test_init(self):
        factory = util.LazyLoader.factory(CollectInit)
        lazy_loader = factory('module name', 'module path', kw='kw')
        loader = lazy_loader.loader
        self.assertEqual(('module name', 'module path'), loader.args)
        self.assertEqual({'kw': 'kw'}, loader.kwargs)

    def test_validation(self):
        with self.assertRaises(TypeError):
            util.LazyLoader.factory(object)


class TestingImporter(abc.MetaPathFinder, abc.Loader):
    module_name = 'lazy_loader_test'
    mutated_name = 'changed'
    loaded = None
    source_code = 'attr = 42; __name__ = {!r}'.format(mutated_name)

    def find_spec(self, name, path, target=None):
        if name != self.module_name:
            return None
        return util.spec_from_loader(name, util.LazyLoader(self))

    def exec_module(self, module):
        exec(self.source_code, module.__dict__)
        self.loaded = module


class LazyLoaderTests(unittest.TestCase):

    def test_init(self):
        with self.assertRaises(TypeError):
            util.LazyLoader(object)

    def new_module(self, source_code=None):
        loader = TestingImporter()
        if source_code is not None:
            loader.source_code = source_code
        spec = util.spec_from_loader(TestingImporter.module_name, util.
            LazyLoader(loader))
        module = spec.loader.create_module(spec)
        if module is None:
            module = types.ModuleType(TestingImporter.module_name)
        module.__spec__ = spec
        module.__loader__ = spec.loader
        spec.loader.exec_module(module)
        self.assertIsNone(loader.loaded)
        return module

    def test_e2e(self):
        importer = TestingImporter()
        assert importer.loaded is None
        with test_util.uncache(importer.module_name):
            with test_util.import_state(meta_path=[importer]):
                module = importlib.import_module(importer.module_name)
        self.assertIsNone(importer.loaded)
        self.assertEqual(module.__loader__, importer)
        self.assertIsNotNone(importer.loaded)
        self.assertEqual(module, importer.loaded)

    def test_attr_unchanged(self):
        module = self.new_module()
        self.assertEqual(TestingImporter.mutated_name, module.__name__)

    def test_new_attr(self):
        module = self.new_module()
        module.new_attr = 42
        self.assertEqual(42, module.new_attr)

    def test_mutated_preexisting_attr(self):
        module = self.new_module()
        module.__name__ = 'bogus'
        self.assertEqual('bogus', module.__name__)

    def test_mutated_attr(self):
        module = self.new_module()
        module.attr = 6
        self.assertEqual(6, module.attr)

    def test_delete_eventual_attr(self):
        module = self.new_module()
        del module.attr
        self.assertFalse(hasattr(module, 'attr'))

    def test_delete_preexisting_attr(self):
        module = self.new_module()
        del module.__name__
        self.assertFalse(hasattr(module, '__name__'))

    def test_module_substitution_error(self):
        with test_util.uncache(TestingImporter.module_name):
            fresh_module = types.ModuleType(TestingImporter.module_name)
            sys.modules[TestingImporter.module_name] = fresh_module
            module = self.new_module()
            with self.assertRaisesRegex(ValueError, 'substituted'):
                module.__name__

    def test_module_already_in_sys(self):
        with test_util.uncache(TestingImporter.module_name):
            module = self.new_module()
            sys.modules[TestingImporter.module_name] = module
            module.__name__


if __name__ == '__main__':
    unittest.main()
