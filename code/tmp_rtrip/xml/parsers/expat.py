"""Interface to the Expat non-validating XML parser."""
import sys
from pyexpat import *
sys.modules['xml.parsers.expat.model'] = model
sys.modules['xml.parsers.expat.errors'] = errors
