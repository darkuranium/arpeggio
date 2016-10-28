# PEGgio

***Warning:*** *PEGgio is alpha software! Bugs are to be expected at this point in its development.*

PEGgio is an advanced PEG ([Parsing Expression Grammar](https://en.wikipedia.org/wiki/Parsing_expression_grammar)) tool supporting the following main features:

- support for multiple language backends (currently, only a C backend exists, while Python and Javascript backends are planned Soon&trade;)
- direct AST transformation rules
- support for using tokens instead of strings as input

The first two features ensure that different languages can be guaranteed to parse *exactly* the same language (thus avoiding the problem of incompatible dialects, e.g. in Markdown). The third allows the tool to be used for more advanced languages, taking advantage of existing or different lexer implementations (for speed and/or separation of concerns).

Raw string input and packrat parsing are not *yet* supported, but support for them is coming (see "Planned Features" below).

## Syntax Reference

*(coming soon)*

## Example Grammars

###JSON:
```
json:   object / array                          ;

object: LBRACE ($p~=pair (COMMA $p~=pair)*)? RBRACE     ->  (OBJECT $p...);
pair:   $k=STRING COLON $v=value                        ->  (PAIR   $k $v);

array:  LARRAY ($i~=value (COMMA $i~=value)*)? RARRAY   ->  (ARRAY  $i...);

value:  object / array / STRING / NUMBER / BOOL / NULL  ;
```

## License

The tool is released under the 2-clause BSD license. This does ***not*** affect the generated code.

## Planned Features

- language backends:
    - C (already implemented, but needs improvement)
        - lookahead support
        - zero warnings on `-Wall`
    - Python
    - Javascript
    - *(any other; I accept contributions)*
- support for raw string input instead of only tokens
    - related: support for string literals in the grammar files
- (optionally-enabled) packrat parsing
