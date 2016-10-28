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

#memoization: (pos,name,tree) => (517, 'pair', ('pair', ..., ...))

class CStream(object):
    def __init__(self):
        super(CStream, self).__init__()
        self.data = []
        self.indent = 0
    def printo(self, obj):
        self.data.append((self.indent, obj))
    #def prints(self, *args):
    #    self.data.append((self.indent, ' '.join(args)))
    def printsln(self, *args):
        self.data.append((self.indent, ' '.join(args) + '\n'))

    @classmethod
    def _generate_seq(cls, part):
        s = ''
        for val in part:
            if isinstance(val, CObject):
                vs = val.gen()
            elif isinstance(val, list):
                vs = cls._generate_seq(val)
            elif isinstance(val, dict):
                vs = cls._generate_seq(val.values())
            else:
                vs = val
            s += vs
        return s
    def generate(self):
        s = ''
        for indent,val in self.data:
            cindent = indent
            if isinstance(val, CObject):
                vs = val.gen()
                cindent = indent + val.indoff
            elif isinstance(val, list):
                vs = CStream._generate_seq(val)
            elif isinstance(val, dict):
                vs = CStream._generate_seq(val.values())
            else:
                vs = val
            s += ''.join('\t' * cindent + line + '\n' for line in vs.splitlines())
        return s

class CObject(object):
    def __init__(self):
        super(CObject, self).__init__()
        self.desc = ''
        self.indoff = 0
    def gen(self):
        raise NotImplementedError(self.__class__.__name__ + '.gen()')

class CRefObject(CObject):
    def __init__(self, value):
        super(CRefObject, self).__init__()
        #self.count = 0
        self.count = 1 ### $$$$$$$$$$ TBD: SET THIS TO 0 $$$$$$$$$$
        self.value = value
    def __format__(self, format):
        return self.use()
    def use(self):
        self.count += 1
        return self.value
    def gen(self):
        if self.count > 0:
            return self.genused()
        return ''
    def genused(self, stream):
        raise NotImplementedError(self.__class__.__name__ + '.genused()')

class CLabel(CRefObject):
    def __init__(self, name):
        super(CLabel, self).__init__(name)
        self.indoff = -1
    def genused(self):
        desc = ' /* %s */' % self.desc if self.desc else ''
        return '%s:%s\n' % (self.value, desc)

class CVarDecl(CRefObject):
    def __init__(self, type, name, defval = None):
        super(CVarDecl, self).__init__(name)
        self.type = type
        self.defval = defval
    def genused(self):
        desc = ' /* %s */' % self.desc if self.desc else ''
        return '%s %s%s;%s\n' % (self.type, self.value, ' = %s' % self.defval if self.defval else '', desc)

class CLenProxy(CObject):
    def __init__(self, obj):
        super(CObject, self).__init__()
        self.obj = obj
    def __format__(self, format):
        return str(len(self.obj))

