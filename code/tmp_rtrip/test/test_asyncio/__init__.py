import os
from test.support import load_package_tests, import_module
import_module('threading')
import_module('concurrent.futures')


def load_tests(*args):
    return load_package_tests(os.path.dirname(__file__), *args)
