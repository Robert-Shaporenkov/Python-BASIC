import unittest
import sys
from basic import *

def setUpModule():
    # This will run once before all tests
    print("\nRunning tests for BASIC interpreter...")

class TestLexer(unittest.TestCase):
    def setUp(self):
        # This will run before each test in this class
        print(f"\nRunning: {self._testMethodName}")

    def test_empty(self):
        lexer = Lexer('<stdin>', '')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TT_EOF)

    def test_numbers(self):
        lexer = Lexer('<stdin>', '123 12.34')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 3)  # 2 numbers + EOF
        self.assertEqual(tokens[0].type, TT_INT)
        self.assertEqual(tokens[0].value, 123)
        self.assertEqual(tokens[1].type, TT_FLOAT)
        self.assertEqual(tokens[1].value, 12.34)

    def test_operators(self):
        lexer = Lexer('<stdin>', '+ - * /')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 5)  # 4 operators + EOF
        self.assertEqual(tokens[0].type, TT_PLUS)
        self.assertEqual(tokens[1].type, TT_MINUS)
        self.assertEqual(tokens[2].type, TT_MUL)
        self.assertEqual(tokens[3].type, TT_DIV)

    def test_invalid_character(self):
        lexer = Lexer('<stdin>', '@')
        tokens, error = lexer.make_tokens()
        self.assertIsNotNone(error)
        self.assertIsInstance(error, IllegalCharError)

    def test_parentheses(self):
        lexer = Lexer('<stdin>', '(2 + 3)')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 6)  # LPAREN, INT, PLUS, INT, RPAREN
        self.assertEqual(tokens[0].type, TT_LPAREN)
        self.assertEqual(tokens[4].type, TT_RPAREN)

    def test_keywords(self):
        """Test lexing of keywords"""
        lexer = Lexer('<stdin>', 'var and or not')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 5)  # 4 keywords + EOF
        self.assertEqual(tokens[0].type, TT_KEYWORD)
        self.assertEqual(tokens[0].value, 'var')
        self.assertEqual(tokens[1].type, TT_KEYWORD)
        self.assertEqual(tokens[1].value, 'and')
        self.assertEqual(tokens[2].type, TT_KEYWORD)
        self.assertEqual(tokens[2].value, 'or')
        self.assertEqual(tokens[3].type, TT_KEYWORD)
        self.assertEqual(tokens[3].value, 'not')

    def test_identifier(self):
        """Test lexing of identifiers"""
        lexer = Lexer('<stdin>', 'x y z')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 4)  # 3 identifiers + EOF
        self.assertEqual(tokens[0].type, TT_IDENTIFIER)
        self.assertEqual(tokens[0].value, 'x')
        self.assertEqual(tokens[1].type, TT_IDENTIFIER)
        self.assertEqual(tokens[1].value, 'y')
        self.assertEqual(tokens[2].type, TT_IDENTIFIER)
        self.assertEqual(tokens[2].value, 'z')

    def test_variable_declaration(self):
        """Test lexing of variable declaration"""
        lexer = Lexer('<stdin>', 'var x = 123')
        tokens, error = lexer.make_tokens()
        self.assertIsNone(error)
        self.assertEqual(len(tokens), 5)  # var, identifier, equals, number, EOF
        self.assertEqual(tokens[0].type, TT_KEYWORD)
        self.assertEqual(tokens[0].value, 'var')
        self.assertEqual(tokens[1].type, TT_IDENTIFIER)
        self.assertEqual(tokens[1].value, 'x')
        self.assertEqual(tokens[2].type, TT_EQ)
        self.assertEqual(tokens[3].type, TT_INT)
        self.assertEqual(tokens[3].value, 123)

