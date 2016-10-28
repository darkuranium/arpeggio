#ifndef COMMON_H_
#define COMMON_H_

#include <stddef.h>
#include <stdbool.h>

typedef struct Token Token;
typedef size_t LexerPos;
typedef struct Lexer Lexer;

struct Token
{
    const char* kind;
    const char* str;
    size_t len;
};
struct Lexer
{
    bool (*next)(Lexer* lex);
    void* data;
    Token tok;
    LexerPos pos;
};

typedef struct ANode ANode;
typedef struct ANodeList ANodeList;

struct ANodeList
{
    size_t len;
    ANode** ptr;
};

bool alist_is_empty(ANodeList a);
bool alist_is_multiple(ANodeList a);
ANodeList alist_append(ANodeList a, ANode* node);
ANodeList alist_concat(ANodeList a, ANodeList b);
ANode* alist_head(ANodeList a);

void alist_dump(ANodeList a, int indent);

struct ANode
{
    const char* kind;
    ANodeList chi;
};

ANode* anode_create(const char* kind);
void anode_chi_append(ANode* node, ANode* cnode);
void anode_chi_concat(ANode* node, ANodeList chi);

void anode_dump(ANode* node, int indent);

#endif /* COMMON_H_ */
