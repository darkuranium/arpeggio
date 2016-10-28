from generator.grammar import *
from generator.lexer import Lexer

class Parser(object):
    def __init__(self, lexer):
        super(Parser, self).__init__()
        self.lexer = lexer
        self.lexi = None
        self.tok = None

    def shift(self):
        ret = self.tok[1] if self.tok is not None else None
        try:
            self.tok = next(self.lexi)
        except StopIteration:
            self.tok = ('eof', '<EOF>')
        return ret
    def match(self, *kinds):
        if self.check(*kinds):
            return self.shift()
        else:
            raise Exception('Parsing error near \'' + self.tok[1] + '\'')
    def check(self, *kinds):
        return self.tok[0] in kinds

    def _p_sem_assignment(self):
        '''$v~=X'''
        name = self.match('var')
        op = self.match('=', '~=')

        return SemAssignment(name[1:], op)
    def _p_sem_node(self):
        '''(...) or TOKEN or $var'''

        kind = None
        value = None
        nodes = []
        if self.check('('):
            self.shift()

            if self.check('token'):
                value = self.shift()
                kind = 'node'
            elif self.check('func'):
                value = self.shift()
                kind = 'func'
            else:
                raise Exception('Expected semantic node, found \'' + self.tok[1] + '\'')

            while self.check('(', 'token', 'var'):
                nodes.append(self._p_sem_node())

            self.match(')')
        elif self.check('token'):
            kind = 'token'
            value = self.shift()
        elif self.check('var'):
            kind = 'var'
            value = self.shift()[1:]
        else:
            raise Exception('Expected semantic item, found \'' + self.tok[1] + '\'')

        ellip = False
        if self.check('...'):
            self.shift()
            ellip = True
        #else epsilon

        return SemNode(kind, value, nodes, ellip)


    def _p_sem_transform(self):
        '''-> ...'''
        self.match('->')

        nodes = []
        while self.check('(', 'token', 'var'):
            nodes.append(self._p_sem_node())
        return SemTransform(nodes)

    def _p_factor(self):
        predicate = None
        sema = None
        if self.check('!', '&'):
            predicate = self.shift()
        elif self.check('var'):
            sema = self._p_sem_assignment()
        #else epsilon

        kind = None
        value = None

        if self.check('('):
            self.shift()
            kind = 'expr'
            value = self._p_expr()
            self.match(')')
        elif self.check('token', 'rule'):
            kind = self.tok[0]
            value = self.shift()
        else:
            raise Exception('Expected factor, got \'' + self.tok[1] + '\'')

        repeat = None
        if self.check('*', '+', '?'):
            repeat = self.shift()
        #else epsilon

        return Factor(kind, value, predicate, repeat, sema)

    def _p_sequence(self):
        facts = []
        while self.check('!', '&', '(', 'token', 'rule', 'var'):
            facts.append(self._p_factor())

        # semantic elements
        ast = None
        if self.check('->'):
            ast = self._p_sem_transform()
        #else epsilon
        return Sequence(facts, ast)
    def _p_expr(self):
        alts = []
        alts.append(self._p_sequence())
        while self.check('/'):
            self.shift()
            alts.append(self._p_sequence())
        return Expr(alts)
    def _p_rule(self):
        name = self.match('rule')
        self.match(':')
        expr = self._p_expr()
        self.match(';')
        return Rule(name, expr)

    def _p_grammar(self):
        frule = None
        rules = {}
        while self.check('rule'):
            rule = self._p_rule()
            if frule is None:
                frule = rule
            rules[rule.name] = rule
        return Grammar(frule, rules)

    def parse(self):
        self.lexi = iter(self.lexer)
        self.shift()

        rule = self._p_grammar()

        if not self.check('eof'):
            raise Exception('Expected EOF, found \'' + self.tok[1] + '\'')

        return rule
