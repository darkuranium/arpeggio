from __future__ import print_function
import copy

from generator.grammar import *
from generator.lexer import *
from generator.parser import *

class Backend(object):
    def on_factor(self, f):
        for c in f.chi:
            if c is not None:
                self.on_expr(c)
    def on_sequence(self, s):
        for c in s.chi:
            if isinstance(c, Factor):
                self.on_factor(c)
    def on_expr(self, e):
        for c in e.chi:
            if isinstance(c, Sequence):
                self.on_sequence(c)
    def on_rule(self, r):
        for c in r.chi:
            if isinstance(c, Expr):
                self.on_expr(c)
    def on_grammar(self, g):
        for c in g.chi:
            if isinstance(c, Rule):
                self.on_rule(c)

    def generate(self, g):
        self.on_grammar(g)

class State(object):
    pass

class DynamicStack(object):
    def __init__(self, val):
        super(DynamicStack, self).__setattr__('_stack', [val])

    def push(self):
        self._stack.append(copy.copy(self._stack[-1]))
    def pop(self):
        return self._stack.pop()

    @property
    def dict(self):
        return self._stack[-1].__dict__

    def __len__(self):
        return len(self._stack)

    def __getattr__(self, key):
        return getattr(self._stack[-1], key)
    def __setattr__(self, key, val):
        return setattr(self._stack[-1], key, val)
    def __delattr__(self, key):
        return delattr(self._stack[-1], key)
    def __getitem__(self, key):
        return self._stack[key]

    def __enter__(self):
        self.push()
    def __exit__(self):
        self.pop()
