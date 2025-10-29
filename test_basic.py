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

class TestParser(unittest.TestCase):
    def test_number(self):
        lexer = Lexer('<stdin>', '123')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, NumberNode)
        self.assertEqual(ast.node.token.value, 123)
    
    def test_power_operation(self):
        """Test parsing of power operation"""
        lexer = Lexer('<stdin>', '2 ^ 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_POW)

    def test_power_precedence(self):
        """Test power operation has higher precedence than multiplication"""
        lexer = Lexer('<stdin>', '2 * 3 ^ 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_MUL)
        self.assertIsInstance(ast.node.right_node, BinOpNode)
        self.assertEqual(ast.node.right_node.op_token.type, TT_POW)

    def test_binary_operation(self):
        lexer = Lexer('<stdin>', '1 + 2')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
        self.assertEqual(ast.node.op_token.type, TT_PLUS)

    def test_invalid_syntax(self):
        lexer = Lexer('<stdin>', '1 +')  # Missing right operand
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNotNone(ast.error)
        self.assertIsInstance(ast.error, InvalidSyntaxError)

    def test_nested_expressions(self):
        lexer = Lexer('<stdin>', '(1 + 2) * 3')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, BinOpNode)
    
    def test_unary_minus(self):
        """Test parsing of unary minus operation"""
        lexer = Lexer('<stdin>', '-5')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, UnaryOpNode)
        self.assertEqual(ast.node.op_token.type, TT_MINUS)

    def test_unary_plus(self):
        """Test parsing of unary plus operation"""
        lexer = Lexer('<stdin>', '+5')
        tokens, error = lexer.make_tokens()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsNone(ast.error)
        self.assertIsInstance(ast.node, UnaryOpNode)
        self.assertEqual(ast.node.op_token.type, TT_PLUS)

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
    

if __name__ == '__main__':
    # Replace the simple unittest.main() with this:
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)