class TestParser(unittest.TestCase):
    def test_number(self):
        lexer = Lexer('<stdin>', '123')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, NumberNode)
        self.assertEqual(ast.node.token.value, 123)

    def test_float(self):
        lexer = Lexer('<stdin>', '12.34')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, NumberNode)
        self.assertEqual(ast.node.token.value, 12.34)

    def test_identifier(self):
        """Test lexing of identifiers"""
        lexer = Lexer('<stdin>', 'myVar')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, VarAccessNode)
        id_token = getattr(ast.node, 'token', None) or getattr(ast.node, 'var_name_token', None)
        self.assertIsNotNone(id_token)
        self.assertEqual(id_token.value, 'myVar')

    def test_variable_declaration(self):
        lexer = Lexer('<stdin>', 'var x = 10')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, VarAssignNode)
        self.assertEqual(ast.node.var_name_token.value, 'x')
        self.assertEqual(ast.node.value_node.token.value, 10)

    def test_binary_operation(self):
        lexer = Lexer('<stdin>', '1 + 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_PLUS)

    def test_unary_operation(self):
        lexer = Lexer('<stdin>', '-5')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, UnaryOpNode)
        self.assertEqual(ast.node.op_token.type, TT_MINUS)

    def test_parentheses(self):
        lexer = Lexer('<stdin>', '(1 + 2) * 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertIsInstance(ast.node.left_node, BinOpNode)

    def test_power_operation(self):
        lexer = Lexer('<stdin>', '2 ^ 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_POW)

    def test_invalid_syntax(self):
        lexer = Lexer('<stdin>', '1 +')  # Missing right operand
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNotNone(ast.error)
        self.assertIsInstance(ast.error, InvalidSyntaxError)

    def test_nested_expressions(self):
        lexer = Lexer('<stdin>', '(1 + 2) * (3 + 4)')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertIsInstance(ast.node.left_node, BinOpNode)
        self.assertIsInstance(ast.node.right_node, BinOpNode)

    def test_logical_operations(self):
        lexer = Lexer('<stdin>', '1 and 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_KEYWORD)
        self.assertEqual(ast.node.op_token.value, 'and')

    def test_if_statement(self):
        lexer = Lexer('<stdin>', 'if x > 0 then var y = 1 else var y = 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, IfNode)

    def test_for_loop(self):
        lexer = Lexer('<stdin>', 'for i = 1 to 10 step 1 then 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, ForNode)

    def test_while_loop(self):
        lexer = Lexer('<stdin>', 'while x < 10 then 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, WhileNode)

    def test_function_definition(self):
        lexer = Lexer('<stdin>', 'func myFunc(a, b) -> a + b')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, FuncDefNode)
        name_token = getattr(ast.node, 'name_token', None) or getattr(ast.node, 'var_name_token', None)
        self.assertIsNotNone(name_token)
        self.assertEqual(name_token.value, 'myFunc')

    def test_function_call(self):
        lexer = Lexer('<stdin>', 'myFunc(1, 2)')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, CallNode)
        # accept either a func_name_token alias or extract from node_to_call.var_name_token
        name_token = getattr(ast.node, 'func_name_token', None) or getattr(getattr(ast.node, 'node_to_call', None), 'var_name_token', None)
        self.assertIsNotNone(name_token)
        self.assertEqual(name_token.value, 'myFunc')

class TestInterpreter(unittest.TestCase):
    def test_number(self):
        lexer = Lexer('<stdin>', '123')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 123)

    def test_addition(self):
        lexer = Lexer('<stdin>', '1 + 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 3)

    def test_subtraction(self):
        lexer = Lexer('<stdin>', '5 - 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 2)

    def test_multiplication(self):
        lexer = Lexer('<stdin>', '4 * 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 8)

    def test_division(self):
        lexer = Lexer('<stdin>', '8 / 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 4)

    def test_division_by_zero(self):
        lexer = Lexer('<stdin>', '5 / 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, RTError)

    def test_complex_expression(self):
        lexer = Lexer('<stdin>', '2 * (3 + 4)')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 14)
    
    def test_unary_minus(self):
        """Test evaluation of unary minus"""
        lexer = Lexer('<stdin>', '-5')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, -5)

    def test_unary_plus(self):
        """Test evaluation of unary plus"""
        lexer = Lexer('<stdin>', '+5')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 5)

    def test_multiple_unary(self):
        """Test multiple unary operators"""
        lexer = Lexer('<stdin>', '--5')  # Should evaluate to 5
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 5)
    
    def test_power(self):
        """Test basic power operation"""
        lexer = Lexer('<stdin>', '2 ^ 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 8)  # 2³ = 8

    def test_power_with_negative(self):
        """Test power with negative number"""
        lexer = Lexer('<stdin>', '-2 ^ 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, -8)  # (-2)³ = -8
    
    def test_power_precedence_evaluation(self):
        """Test power operation precedence in evaluation"""
        lexer = Lexer('<stdin>', '2 * 3 ^ 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 18)  # 2 * (3²) = 2 * 9 = 18

    def test_power_with_parentheses(self):
        """Test power operation with parentheses"""
        lexer = Lexer('<stdin>', '(2 + 1) ^ 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 27)  # (2 + 1)³ = 3³ = 27

    def test_power_of_zero(self):
        """Test number raised to power of zero"""
        lexer = Lexer('<stdin>', '5 ^ 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 1)  # Any number ^ 0 = 1
    
    def test_var_assignment_and_access(self):
        """Test variable assignment and access"""
        # First assign the variable
        lexer = Lexer('<stdin>', 'var x = 42')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 42)

        # Then access the variable
        lexer = Lexer('<stdin>', 'x')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 42)

    def test_undefined_variable(self):
        """Test accessing undefined variable"""
        lexer = Lexer('<stdin>', 'y')  # Variable 'y' not defined
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, RTError)

    def test_logical_and_true(self):
        """Test logical AND with true condition"""
        lexer = Lexer('<stdin>', '1 and 1')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 1)

    def test_logical_and_false(self):
        """Test logical AND with false condition"""
        lexer = Lexer('<stdin>', '1 and 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

    def test_logical_or_true(self):
        """Test logical OR with true condition"""
        lexer = Lexer('<stdin>', '1 or 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 1)

    def test_logical_or_false(self):
        """Test logical OR with false condition"""
        lexer = Lexer('<stdin>', '0 or 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

    def test_logical_not_true(self):
        """Test logical NOT with true condition"""
        lexer = Lexer('<stdin>', 'not 0')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 1)

    def test_logical_not_false(self):
        """Test logical NOT with false condition"""
        lexer = Lexer('<stdin>', 'not 1')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        result = interpreter.visit(ast.node, context)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

class TestControlFlowAndFunctions(unittest.TestCase):
    def run_lines(self, lines):
        """Run multiple top-level expressions/statements in the same context in sequence."""
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = SymbolTable()
        last_result = None

        for code in lines:
            lexer = Lexer('<stdin>', code)
            tokens, error = lexer.make_tokens()
            self.assertIsNone(error, msg=f"Lexer error for '{code}': {error}")
            parser = Parser(tokens)
            ast = parser.parse()
            self.assertIsNone(ast.error, msg=f"Parser error for '{code}': {ast.error}")
            last_result = interpreter.visit(ast.node, context)
            # allow tests to assert runtime errors where expected
        return last_result, context

    def test_for_sum_1_to_5(self):
        # basic.py's for loop is exclusive of 'to' when step > 0, so use end=6 to include 5
        lines = [
            "var sum = 0",
            "for i = 1 to 6 step 1 then var sum = sum + i",
            "sum"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 15)  # 1+2+3+4+5 = 15

    def test_for_negative_step(self):
        lines = [
            "var last = 0",
            "for i = 5 to 0 step -1 then var last = i",
            "last"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 1)  # loop runs 5,4,3,2,1 -> last = 1

    def test_for_zero_iterations(self):
        # start == end -> no iterations for positive step
        lines = [
            "var count = 0",
            "for i = 1 to 1 step 1 then var count = count + 1",
            "count"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

    def test_for_default_step(self):
        # when 'step' omitted, interpreter uses step = 1
        lines = [
            "var sum = 0",
            "for i = 1 to 4 then var sum = sum + i",  # end=4 -> runs 1..3 => sum = 6
            "sum"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 6)

    def test_while_countdown(self):
        lines = [
            "var i = 3",
            "while i > 0 then var i = i - 1",
            "i"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

    def test_while_never_entered(self):
        lines = [
            "var i = 0",
            "while i > 0 then var i = i - 1",
            "i"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 0)

    def test_function_no_args(self):
        lines = [
            "var f = func() -> 42",
            "f()"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 42)

    def test_function_with_args(self):
        lines = [
            "var add = func(a, b) -> a + b",
            "add(2, 3)"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 5)

    def test_recursive_factorial(self):
        lines = [
            "var fact = func(n) -> if n <= 1 then 1 else n * fact(n - 1)",
            "fact(5)"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 120)

    def test_function_arg_count_mismatch_error(self):
        lines = [
            "var f = func(a, b) -> a + b",
            "f(1)"
        ]
        result, ctx = self.run_lines(lines)
        # expect runtime RTError for too few args
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, RTError)

    def test_closure_reads_outer(self):
        lines = [
            "var x = 10",
            "var f = func() -> x",
            "f()"
        ]
        result, ctx = self.run_lines(lines)
        self.assertIsNone(result.error)
        self.assertEqual(result.value.value, 10)


if __name__ == '__main__':
    # Replace the simple unittest.main() with this:
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)