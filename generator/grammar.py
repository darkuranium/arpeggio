class Node(object):
    nextid = 0

    def __init__(self):
        super(Node, self).__init__()
        self.chi = []
        self.id = Node.nextid
        Node.nextid += 1

    def strattrib(self):
        return '[%s]' % str(self.index) if hasattr(self, 'index') else None

    def __str__(self, indent = 0):
        a = self.strattrib()
        ret = ' ' * indent + type(self).__name__ + (' ' + a if a is not None else '') + '\n'
        for c in self.chi:
            ret += c.__str__(indent + 1) if c is not None else ' ' * (indent + 1) + 'None\n'
        return ret

    def resolve(self, g):
        assert hasattr(self, 'parent')

        if not hasattr(self, 'idseq'):
            self.idseq = self.parent.idseq + ['n%s' % self.id] if self.parent else ['n%s' % self.id]

        i = 0
        for c in self.chi:
            if c is not None:
                c.parent = self
                c.index = i
                c.resolve(g)
            i += 1

class SemAssignment(Node):
    def __init__(self, name, op):
        super(SemAssignment, self).__init__()
        self.name = name
        self.op = op

    def strattrib(self):
        return self.name + self.op
class SemNode(Node):
    def __init__(self, kind, value, nodes, ellip):
        super(SemNode, self).__init__()
        self.kind = kind
        self.value = value
        self.nodes = nodes
        self.ellip = ellip
        self.chi = nodes[:]

    def strattrib(self):
        return self.kind + ':' + self.value

    def resolveVars(self, vnames, capsem):
        # $v=X  -> $v       $v or nil
        # $v=X  -> $v...    $v or empty
        # $v~=X -> $v       ILLEGAL
        # $v~=X -> $v...    list
        if self.kind == 'var':
            if not self.value in vnames:
                raise Exception('Unknown variable ' + self.value)
            if vnames[self.value] == '~=' and self.ellip == False:
                raise Exception('Invalid use of list variable as node')
        elif self.kind == 'node' or self.kind == 'func':
            for node in self.nodes:
                node.resolveVars(vnames, capsem)

class SemTransform(Node):
    def __init__(self, nodes):
        super(SemTransform, self).__init__()
        self.nodes = nodes
        self.chi = nodes[:]

    def resolveVars(self, vnames, capsem):
        for node in self.nodes:
            node.resolveVars(vnames, capsem)

class Factor(Node):
    def __init__(self, kind, value, predicate, repeat, sema):
        super(Factor, self).__init__()
        self.kind = kind
        self.value = value
        self.predicate = predicate
        self.repeat = repeat
        self.sema = sema

        if isinstance(self.value, Expr):
            self.chi.append(self.value)

    def strattrib(self):
        return (self.sema.strattrib() if self.sema is not None else '') + (self.predicate if self.predicate is not None else '') + self.kind + ':' + (self.value if not isinstance(self.value, Expr) else '<...>') + ' ' + (self.repeat if self.repeat is not None else '')

    def resolveVars(self, vnames, capsem):
        if self.sema is not None:
            if self.sema.name in vnames and self.sema.op != vnames[self.sema.name]:
                raise Exception('Mixing operators for variable ' + self.sema.name)
            vnames[self.sema.name] = self.sema.op
            capsem = self.sema
        elif self.predicate:
            capsem = None
        self.sem_capvar = capsem
        if self.kind == 'expr':
            self.value.resolveVars(vnames, capsem)

    def resolve(self, g):
        self.idseq = self.parent.idseq + ['f%s' % self.index]
        super(Factor, self).resolve(g)
        if self.kind == 'rule':
            if self.value not in g.rules:
                raise Exception('Unknown rule \'' + self.value + '\'')

class Sequence(Node):
    def __init__(self, facts, sem):
        super(Sequence, self).__init__()
        self.facts = facts
        self.sem = sem
        self.chi = facts[:]
        self.chi.append(self.sem)

    def resolveVars(self, vnames, capsem):
        if capsem is None and self.sem is None: #$$$$$$$$$$$$$$$ TODO FLUID OUTPUT $$$$$$$$$$$$$$$$$$$$$$$$
            capsem = SemAssignment('', '~=')
        for c in self.chi:
            if c is not None:
                c.resolveVars(vnames, capsem)

    def resolve(self, g):
        self.idseq = self.parent.idseq + ['s%s' % self.index]
        super(Sequence, self).resolve(g)

        self.sem_vnames = {}
        self.resolveVars(self.sem_vnames, None)

        if self.sem:
            self.sem.resolveVars(self.sem_vnames, None)

class Expr(Node):
    def __init__(self, alts):
        super(Expr, self).__init__()
        self.alts = alts
        self.chi = alts[:]

    def resolveVars(self, vnames, capsem):
        for c in self.chi:
            if c is not None:
                c.resolveVars(vnames, capsem)

    def resolve(self, g):
        self.idseq = self.parent.idseq + ['e%s' % self.id]
        super(Expr, self).resolve(g)

class Rule(Node):
    def __init__(self, name, expr):
        super(Rule, self).__init__()
        self.name = name
        self.expr = expr
        self.chi.append(expr)

    def strattrib(self):
        return self.name + ' => ' + ','.join(self.idseq)

    def resolve(self, g):
        self.idseq = self.parent.idseq + [self.name]
        super(Rule, self).resolve(g)

class Grammar(Node):
    def __init__(self, frule, rules):
        super(Grammar, self).__init__()
        self.frule = frule
        self.rules = rules
        for name in rules:
            self.chi.append(rules[name])

    def resolve(self, g = None):
        self.parent = None
        self.idseq = []
        super(Grammar, self).resolve(self)
