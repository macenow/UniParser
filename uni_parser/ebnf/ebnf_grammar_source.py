from uni_parser.ebnf.ebnf_grammar_obj import *
from uni_parser.ebnf.errors import GrammarNotExists, SyntaxError


class EBNFAtom:
    # match the `name` of a grammar
    NAME = Literal(
        re.compile('[a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*'), 'NAME')
    # match the value of `number` of a grammar
    NUMBER = Literal(re.compile('-?[0-9]{0,10}'), 'NUMBER')
    # match the value of `string` of a grammar, with format in `' ... '`
    # which already includes some atoms like 'True', ',', '.', etc.
    STRING = Literal(re.compile('\'[\w\W]*?\''),
                     'STRING')

    NEWLINE = Literal(r'\n', 'NEWLINE')
    STAR = Literal('*', 'STAR', escape=True)
    PLUS = Literal('+', 'PLUS', escape=True)
    ALT = Literal('|', 'ALT', escape=True)
    EXCEP = Literal('-', 'EXCEP', escape=True)
    LREP = Literal('{', 'LREP', escape=True)
    RREP = Literal('}', 'RREP', escape=True)
    LGR = Literal('(', 'LGR', escape=True)
    RGR = Literal(')', 'RGR', escape=True)
    LOP = Literal('[', 'LOP', escape=True)
    ROP = Literal(']', 'ROP', escape=True)
    DEF = Literal('::=', 'DEF', escape=True)  # DEF should be assigned manually
    EPSILON_EXPR = Literal('_e', 'EPSILON_EXPR', escape=True)
    EPSILON = Epsilon()


