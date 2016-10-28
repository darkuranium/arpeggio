import re

class LexerIterator(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None
        self.pos = 0

    def __next__(self):
        while True:
            if self.pos == len(self.lexer.text):
                raise StopIteration()
            for r in self.lexer.re:
                m = r[1].match(self.lexer.text, self.pos)
                if m:
                    self.pos = m.end()
                    # skip comments & whitespace
                    if r[0].startswith('!') and r[0] != '!':
                        break
                    return (r[0], m.group())
            else:
                raise Exception('Invalid token near \'' + self.lexer.text[self.pos] + '\'')

    next = __next__
class Lexer(object):
    def __init__(self, text):
        super(Lexer, self).__init__()
        self.text = text

        self.res = (
            # ignorable
            ('!slcomment', r'//[^\r\n]*'),
            ('!mlcomment', r'/\*([^*]|\*[^/])*\*/', re.DOTALL),
            ('!whitespace', r'\s+'),

            # basic PEG elements
            (':', r':'),
            (';', r';'),
            ('/', r'/'),
            ('*', r'\*'),
            ('+', r'\+'),
            ('?', r'\?'),
            ('!', r'!'),
            ('&', r'&'),
            ('(', r'\('),
            (')', r'\)'),
            ('token', r'[A-Z][A-Za-z0-9_]*'),
            ('rule', r'[a-z][A-Za-z0-9_]*'),

            # AST output rules
            ('->', r'->'),
            ('=', r'='),
            ('~=', r'~='),
            ('...', r'\.\.\.'),
            ('var', r'\$[A-Za-z0-9_]*'),
            ('func', r'#[A-Za-z0-9_]*'),
        )
        self.re = tuple(map(lambda item: (item[0], re.compile(item[1], item[2] if len(item) > 2 else 0)), self.res))

    def __iter__(self):
        return LexerIterator(self)
