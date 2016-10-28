#include "output.GEN.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>

/*
    COLON   :
    COMMA   ,
    LBRACE  {
    RBRACE  }
    LARRAY  [
    RARRAY  ]
    STRING  "..."
    NUMBER  ...
    BOOL    true
            false
    NULL    null
*/
typedef struct LexData
{
    const char* str;
    size_t len;
} LexData;

#define PUSHTOK(KIND, LEN)  do { lex->tok.kind = (KIND); lex->tok.str = ptr; lex->tok.len = (LEN); lex->pos += (LEN); printf(">>> %s %u\n", KIND, (unsigned)lex->pos); return true; } while(0)
static bool startswith(const char* ptr, size_t len, const char* with)
{
    size_t wlen = strlen(with);
    if(len < wlen) return false;
    return !strncmp(ptr, with, wlen);
}
static bool lex_next(Lexer* lex)
{
    char spattern[512];
    double d;
    LexData* ldata = lex->data;
    const char* ptr;
    size_t i;
    int count;
start:
    ptr = &ldata->str[lex->pos];
    if(lex->pos >= ldata->len)
    {
        printf(">>> EOF\n");
        lex->tok.kind = "EOF";
        lex->tok.str = "<EOF>";
        lex->tok.len = 5;
        return true;
    }
    switch(*ptr)
    {
    case ':': PUSHTOK("COLON", 1);
    case ',': PUSHTOK("COMMA", 1);
    case '{': PUSHTOK("LBRACE", 1);
    case '}': PUSHTOK("RBRACE", 1);
    case '[': PUSHTOK("LARRAY", 1);
    case ']': PUSHTOK("RARRAY", 1);
    case '"':
        lex->tok.kind = "STRING";
        for(i = 1; lex->pos + i < ldata->len; i++)
            if(ptr[i] == '"')
                break;
        if(ptr[i] != '"') return false;
        PUSHTOK("STRING", i + 1);
    case ' ': case '\t': case '\v': case '\r': case '\n':
        lex->pos++;
        goto start;
    default:
        if(startswith(ptr, ldata->len - lex->pos, "true"))
            PUSHTOK("BOOL", 4);
        if(startswith(ptr, ldata->len - lex->pos, "false"))
            PUSHTOK("BOOL", 5);
        if(startswith(ptr, ldata->len - lex->pos, "null"))
            PUSHTOK("NULL", 4);

        snprintf(spattern, sizeof(spattern), "%%%ulf%%n", (unsigned int)(ldata->len - lex->pos));
        if(sscanf(ptr, spattern, &d, &count) == 1)
            PUSHTOK("NUMBER", count);
        return false;
    }
    assert(0); /* should be unreachable */
    return false;
}

int main(void)
{
    FILE* file = fopen("test.json", "rb");
    if(!file)
    {
        printf("Error opening file!\n");
        return 1;
    }

    fseek(file, 0, SEEK_END);
    long int len = ftell(file);
    if(len < 0)
    {
        printf("Error getting file length!\n");
        return 1;
    }
    fseek(file, 0, SEEK_SET);

    char* buf = malloc(len + 1);
    buf[len] = 0;
    if(fread(buf, 1, len, file) != len)
    {
        printf("Error reading from file!\n");
        return 1;
    }

    fclose(file);

    LexData data = { .str = buf, .len = len };

    Lexer lex = { .next = lex_next, .data = &data };

    /*while(lex.next(&lex))
    {
        printf("%s %.*s\n", lex.tok.kind, (int)lex.tok.len, lex.tok.str);
        if(!strcmp(lex.tok.kind, "EOF"))
            goto end;
    }
    printf("Error: Invalid token!\n");
    free(buf);
    return 1;*/

    ANodeList alist;
    if(parse(&alist, &lex))
    {
        alist_dump(alist, 0);
    }
    else
    {
        printf("Parsing Error!\n");
        free(buf);
        return 1;
    }

//end:
    free(buf);
    return 0;
}