class EBNF:
    # `test` is the top level statement
    # `test`: (( `\n` )* (define)+ ( `\n` )*)+
    test = Base(
        [
            Group(
                [
                    Group(
                        [EBNFAtom.NEWLINE],
                    ),
                    Group(
                        [Refer('define')],
                        repeat=(1, -1)
                    ),
                    Group(
                        [EBNFAtom.NEWLINE],
                    ),
                ],
                repeat=(1, -1)
            ),
        ],
        name='test'
    )

    # `define`: NAME '::=' expr
    define = Base(
        [
            EBNFAtom.NAME,
            EBNFAtom.DEF,
            Refer('expr')
        ],
        name='define'
    )

    # `repetition`: '+' | '*' | '{' n1 n2 '}'
    # [ expr ] was handled in token scanner, will be convert to ( expr ){0, 1}
    repetition = Base(
        [EBNFAtom.PLUS],
        [EBNFAtom.STAR],
        [
            EBNFAtom.LREP,
            Group(
                [
                    EBNFAtom.NUMBER
                ],
                repeat=(1, 2)
            ),
            EBNFAtom.RREP
        ],
        name='repetition'
    )

    # `expr`: base_expr ( '|' base_expr )*
    expr = Base(
        [
            Refer('base_expr'),
            Group(
                [
                    EBNFAtom.ALT,
                    Refer('base_expr')
                ],
            ),

        ],
        name='expr'
    )

    # `base_expr`: ( atom_expr )+
    base_expr = Base(
        [
            Group(
                [Refer('atom_expr')],
                repeat=(1, -1)
            )
        ],
        name='base_expr'
    )

    # `atom_expr`: atom ( '+' | '*' | {x, x} )*
    atom_expr = Base(
        [
            Refer('atom'),
            Group([Refer('repetition')])
        ],
        name='atom_expr'
    )

    # `atom`: NAME | STRING | '(' expr ')' | EPSILON
    atom = Base(
        [EBNFAtom.NAME],
        [EBNFAtom.STRING],
        [
            EBNFAtom.LGR,
            Refer('expr'),
            EBNFAtom.RGR
        ],
        [EBNFAtom.EPSILON_EXPR],
        name='atom'
    )

    tracker = BuildTracker({
        'test': test,
        'define': define,
        'repetition': repetition,
        'expr': expr,
        'base_expr': base_expr,
        'atom_expr': atom_expr,
        'atom': atom,
    })

    @staticmethod
    def eliminate_i_lr(tracker: BuildTracker):
        """
        accept a tracker instance, format indirect left recursion to direct
        left recursion

        A ::= C X
        B ::= C Y
        C ::= A | B | Z
        ==>
        C ::= C X | C Y | Z
        """
        # TODO
        path_stack = []

        pass

    @staticmethod
    def eliminate_lr(tracker: BuildTracker):
        """
        accept a tracker instance, for eliminating direct left recursion

        E ::= E A B | E C D | F | G
                   expr1    , expr2
        ==>
        E ::= F E_LR | G E_LR
        E_LR ::= A B E_LR | C D E_LR | epsilon
        """
        expr1 = []
        expr2 = []

        # use `list()` force a copy of keys into a list rather than an iterator
        # otherwise error is thrown during operation to the dictionary
        for key in list(tracker):

            # `self` is a Base or Group instance
            self = tracker[key]
            if isinstance(self, Base):
                if self.grammars[0][0].name == self.name:

                    # eliminate direct left recursion
                    for grammar_list in self.grammars:
                        if grammar_list[0].name == self.name:
                            temp_list = grammar_list[1:]
                            temp_list.append(Refer(f'_{self.name}'))
                            expr1.append(temp_list)
                        else:
                            temp_list = grammar_list
                            temp_list.append(Refer(f'_{self.name}'))
                            expr2.append(temp_list)

                    # expand the two expr list into *args
                    del tracker[self.name]
                    tracker[self.name] = \
                        Base(*expr1, name=self.name)
                    tracker[f'_{self.name}'] = \
                        Base(*expr2, [EBNFAtom.EPSILON], name=f'_{self.name}')

    @staticmethod
    def build(tracker: BuildTracker, *grammars, debug=0):
        """
        build entry point

        set `debug` to `1` to print productions of all grammars
        """
        EBNF.eliminate_lr(tracker)
        EBNF.eliminate_i_lr(tracker)

        if not grammars:
            tracker['test'].build(tracker)
        else:
            for grammar in grammars:
                try:
                    _grammar = tracker[grammar]
                except:
                    raise GrammarNotExists(
                        f'Unknown EBNF grammar \'{grammar}\'.')
                else:
                    if isinstance(_grammar, Base):
                        _grammar.build(tracker)
        if debug:
            for grammar in tracker:
                if isinstance(tracker[grammar], Base):
                    print(tracker[grammar].print_productions())

    @staticmethod
    def match(tracker: BuildTracker, lexer: Lexer, grammar: str = None,
              return_ast: bool = False, message_only: bool = False, debug=0):
        """
        match entry point

        set `debug` to `1` to enable debug message with recursion indent
        """
        if not grammar:
            result = tracker['test'].match(lexer, debug)
        else:
            result = tracker[grammar].match(lexer, debug)

        if return_ast and not message_only:
            return result

        if lexer.current_token is not None or not result:
            if message_only:
                current_spelling = lexer.current_token.spelling
                last_spelling = lexer.last_token.spelling

                if len(lexer.current_token.spelling) > 30:
                    current_spelling = f'{lexer.current_token.spelling[0:18]}...{lexer.current_token.spelling[len(lexer.current_token.spelling) - 10:]}'
                if len(lexer.last_token.spelling) > 30:
                    last_spelling = f'{lexer.last_token.spelling[0:18]}...{lexer.last_token.spelling[len(lexer.last_token.spelling) - 10:]}'

                current_spelling = re.sub('<|>', '', current_spelling)
                last_spelling = re.sub('<|>', '', last_spelling)
                returned_message = {
                    'error_start': [lexer.current_token.position[0],
                                    lexer.current_token.position[1]],
                    'error_end': [lexer.last_token.position[2],
                                  lexer.last_token.position[3]],
                    'spelling': current_spelling,
                    'spelling_last': last_spelling,
                    'passed': False
                }
                if lexer.last_token.position[2] > lexer.current_token.position[
                    0] \
                        and lexer.current_token.spelling in ['if', 'for',
                                                             'while', 'elif',
                                                             'else']:
                    returned_message['analysis'] = 'condition'
                elif lexer.current_token.spelling == 'end':
                    returned_message['analysis'] = 'end'

                return returned_message
            else:
                raise SyntaxError(
                    f"""\n    Syntax Error while parsing, around chunk {lexer.current_token.position[0]}[{lexer.current_token.position[1]}] ... line {lexer.last_token.position[2]}[{lexer.last_token.position[3]}], near spelling < {repr(lexer.current_token.spelling)} >""")
        elif message_only:
            return {'passed': True}