# PSEUDOCODES:
# grammar       <preamble> rule* <postamble>
# rule          <preamble> expr <ok:postamble><err:postamble>
# expr          <save-vars> sequence* <ok:ast-transform|copy-vars>
# sequence      factor*
# factor        body
# &factor       <drop-vars> body
# !factor       <drop-vars> body
# factor?       <save-vars,save-pos> body <ok:copy-vars><err:load-pos>
# factor*       <save-vars,save-pos> @start: body <ok:copy-vars,goto-start><err:load-pos>
# factor+       body <save-vars,save-pos> @start: body <ok:copy-vars,goto-start><err:load-pos>
class CBackend(Backend):
    def __init__(self, name):
        super(CBackend, self).__init__()
        self.name = name
        self.S = DynamicStack(State())

        self.h = CStream()
        self.c = CStream()

        self.S.name = name
        self.S.alist_type = 'ANodeList'
        self.S.anode_type = 'ANode*'
        self.S.lexer_type = 'Lexer*'

    def _factor_body(self, f):
        op = f.sema.op if f.sema else None

        if f.kind == 'expr':
            super(CBackend, self).on_factor(f)
        elif f.kind == 'token':
            self.c.printsln('if(!LEXER_CHECK(lexer, {value}))'.format(value=f.value))
            self.c.indent += 1
            self.c.printsln('{stat_error}'.format(**self.S.dict))
            self.c.indent -= 1
            if op == '=':
                self.c.printsln('{var_o} = alist_append(elist, MKNODE_TOKEN(LEXER_VALUE(lexer)));'.format(**self.S.dict))
            else:
                self.c.printsln('{var_o} = alist_append({var_o}, MKNODE_TOKEN(LEXER_VALUE(lexer)));'.format(**self.S.dict))
            self.c.printsln('LEXER_NEXT(lexer);')
        elif f.kind == 'rule':
            if op == '=':
                self.c.printsln('{var_o} = elist;'.format(**self.S.dict))
            self.c.printsln('if(!p_{value}(&{var_o}, lexer))'.format(value=f.value, **self.S.dict))
            self.c.indent += 1
            self.c.printsln('{stat_error}'.format(**self.S.dict))
            self.c.indent -= 1
        else:
            assert False, 'Unknown factor kind `%s`' % f.kind

    def on_factor(self, f):
        self.c.printsln('/* <factor %s%s> */' % (f.id, ':%s' % f.repeat if f.repeat else ''))
        self.S.push()

        if f.predicate:
            # TODO: predicate!
            raise NotImplementedError('Factor.predicate')

        if f.repeat == '+': # '+' gets a single obligatory repeat
            self._factor_body(f)

        if f.repeat:
            self.S.var_ok = CVarDecl('bool', 'ok{slen}_{index}'.format(index=f.index, **self.S.dict))
            self.c.printo(self.S.var_ok)
            self.S.stat_ok = '{var_ok} = true;'.format(**self.S.dict)

            self.S.var_pos = CVarDecl('LexerPos', 'P{slen}_{index}'.format(index=f.index, **self.S.dict), 'LEXER_GETPOS(lexer)')
            self.c.printo(self.S.var_pos)

            self.S.stat_error = 'break;'

            if f.repeat == '?':
                self.c.printsln('do')
                self.c.printsln('{')
            elif f.repeat == '*' or f.repeat == '+':
                self.c.printsln('for(;;)')
                self.c.printsln('{')

            self.c.indent += 1

            self.S.vars = {}
            self.S.var_o = CVarDecl(self.S.alist_type, 'O{slen}_{index}'.format(index=f.index, **self.S.dict), 'elist')
            for name, var in self.S[-2].vars.items():
                if not f.sema or name != f.sema.name:
                    self.S.vars[name] = CVarDecl(self.S.alist_type, 'V{slen}_{var_name}'.format(var_name=name, **self.S.dict), 'elist')
                    self.c.printo(self.S.vars[name])
            if f.sema:
                self.S.vars[f.sema.name] = self.S.var_o
            self.c.printo(self.S.var_o)

            self.c.printsln('{var_ok} = false;'.format(**self.S.dict))
        elif f.sema:
            self.S.vars = {}
            for name, var in self.S[-2].vars.items():
                self.S.vars[name] = var
            self.S.var_o = CVarDecl(self.S.alist_type, 'O{slen}_{index}'.format(index=f.index, **self.S.dict), 'elist')
            self.S.vars[f.sema.name] = self.S.var_o
            self.c.printo(self.S.var_o)

        self._factor_body(f)

        if f.repeat:
            self.c.printsln('if({var_ok})'.format(**self.S.dict))
            self.c.printsln('{')
            self.c.indent += 1

            for name, var in self.S.vars.items():
                if name in self.S[-2].vars and (not f.sema or name != f.sema.name):
                    self.c.printsln('{pvar} = alist_concat({pvar}, {var});'.format(pvar=self.S[-2].vars[name], var=var))

            if f.sema:
                if f.sema.op == '=':
                    self.c.printsln('{pvar} = alist_concat(elist, {var_o});'.format(pvar=self.S[-2].vars[f.sema.name], **self.S.dict))
                else:
                    self.c.printsln('{pvar} = alist_concat({pvar}, {var_o});'.format(pvar=self.S[-2].vars[f.sema.name], **self.S.dict))
            else:
                self.c.printsln('{pvar_o} = alist_concat({pvar_o}, {var_o});'.format(pvar_o=self.S[-2].var_o, **self.S.dict))


            self.c.indent -= 1
            self.c.printsln('}')
            self.c.indent -= 1

            if f.repeat == '?':
                self.c.printsln('} while(0);')
            elif f.repeat == '*' or f.repeat == '+':
                self.c.printsln('}')
        elif f.sema:
            if f.sema.op == '=':
                self.c.printsln('{pvar} = alist_concat(elist, {var_o});'.format(pvar=self.S[-2].vars[f.sema.name], **self.S.dict))
            else:
                self.c.printsln('{pvar} = alist_concat({pvar}, {var_o});'.format(pvar=self.S[-2].vars[f.sema.name], **self.S.dict))

        self.S.pop()
        self.c.printsln('/* </factor %s> */' % f.id)

    def _add_sem_transform(self, sem):
        self.S.push()

        for node in sem.nodes:
            if node.kind == 'var':
                if self.S[-2].var_ast_kind == 'list':
                    self.c.printsln('{pvar_ast} = alist_concat({pvar_ast}, {var});'.format(pvar_ast=self.S[-2].var_ast, var=self.S.vars[node.value]))
                elif self.S[-2].var_ast_kind == 'node':
                    self.c.printsln('anode_chi_concat({pvar_ast}, {var});'.format(pvar_ast=self.S[-2].var_ast, var=self.S.vars[node.value]))
                else:
                    assert False, 'Unknown var_ast_kind `%s`' % self.S.var_ast_kind
            elif node.kind == 'node':
                self.S.var_ast = CVarDecl(self.S.anode_type, 'A{slen}'.format(**self.S.dict), 'MKNODE_SEM({kind})'.format(kind=node.value))
                self.S.var_ast_kind = 'node'
                self.c.printo(self.S.var_ast)

                self._add_sem_transform(node)

                if self.S[-2].var_ast_kind == 'list':
                    self.c.printsln('{pvar_ast} = alist_append({pvar_ast}, {var_ast});'.format(pvar_ast=self.S[-2].var_ast, var_ast=self.S[-1].var_ast))
                elif self.S[-2].var_ast_kind == 'node':
                    self.c.printsln('anode_chi_append({pvar_ast}, {var_ast});'.format(pvar_ast=self.S[-2].var_ast, var_ast=self.S[-1].var_ast))
                else:
                    assert False, 'Unknown var_ast_kind `%s`' % self.S.var_ast_kind
            elif node.kind == 'func':
                assert False, '$$$ TODO: SemNode kind `func` $$$'
            else:
                assert False, 'Unknown SemNode kind `%s`' % node.kind

        self.S.pop()

    def on_sequence(self, s):
        self.c.printsln('/* <sequence %s> */' % s.index)
        self.S.push()

        self.S.stat_error = 'break;'

        if s.index != 0:
            self.c.printsln('if(!{var_ok}) do'.format(**self.S.dict))
        else:
            self.c.printsln('do'.format(**self.S.dict))
        self.c.printsln('{')
        self.c.indent += 1
        if s.index != 0:
            self.c.printsln('LEXER_SETPOS(lexer, {var_pos});'.format(**self.S.dict))

        # $$$ TODO: Move saving vars to function
        self.S.vars = {}
        for name, kind in s.sem_vnames.items():
            self.S.vars[name] = CVarDecl(self.S.alist_type, 'V{slen}_{var_name}'.format(var_name=name, **self.S.dict), 'elist')
            self.c.printo(self.S.vars[name])
        self.S.var_o = CVarDecl(self.S.alist_type, 'O{slen}'.format(**self.S.dict), 'elist')
        self.c.printo(self.S.var_o)

        super(CBackend, self).on_sequence(s)

        if s.sem:
            self.c.printsln('/* <semantic> */')
            self.S.var_ast = self.S[-2].var_o
            self.S.var_ast_kind = 'list'
            self._add_sem_transform(s.sem)
            self.c.printsln('/* </semantic> */')
        else:
            self.c.printsln('/* <semantic auto %s> */' % '_'.join(s.idseq))
            for name, var in self.S.vars.items():
                if name in self.S[-2].vars:
                    self.c.printsln('{pvar} = alist_concat({pvar}, {var});'.format(pvar=self.S[-2].vars[name], var=var))
                else:
                    print('NNAME', self.S[-2].vars)
            self.c.printsln('{pvar_o} = alist_concat({pvar_o}, {var_o});'.format(pvar_o=self.S[-2].var_o, **self.S.dict))
            self.c.printsln('/* </semantic auto> */')

        self.c.printsln('{stat_ok}'.format(**self.S.dict))

        self.c.indent -= 1
        self.c.printsln('} while(0);')

        self.S.pop()
        self.c.printsln('/* </sequence %s> */' % s.index)
    def on_expr(self, e):
        self.c.printsln('/* <expr %s> */' % e.id)
        self.S.push()

        self.S.var_o = CVarDecl(self.S.alist_type, 'O{slen}'.format(**self.S.dict), 'elist')
        self.c.printo(self.S.var_o)

        self.S.var_ok = CVarDecl('bool', 'ok{slen}'.format(**self.S.dict), 'false')
        self.c.printo(self.S.var_ok)

        self.S.stat_ok = '{var_ok} = true;'.format(**self.S.dict)

        if len(e.alts) > 1:
            self.S.var_pos = CVarDecl('LexerPos', 'P{slen}'.format(**self.S.dict), 'LEXER_GETPOS(lexer)')
            self.c.printo(self.S.var_pos)

        super(CBackend, self).on_expr(e)

        self.c.printsln('if(!{var_ok})'.format(**self.S.dict))
        #self.c.printsln('{')
        self.c.indent += 1
        self.c.printsln('{pstat_error}'.format(pstat_error=self.S[-2].stat_error))
        self.c.indent -= 1
        #self.c.printsln('}')
        self.c.printsln('{var_po} = alist_concat({var_po}, {var_o});'.format(var_po=self.S[-2].var_o, var_o=self.S[-1].var_o))
        self.c.printsln('{pstat_ok}'.format(pstat_ok=self.S[-2].stat_ok))

        self.S.pop()
        self.c.printsln('/* </expr %s> */' % e.id)
    def on_rule(self, r):
        self.c.printsln('/* <rule %s> */' % r.name)
        self.S.push()

        self.S.rule_name = r.name
        self.S.stat_ok = 'return true;'
        self.S.stat_error = 'return false;'

        self.S.vars = {}
        self.S.vdecls = {}
        self.S.var_o = CVarDecl(self.S.alist_type, '*alist')

        self.c.printsln('static bool p_{rule_name}({alist_type}* alist, {lexer_type} lexer)'.format(**self.S.dict))
        self.c.printsln('{')
        self.c.indent += 1
        self.c.printo(self.S.vdecls)
        super(CBackend, self).on_rule(r)
        self.c.indent -= 1
        self.c.printsln('}')

        self.S.pop()
        self.c.printsln('/* </rule %s> */' % r.name)
    def on_grammar(self, g):
        self.S.frule_name = g.frule.name
        self.S.slen = CLenProxy(self.S)

        self.h.printsln('''\
#ifndef GRAMMAR_H_
#define GRAMMAR_H_

#include "common.h"
bool parse({alist_type}* alist, {lexer_type} lexer);

#endif /* GRAMMAR_H_ */'''.format(**self.S.dict))

        with open(self.name + '.h', 'w') as h:
            h.write(self.h.generate())

        self.c.printsln('''\
#include "{name}.h"
#include <assert.h>

#include <string.h>
#define MKNODE_TOKEN(TOK)       anode_create(TOK.kind)
#define MKNODE_SEM(KIND)        anode_create(#KIND)
#define MKNODE_NIL()            NULL
#define LEXER_NEXT(lex)         if(!(lex)->next((lex))) return false;
#define LEXER_CHECK(lex, KIND)  (!strcmp((lex)->tok.kind, (#KIND)))
#define LEXER_VALUE(lex)        ((lex)->tok)
#define LEXER_GETPOS(lex)       ((lex)->pos)
#define LEXER_SETPOS(lex, POS)  ((lex)->pos = (POS))

/*#ifdef GEN_DEBUG*/
#if 1
#include <stdio.h>
#define GEN_PRINTF(args) (fprintf args, fflush(stderr))
#else
#define GEN_PRINTF(args)
#endif

static ANodeList elist = {{}};
'''.format(**self.S.dict))

        for r in g.rules:
            self.c.printsln('static bool p_{rule_name}({alist_type}* alist, {lexer_type} lexer);'.format(rule_name=r, **self.S.dict))

        self.c.printsln()
        super(CBackend, self).on_grammar(g)
        self.c.printsln()

        self.c.printsln('''\
bool parse({alist_type}* alist, {lexer_type} lexer)
{{
\tLEXER_NEXT(lexer);

\tif(alist) *alist = elist;

\tif(!p_{frule_name}(alist, lexer)) return false;
\tif(!LEXER_CHECK(lexer, EOF)) return false;

\treturn true;
}}'''.format(**self.S.dict))

        with open(self.name + '.c', 'w') as c:
            c.write(self.c.generate())

with open('json.peg', 'rb') as f:
#with open('predtest.peg', 'rb') as f:
#gwith open('test.peg', 'rb') as f:
    lexer = Lexer(f.read())
    parser = Parser(lexer)

    root = parser.parse()
    root.resolve()

    #print(root)

    backend = CBackend('output')
    backend.generate(root)
