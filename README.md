## UniParser

A universal parser engine

#### How to Make a Quick Run
**`loader.py`** is the "runner" script, in which you can customize the parser engine:
- `template_tag`: if the target language is a template language, provide template tags in the format of list (e.g.: `['{{}}', '{%%}']`)
- `var_define`: if the target language is a template language, provide the keyword of definining variable (e.g.: `var` refers to `var a = 1` in code)
- `end_tag`: if the target language is a template language, provide the end tag for statements in the format of list (e.g.: `['endfor', 'endif']`)
- `return_ast`: whether the engine will return an AST instance
- `save_ast`: whether the engine will save an human readable AST in a formatted string to a file with ".ast" extension
- `reserved_names`: customized reserved key word, the engine will not treat them as variable names
- `overwrite`: whether overwrite the old parser engine file based or not. If True, the old parser file will be overwriten based on former configurations

- folder `ast_results`: for storing saved AST files
- folder `grammars`: for storing EBNF grammar files (e.g.: `python.ebnf`)
- folder `sources`: for storing source code files, where the engine read code from

```python
# create a ParserLoader instance, load grammar file called "demo.ebnf" in folder "grammars"
p = ParserLoader('demo')

# configure parser engine
p.generator(template_tag=['{{}}'],
            var_define='let',
            end_tag=['end'],
            return_ast=True,
            save_ast=True,
            reserved_names=[],
            overwrite=True,
            indent=4)

# run parser engine
# source code can be read from a source file (in here is "sample.txt") or a string
# message_only is for Json API, if True then only a dict message wil be returned, for
# indicating engine's running status
#
# "debug" can be set to "1" (not boolean) for displaying grammar matching process
ast = p.parse(source_file='sample.txt',
            source_code="""""",
            message_only=False,
            debug=0)

# print AST in a human readable format (if "return_ast" has been set to True)
print(ast)
```
