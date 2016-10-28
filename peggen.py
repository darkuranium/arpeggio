from __future__ import print_function
import copy

from generator.grammar import *
from generator.lexer import *
from generator.parser import *

import importlib

Backend = importlib.import_module('backends.c').Backend

with open('json.peg', 'rb') as f:
#with open('predtest.peg', 'rb') as f:
#gwith open('test.peg', 'rb') as f:
    lexer = Lexer(f.read())
    parser = Parser(lexer)

    root = parser.parse()
    root.resolve()

    #print(root)

    backend = Backend(name='output')
    backend.generate(root)
