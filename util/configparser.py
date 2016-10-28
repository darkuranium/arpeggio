import re
from collections import defaultdict

# The "usual" Python ConfigParser is *TERRIBLE* (enforces sections, no way for
# robust multi-line strings, Py2 vs Py3 incompatibilities, etc ...), so I'm
# making my own.
class ConfigParser(object):
    def __init__(self):
        super(ConfigParser, self).__init__()
        self.dict = defaultdict(str)
    def read(self, fname):
        idset=r'[A-Za-z0-9_-]'
        newline=r'(?:\n|\r\n?)'

        re_wspace = re.compile(r'\s+')
        re_comment = re.compile(r'#[^\r\n]*')
        re_assign = re.compile(r'({NCHR}+)\s*\=\s*((?:\S|[ \t\f\v]\S)*)[ \t\f\v]*'.format(NCHR=idset))
        re_heredoc = re.compile(r'({NCHR}+) <<({NCHR}*){NL}(.*?({NL}))?\2>>{NL}'.format(NCHR=idset,NL=newline), re.DOTALL)

        # for errors
        re_getline = re.compile(r'[^\r\n]*')

        res = (
            ('!wspace', re_wspace),
            ('!comment', re_comment),
            ('assign', re_assign),
            ('heredoc', re_heredoc),
        )

        with open(fname, 'r') as f:
            text = f.read()
            pos = 0
            while pos < len(text):
                for kind, r in res:
                    m = r.match(text, pos)
                    if not m:
                        continue
                    pos = m.end()
                    if kind[0] == '!':
                        pass
                    elif kind == 'assign':
                        self.dict[m.group(1)] = m.group(2)
                    elif kind == 'heredoc':
                        if m.group(3):
                            self.dict[m.group(1)] = m.group(3)#[:-len(m.group(4))]
                        else:
                            self.dict[m.group(1)] = ''
                    break
                else:
                    m = re_getline.match(text, pos)
                    raise Exception('Unable to parse config file `%s` near "%s"' % (fname, m.group()))
