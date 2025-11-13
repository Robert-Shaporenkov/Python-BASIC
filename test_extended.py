import unittest
import sys
from basic import *

class TestLexerExtended(unittest.TestCase):
    def test_string_escapes(self):
        lexer = Lexer('<stdin>', '"hello\\nworld"')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(tokens[0].type, TT_STRING)
        self.assertEqual(tokens[0].value, 'hello\nworld')

    def test_arrow_token(self):
        lexer = Lexer('<stdin>', '->')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(tokens[0].type, TT_ARROW)

    def test_double_equals(self):
        lexer = Lexer('<stdin>', '==')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(tokens[0].type, TT_EE)

    def test_not_equals(self):
        lexer = Lexer('<stdin>', '!=')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(tokens[0].type, TT_NE)

    def test_less_equal_greater_equal(self):
        lexer = Lexer('<stdin>', '<= >=')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(tokens[0].type, TT_LTE)
        self.assertEqual(tokens[1].type, TT_GTE)

    def test_not_followed_by_eq_error(self):
        lexer = Lexer('<stdin>', '!')
        tokens, error = lexer.make_tokens()
        self.assertIsNotNone(error)
        self.assertIsInstance(error, ExpectedCharError)

    def test_illegal_char_error_percent(self):
        lexer = Lexer('<stdin>', '%')
        tokens, error = lexer.make_tokens()
        self.assertIsNotNone(error)
        self.assertIsInstance(error, IllegalCharError)

class TestParserExtended(unittest.TestCase):
    def test_list_parsing(self):
        lexer = Lexer('<stdin>', '[1, 2]')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, ListNode)
        self.assertEqual(len(ast.node.element_nodes), 2)

    def test_if_parsing(self):
        lexer = Lexer('<stdin>', 'if 1 then 2 else 3')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, IfNode)

    def test_for_parsing(self):
        lexer = Lexer('<stdin>', 'for i = 0 to 2 then i')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, ForNode)

    def test_while_parsing(self):
        lexer = Lexer('<stdin>', 'while 1 then 2')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, WhileNode)

    def test_func_def_parsing(self):
        lexer = Lexer('<stdin>', 'func add(a, b) -> a + b')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, FuncDefNode)
        self.assertEqual(ast.node.var_name_token.value, 'add')
        self.assertEqual(len(ast.node.arg_name_tokens), 2)

class TestInterpreterExtended(unittest.TestCase):
    def test_string_concatenation(self):
        value, error = run('<stdin>', '"a" + "b"')
        self.assertIsNone(error)
        self.assertIsInstance(value, String)
        self.assertEqual(value.value, 'ab')

    def test_string_multiplication(self):
        value, error = run('<stdin>', '"a" * 3')
        self.assertIsNone(error)
        self.assertIsInstance(value, String)
        self.assertEqual(value.value, 'aaa')

    def test_list_append_and_indexing(self):
        value, error = run('<stdin>', '[1] + 2')
        self.assertIsNone(error)
        self.assertIsInstance(value, List)
        self.assertEqual(value.elements[0].value, 1)
        self.assertEqual(value.elements[1].value, 2)

        v2, err2 = run('<stdin>', '[10, 20] / 1')
        self.assertIsNone(err2)
        self.assertIsInstance(v2, Number)
        self.assertEqual(v2.value, 20)

    def test_list_remove_and_concat(self):
        v, e = run('<stdin>', '[1,2] - 0')
        self.assertIsNone(e)
        self.assertIsInstance(v, List)
        self.assertEqual(len(v.elements), 1)
        self.assertEqual(v.elements[0].value, 2)

        v3, e3 = run('<stdin>', '[1] * [2,3]')
        self.assertIsNone(e3)
        self.assertIsInstance(v3, List)
        self.assertEqual(len(v3.elements), 3)
        self.assertEqual(v3.elements[1].value, 2)

    def test_list_index_out_of_range_error(self):
        v, e = run('<stdin>', '[1] / 5')
        self.assertIsNotNone(e)
        self.assertIsInstance(e, RTError)

    def test_function_definition_and_call(self):
        # define function
        lexer = Lexer('<stdin>', 'func dbl(x) -> x * 2')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)

        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        res = interpreter.visit(ast.node, context)
        self.assertIsNone(res.error)

        # call function
        lexer2 = Lexer('<stdin>', 'dbl(5)')
        tokens2, error2 = lexer2.make_tokens()
        self.assertIsNone(error2)
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        self.assertIsNone(ast2.error)
        result = interpreter.visit(ast2.node, context)
        self.assertIsNone(result.error)
        self.assertIsInstance(result.value, Number)
        self.assertEqual(result.value.value, 10)

    def test_function_arg_count_errors(self):
        # define function with two args
        lexer = Lexer('<stdin>', 'func f(a, b) -> a')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)

        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        res = interpreter.visit(ast.node, context)
        self.assertIsNone(res.error)

        # too few args
        lexer2 = Lexer('<stdin>', 'f(1)')
        tokens2, error2 = lexer2.make_tokens()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        result = interpreter.visit(ast2.node, context)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, RTError)

        # too many args
        lexer3 = Lexer('<stdin>', 'f(1,2,3)')
        tokens3, error3 = lexer3.make_tokens()
        parser3 = Parser(tokens3)
        ast3 = parser3.parse()
        result2 = interpreter.visit(ast3.node, context)
        self.assertIsNotNone(result2.error)
        self.assertIsInstance(result2.error, RTError)

    def test_comparisons_and_logic(self):
        v, e = run('<stdin>', '1 == 1')
        self.assertIsNone(e)
        self.assertIsInstance(v, Number)
        self.assertEqual(v.value, 1)

        v2, e2 = run('<stdin>', '1 != 2')
        self.assertIsNone(e2)
        self.assertEqual(v2.value, 1)

        v3, e3 = run('<stdin>', '2 < 3')
        self.assertIsNone(e3)
        self.assertEqual(v3.value, 1)

        v4, e4 = run('<stdin>', '3 >= 3')
        self.assertIsNone(e4)
        self.assertEqual(v4.value, 1)

    def test_and_or_short_examples(self):
        v, e = run('<stdin>', '1 and 0')
        self.assertIsNone(e)
        self.assertEqual(v.value, 0)
        v2, e2 = run('<stdin>', '0 or 1')
        self.assertIsNone(e2)
        self.assertEqual(v2.value, 1)

    def test_define_var_overwrites(self):
        # ensure variable assignment stores and overwrites
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()

        lexer = Lexer('<stdin>', 'var x = 5')
        tokens, err = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        res = interpreter.visit(ast.node, context)
        self.assertIsNone(res.error)
        self.assertEqual(res.value.value, 5)

        # overwrite
        lexer2 = Lexer('<stdin>', 'var x = 7')
        tokens2, err2 = lexer2.make_tokens()
        parser2 = Parser(tokens2)
        ast2 = parser2.parse()
        res2 = interpreter.visit(ast2.node, context)
        self.assertIsNone(res2.error)
        self.assertEqual(res2.value.value, 7)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)