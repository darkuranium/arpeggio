#include "common.h"

#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <stdio.h>

ANode* anode_create(const char* kind)
{
    static ANode InitNode;

    ANode* node = malloc(sizeof(ANode));
    *node = InitNode;

    node->kind = kind;

    return node;
}
void anode_chi_append(ANode* node, ANode* cnode)
{
    /*assert(!cnode->parent);
    cnode->parent = node;*/
    node->chi = alist_append(node->chi, cnode);
}
void anode_chi_concat(ANode* node, ANodeList chi)
{
    /*ANode* cnode;
    for(cnode = chi.head; cnode; cnode = cnode->nsib)
    {
        assert(!cnode->parent);
        cnode->parent = node;
    }*/
    node->chi = alist_concat(node->chi, chi);
}

//#define ALIST_ASSERT(a) assert(!(a).head == !(a).tail && (!(a).head || !(a).head->psib) && (!(a).tail || !(a).tail->nsib))
#define ALIST_ASSERT(a) do {  } while(0)

bool alist_is_empty(ANodeList a)
{
    ALIST_ASSERT(a);
    return !a.len;
}
bool alist_is_multiple(ANodeList a)
{
    return a.len > 1;
}
ANodeList alist_append(ANodeList a, ANode* node)
{
    ALIST_ASSERT(a);

    a.ptr = realloc(a.ptr, (a.len + 1) * sizeof(ANode*));
    a.ptr[a.len++] = node;
    return a;
}
ANodeList alist_concat(ANodeList a, ANodeList b)
{
    ALIST_ASSERT(a);
    ALIST_ASSERT(b);

    if(alist_is_empty(a)) return b;
    if(alist_is_empty(b)) return a;

    a.ptr = realloc(a.ptr, (a.len + b.len) * sizeof(ANode*));
    memcpy(a.ptr + a.len, b.ptr, b.len * sizeof(ANode*));
    a.len += b.len;
    return a;
}
ANode* alist_head(ANodeList a)
{
    return a.len ? a.ptr[0] : NULL;
}

void alist_dump(ANodeList a, int indent)
{
    size_t i;
    for(i = 0; i < a.len; i++)
        anode_dump(a.ptr[i], indent);
}
void anode_dump(ANode* node, int indent)
{
    size_t i;
    printf("%*s%s\n", indent * 2, "", node->kind);
    alist_dump(node->chi, indent + 1);
}
