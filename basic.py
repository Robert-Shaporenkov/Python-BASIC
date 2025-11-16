##################################
# IMPORTS
##################################

from strings_with_arrows import string_with_arrows
from string import ascii_letters
import os
from math import pi

##################################
# CONSTANTS
##################################

DIGITS = "0123456789"
LETTERS = ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

##################################
# ERRORS
##################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}\n"
        result += f"File {self.pos_start.file_name}, line {self.pos_start.ln + 1}"
        result += f"\n\n{string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)}"
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Expected Character", details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context
    
    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}\n"
        result += f"\n\n{string_with_arrows(self.pos_start.file_text, self.pos_start, self.pos_end)}"
        return result

    def generate_traceback(self):
        result = ""
        pos = self.pos_start
        context = self.context

        while context:
            result = f"    File {pos.file_name}, line {str(pos.ln + 1)}, in {context.display_name}\n" + result
            pos = context.parent_entry_pos
            context = context.parent
        
        return "Traceback (most recent call last):\n" + result

##################################
# POSITION
##################################

class Position:
    def __init__(self, idx, ln, col, file_name, file_text):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self
    
    def copy(self):
        return Position(self.idx, self.ln, self.col, self.file_name, self.file_text)
    
    

##################################
# TOKENS
##################################

TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_STRING = "STRING"
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_POW = "POW"
TT_EQ = "EQ"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_LSQUARE = "LSQUARE"
TT_RSQUARE = "RSQUARE"
TT_EE = "EE"
TT_NE = "NE"
TT_LT = "LT"
TT_GT  ="GT"
TT_LTE = "LTE"
TT_GTE = "GTE"
TT_COMMA = "COMMA"
TT_ARROW = "ARROW"
TT_NEWLINE = "NEWLINE"
TT_EOF = "EOF"

KEYWORDS = [
    "var",
    "and",
    "or",
    "not",
    "if",
    "then",
    "elif",
    "else",
    "for",
    "to",
    "step",
    "while",
    "func",
    "end",
    "return",
    "continue",
    "break"
]


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        if pos_end:
            self.pos_end = pos_end

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value:
            return f"{self.type}:{self.value}"
        return f"{self.type}"

##################################
# LEXER
##################################

class Lexer:
    def __init__(self, file_name, text):
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, self.file_name, self.text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
    
    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char in ";\n":
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == "-":
                tokens.append(self.make_minus_or_arrow())
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == "^":
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == "[":
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "]":
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == "!":
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == "=":
                tokens.append(self.make_equals())
            elif self.current_char == "<":
                tokens.append(self.make_less_than())
            elif self.current_char == ">":
                tokens.append(self.make_greater_than())
            elif self.current_char == ",":
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, char)

        
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ""
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()
        
        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)
    
    def make_string(self):
        string = ""
        pos_start = self.pos.copy()
        self.advance()  # Skip the opening quote

        esc_char = False
        esc_chars = {
            "n": "\n",
            "t": "\t",
            "\\": "\\",
            '"': '"'
        }

        while self.current_char is not None:
            if esc_char:
                # Replace escape sequence with actual character
                string += esc_chars.get(self.current_char, self.current_char)
                esc_char = False  # Reset after processing escape
            else:
                if self.current_char == "\\":
                    esc_char = True  # Next char is escaped
                elif self.current_char == '"':
                    break  # End of string
                else:
                    string += self.current_char

            self.advance()

        self.advance()  # Skip closing quote
        return Token(TT_STRING, string, pos_start, self.pos)

    
    def make_identifier(self):
        id_str = ""
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS + "_":
            id_str += self.current_char
            self.advance()
        
        token_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(token_type, id_str, pos_start, self.pos)
    
    def make_minus_or_arrow(self):
        token_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == ">":
            self.advance()
            token_type = TT_ARROW
        
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None
        
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
    
    def make_equals(self):
        token_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            token_type = TT_EE
        
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_less_than(self):
        token_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            token_type = TT_LTE
        
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)
    
    def make_greater_than(self):
        token_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            token_type = TT_GTE
        
        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

##################################
# NODES
##################################

class NumberNode:
    def __init__(self, token):
        self.token = token

        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
    
    def __repr__(self):
        return f"{self.token}"

class StringNode:
    def __init__(self, token):
        self.token = token

        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
    
    def __repr__(self):
        return f"{self.token}"
    
class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes

        self.pos_start = pos_start
        self.pos_end = pos_end

class VarAccessNode:
    def __init__(self, var_name_token):
        self.var_name_token = var_name_token
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.var_name_token.pos_end

class VarAssignNode:
    def __init__(self, var_name_token, value_node):
        self.var_name_token = var_name_token
        self.value_node = value_node
        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.value_node.pos_end

class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.right_node = right_node
        self.op_token = op_token

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end
    
    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"

class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

        self.pos_start = self.op_token.pos_start
        self.pos_end = node.pos_end
    
    def __repr__(self):
        return f"({self.op_token}, {self.node})"

class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[-1])[0].pos_end

class ForNode:
    def __init__(self, var_name_token, start_value_node, end_value_node, step_value_node, body_node, should_return_none):
        self.var_name_token = var_name_token
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_none = should_return_none

        self.pos_start = self.var_name_token.pos_start
        self.pos_end = self.body_node.pos_end

class WhileNode:
    def __init__(self, condition_node, body_node, should_return_none):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_none = should_return_none

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end

class FuncDefNode:
    def __init__(self, var_name_token, arg_name_tokens, body_node, should_auto_return):
        self.var_name_token = var_name_token
        self.arg_name_tokens = arg_name_tokens
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if self.var_name_token:
            self.pos_start = self.var_name_token.pos_start
        elif len(self.arg_name_tokens) > 0:
            self.pos_start = self.arg_name_tokens[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start
        
        self.pos_end = self.body_node.pos_end

class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[-1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end

class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        
        self.pos_start = pos_start
        self.pos_end = pos_end

class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

##################################
# PARSE RESULT
##################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0
    
    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1
    
    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node
    
    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

##################################
# PARSER
##################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.advance()

    def advance(self):
        self.token_idx += 1
        self.update_current_token()
        return self.current_token
    
    def reverse(self, amount=1):
        self.token_idx -= amount
        self.update_current_token()
        return self.current_token
    
    def update_current_token(self):
        if self.token_idx >= 0 and self.token_idx < len(self.tokens):
            self.current_token = self.tokens[self.token_idx]
        
    
    ##################################

    def parse(self):
        res = self.statements()
        if not res.error and self.current_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
            self.current_token.pos_start, self.current_token.pos_end,
            "Expected '+', '-', '*', or '/'"
        ))
        return res
    
    ##################################

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_token.pos_start.copy()

        while self.current_token.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

        statement = res.register(self.statement())
        if res.error:
            return res
        statements.append(statement)

        more_statements = True
        
        while True:
            newline_count = 0
            while self.current_token.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False
            if not more_statements:
                break
            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)
        
        return res.success(ListNode(
            statements,
            pos_start,
            self.current_token.pos_end.copy()
        ))
    
    def statement(self):
        res = ParseResult()
        pos_start = self.current_token.pos_start.copy()

        if self.current_token.matches(TT_KEYWORD, "return"):
            res.register_advancement()
            self.advance()

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_token.pos_start.copy()))
        
        if self.current_token.matches(TT_KEYWORD, "continue"):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(pos_start, self.current_token.pos_start.copy()))
        
        if self.current_token.matches(TT_KEYWORD, "break"):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(pos_start, self.current_token.pos_start.copy()))
        
        expr = res.register(self.expr())
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'return', 'continue', 'break', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-' or '(', '[' or 'not'"
            ))
        
        return res.success(expr)
        

    
    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_token.pos_start.copy()

        if self.current_token.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected '['"
            ))
        
        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected ']', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-' or '(', '[' or 'not'"
            ))
        
            while self.current_token.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res
                
            if self.current_token.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f"Expected ',' or ']'"
                ))
            
            res.register_advancement()
            self.advance() 
    
        return res.success(ListNode(
            element_nodes,
            pos_start,
            self.current_token.pos_end.copy()
        ))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases("if"))
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))
    
    def if_expr_b(self):
        return self.if_expr_cases("elif")
    
    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_token.matches(TT_KEYWORD, "else"):
            res.register_advancement()
            self.advance()

            if self.current_token.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()

                statements = res.register(self.statements())
                if res.error:
                    return res
                else_case = (statements, True)

                if self.current_token.matches(TT_KEYWORD, "end"):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        "Expected 'end'"
                    ))
            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                else_case = (expr, False)
        
        return res.success(else_case)
    
    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None

        if self.current_token.matches(TT_KEYWORD, "elif"):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res
        
        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_token.matches(TT_KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected '{case_keyword}'"
            ))
        
        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'then'"
            ))
        
        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            statements = res.register(self.statements())
            if res.error:
                return res
            cases.append((condition, statements, True))

            if self.current_token.matches(TT_KEYWORD, "end"):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error:
                    return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            expr = res.register(self.statement())
            if res.error:
                return res
            cases.append((condition, expr, False))

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)
        
        return res.success((cases, else_case))

    def for_expr(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "for"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'for'"
            ))
        
        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected identifier"
            ))
        
        var_name = self.current_token
        res.register_advancement()
        self.advance()

        if self.current_token.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected '='"
            ))
        
        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "to"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'to'"
            ))
        
        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error:
            return res
        
        if self.current_token.matches(TT_KEYWORD, "step"):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error:
                return res
        else:
            step_value = None
            
        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'then'"
            ))
        
        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error:
                return res
            
            if not self.current_token.matches(TT_KEYWORD, "end"):
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f"Expected 'end'"
                ))
            
            res.register_advancement()
            self.advance()
        
            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))
        
        body = res.register(self.statement())
        if res.error:
            return res
        
        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    
    def while_expr(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "while"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'then'"
            ))
        
        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'then'"
            ))
        
        res.register_advancement()
        self.advance()

        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error:
                return res
            
            if not self.current_token.matches(TT_KEYWORD, "end"):
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f"Expected 'end'"
                ))
            
            res.register_advancement()
            self.advance()
        
            return res.success(WhileNode(condition, body, True))
        
        body = res.register(self.statement())
        if res.error:
            return res
        
        return res.success(WhileNode(condition, body, False))
    
    def func_def(self):
        res = ParseResult()

        if not self.current_token.matches(TT_KEYWORD, "func"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'func'"
            ))
        
        res.register_advancement()
        self.advance()

        var_name_token = None
        if self.current_token.type == TT_IDENTIFIER:
            var_name_token = self.current_token
            res.register_advancement()
            self.advance()
        
        if self.current_token.type != TT_LPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected '('"
            ))
        
        res.register_advancement()
        self.advance()
        arg_name_tokens = []

        if self.current_token.type == TT_IDENTIFIER:
            arg_name_tokens.append(self.current_token)
            res.register_advancement()
            self.advance()

            while self.current_token.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_token.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        f"Expected identifier"
                    ))
                
                arg_name_tokens.append(self.current_token)
                res.register_advancement()
                self.advance()
        
        if self.current_token.type != TT_RPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected ',' or ')'"
            ))
        else:
            if self.current_token.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f"Expected identifier or ')'"
                ))
        
        res.register_advancement()
        self.advance()

        if self.current_token.type == TT_ARROW:
            res.register_advancement()
            self.advance()
            node_to_return = res.register(self.expr())
            if res.error:
                return res

            return res.success(FuncDefNode(
                var_name_token,
                arg_name_tokens,
                node_to_return,
                True
            ))
        if self.current_token.type != TT_NEWLINE:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected '->' or NEWLINE"
            ))
        
        res.register_advancement()
        self.advance()

        body = res.register(self.statements())
        if res.error:
            return res
        
        if not self.current_token.matches(TT_KEYWORD, "end"):
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f"Expected 'end'"
            ))
        
        res.register_advancement()
        self.advance()

        return res.success(FuncDefNode(
            var_name_token,
            arg_name_tokens,
            body,
            False
        ))

    ##################################        
    
    def atom(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(token))
    
        elif token.type == TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(token))
        
        elif token.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(token))
        
        elif token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.pos_start, self.pos_end,
                    "Expected ')'"
                ))
        
        elif token.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list_expr)
        
        elif token.matches(TT_KEYWORD, "if"):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)
        
        elif token.matches(TT_KEYWORD, "for"):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)
        
        elif token.matches(TT_KEYWORD, "while"):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)
        
        elif token.matches(TT_KEYWORD, "func"):
            func_def = res.register(self.func_def())
            if res.error:
                return res
            return res.success(func_def)
        
        return res.failure(InvalidSyntaxError(
            token.pos_start, token.pos_end,
            "Expected int, float, identifier, '+', '-' or '(', '[', 'if', 'for', 'while', 'func'"
        ))

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res
        
        if self.current_token.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_token.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected ')', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-', '(', '[' or 'not'"
                ))
            
                while self.current_token.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res
                    
                if self.current_token.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        f"Expected ',' or ')'"
                    ))
                
                res.register_advancement()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)
                
    def power(self):
        return self.bin_op(self.call, (TT_POW, ), self.factor)
    
    def factor(self):
        res = ParseResult()
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(token, factor))

        return self.power()

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV)) #both term and expr use bin_op()

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))
    
    def comp_expr(self):
        res = ParseResult()

        if self.current_token.matches(TT_KEYWORD, "not"):
            op_token = self.current_token
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_token, node))
        
        node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
    
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))
        
        return res.success(node)

    def expr(self):
        res = ParseResult()

        if self.current_token.matches(TT_KEYWORD, "var"):
            res.register_advancement()
            self.advance()

            if self.current_token.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected identifier"
                ))
            
            var_name = self.current_token
            res.register_advancement()
            self.advance()

            if self.current_token.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    "Expected '='"
                ))
            
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                "Expected 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-' or '(', '[' or 'not'"
            ))
        return res.success(node)
    
    ################################## 

    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error:
            return res

        while self.current_token.type in ops or (self.current_token.type, self.current_token.value) in ops:
            op_token = self.current_token
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_token, right)
        
        return res.success(left)

##################################
# RUNTIME RESULT
##################################

class RTResult:
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False
    
    def register(self, res):
        if res is None:
            return None
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self
    
    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self
    
    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self
    
    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self
    
    def failure(self, error):
        self.reset()
        self.error = error
        return self
    
    def should_return(self):
        return (
            self.error or 
            self.func_return_value or
            self.loop_should_continue or 
            self.loop_should_break
        )
    

##################################
# VALUES
##################################

class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def added_to(self, other):
        return None, self.illegal_operation(other)
    
    def subbed_by(self, other):
        return None, self.illegal_operation(other)
    
    def multed_by(self, other):
        return None, self.illegal_operation(other)
    
    def dived_by(self, other):
        return None, self.illegal_operation(other)

    def powed_by(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)
        
    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)
    
    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)
    
    def anded_by(self, other):
        return None, self.illegal_operation(other)
    
    def ored_by(self, other):
        return None, self.illegal_operation(other)
    
    def notted(self):
        return None, self.illegal_operation()
    
    def execute(self, args):
        return RTResult().failure(self.illegal_operation())
    
    def copy(self):
        raise Exception("No copy method defined")
    
    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if other is None:
            other = self
        return RTError(
            self.pos_start, self.pos_end,
            "Illegal operation",
            self.context
        )
    
    def __repr__(self):
        return f"{self.value}"

class Number(Value):

    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
    
    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    self.pos_start, other.pos_end,
                    "Division by zero",
                    self.context
                )
            
            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def powed_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value ** other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(self.value and other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(self.value or other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self.pos_start, other.pos_end)
        
    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None
    
    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def is_true(self):
        return self.value != 0

    def __repr__(self):
        return str(self.value)

Number.none = Number(0)
Number.true = Number(1)
Number.false = Number(0)
Number.math_pi = Number(pi)

class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"
    
    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        res = RTResult()

        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
                self.context
            ))
        
        if len(args) < len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(arg_names) - len(args)} too few args passed into '{self.name}'",
                self.context
            ))
        
        return res.success(None)
    
    def populate_args(self, arg_names, args, exec_ctx):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)
    
    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, exec_ctx)
        return res.success(None)

class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return
    
    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
        if res.should_return():
            return res
 
        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value is None:
            return res
        
        return_value = (value if self.should_auto_return else None) or res.func_return_value or Number.none
        return res.success(return_value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f"<function {self.name}>"

class BuiltInFunction(BaseFunction):

    def __init__(self, name):
        super().__init__(name)
    
    def execute(self, args):
        res = RTResult()
        exec_ctx = self.generate_new_context()

        method_name = f"execute_{self.name}"
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
        if res.should_return():
            return res
        
        return_value = res.register(method(exec_ctx))
        if res.should_return():
            return res
        return res.success(return_value)

    
    def no_visit_method(self, node, context):
        raise Exception(f"No execute_{self.name} method defined")
    
    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy
    
    def __repr__(self):
        return f"<built-in function {self.name}"
    
    ##################################

    def execute_print(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        print(str(value))
        return RTResult().success(Number.none)
    execute_print.arg_names = ["value"]

    def execute_print_return(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        if isinstance(value, String):
            return RTResult().success(value)
        return RTResult().success(String(str(value)))
    execute_print_return.arg_names = ["value"]

    def execute_input(self, exec_ctx):
        text = input()
        return RTResult().success(String(text))
    execute_input.arg_names = []

    def execute_input_int(self, exec_ctx):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer.")
        return RTResult().success(Number(number))
    execute_input_int.arg_names = []

    ##################################
    
    def execute_clear(self, exec_ctx):
        os.system("cls" if os.name == "nt" else "clear")
        return RTResult().success(Number.none)
    execute_clear.arg_names = []

    ##################################

    def execute_is_num(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_num.arg_names = ["value"]

    def execute_is_str(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_str.arg_names = ["value"]

    def execute_is_list(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_list.arg_names = ["value"]

    def execute_is_func(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_func.arg_names = ["value"]

    ##################################

    def execute_append(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First arg must be list",
                exec_ctx
            ))
        
        list_.elements.append(value)
        return RTResult().success(Number.none)
    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First arg must be list",
                exec_ctx
            ))
        
        if not isinstance(index, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second arg must be number",
                exec_ctx
            ))
        
        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Element could not be removed because list index out of range",
                exec_ctx
            ))    
        return RTResult().success(element)
    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, exec_ctx):
        listA = exec_ctx.symbol_table.get("listA")
        listB = exec_ctx.symbol_table.get("listB")

        if not isinstance(listA, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First arg must be list",
                exec_ctx
            ))
        
        if not isinstance(listB, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second arg must be list",
                exec_ctx
            ))
        
        listA.elements.extend(listB.elements)
        return RTResult().success(Number.none)
    execute_extend.arg_names = ["listA", "listB"]  

class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
    
    def is_true(self):
        return len(self.value) > 0
    
    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return f'"{self.value}"'

class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements
    
    def added_to(self, other):
        new_list = self.copy()
        new_list.elements.append(other)
        return new_list, None

    def subbed_by(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            try:
                new_list.elements.pop(other.value)
                return new_list, None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    "Element at this index could not be removed from list because list index out of range",
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)  
    
    def multed_by(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        else:
            return None, Value.illegal_operation(self, other)
    
    def dived_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    "Element at this index could not be accessed because list index out of range",
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)  
    
    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
    
    def __str__(self):
        return f"[{', '.join([repr(x) for x in self.elements])}]"

    def __repr__(self):
        return self.__str__()

##################################
# Built-in Functions
##################################

BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_return = BuiltInFunction("print_return") 
BuiltInFunction.input = BuiltInFunction("input") 
BuiltInFunction.input_int = BuiltInFunction("input_int") 
BuiltInFunction.clear = BuiltInFunction("clear") 
BuiltInFunction.is_num = BuiltInFunction("is_num") 
BuiltInFunction.is_str = BuiltInFunction("is_str") 
BuiltInFunction.is_list = BuiltInFunction("is_list") 
BuiltInFunction.is_func = BuiltInFunction("is_func")
BuiltInFunction.append = BuiltInFunction("append") 
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend") 



##################################
# CONTEXT
##################################

class Context():
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None

    
##################################
# SYMBOL TABLE
##################################

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.get(name)
        return value
    
    def set(self, name, value):
        self.symbols[name] = value
    
    def remove(self, name):
        del self.symbols[name]

##################################
# INTERPRETER
##################################

class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    ##################################

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res
        
        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))
        
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        
        return res.success(value)
    
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_token.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res
        
        context.symbol_table.set(var_name, value)
        return res.success(value)
        
    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res

        if node.op_token.type == TT_PLUS:
            result, error = left.added_to(right)
        
        elif node.op_token.type == TT_MINUS:
            result, error = left.subbed_by(right)
        
        elif node.op_token.type == TT_MUL:
            result, error = left.multed_by(right)
        
        elif node.op_token.type == TT_DIV:
            result, error = left.dived_by(right)
        
        elif node.op_token.type == TT_POW:
            result, error = left.powed_by(right)
        
        if node.op_token.type == TT_EE:
            result, error = left.get_comparison_eq(right)
        
        elif node.op_token.type == TT_NE:
            result, error = left.get_comparison_ne(right)
        
        elif node.op_token.type == TT_LT:
            result, error = left.get_comparison_lt(right)
        
        elif node.op_token.type == TT_GT:
            result, error = left.get_comparison_gt(right)
        
        elif node.op_token.type == TT_LTE:
            result, error = left.get_comparison_lte(right)
        
        elif node.op_token.type == TT_GTE:
            result, error = left.get_comparison_gte(right)

        elif node.op_token.matches(TT_KEYWORD, "and"):
            result, error = left.anded_by(right)
        
        elif node.op_token.matches(TT_KEYWORD, "or"):
            result, error = left.ored_by(right)
        
        if error:
            return res.failure(error)
        else:
            return res.success(
                result.set_pos(node.pos_start, node.pos_end)
            )

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res
        
        error = None

        if node.op_token.type == TT_MINUS:
            number, error = number.multed_by(Number(-1).set_context(context))
        elif node.op_token.matches(TT_KEYWORD, "not"):
            number, error = number.notted()



        if error:
            return res.failure(error)
        else:
            return res.success(
                number.set_pos(node.pos_start, node.pos_end)
            )
    
    def visit_IfNode(self, node, context):
        res = RTResult()

        for condition, expr, should_return_none in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res
            
            if condition_value.is_true():
                expr_value = res.register(self.visit(expr, context))
                if res.should_return():
                    return res
                return res.success(Number.none if should_return_none else expr_value)
        
        if node.else_case:
            expr, should_return_none = node.else_case
            else_value = res.register(self.visit(expr, context))
            if res.should_return():
                return res
            return res.success(Number.none if should_return_none else else_value)
        
        return res.success(Number.none)
    
    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return(): return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return(): return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.should_return(): return res
        else:
            step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i < end_value.value
        else:
            condition = lambda: i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_token.value, Number(i))

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and not (res.loop_should_continue or res.loop_should_break):
                return res

            if res.loop_should_continue:
                res.loop_should_continue = False
                i += step_value.value
                continue

            if res.loop_should_break:
                res.loop_should_break = False
                break

            elements.append(value)
            i += step_value.value

        return res.success(
            Number.none if node.should_return_none else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )


    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res
            
            if not condition.is_true():
                break

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res
            
            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)
            
        return res.success(
            Number.none if node.should_return_none else
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_FuncDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_token.value if node.var_name_token else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_tokens]
        func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)

        if node.var_name_token:
            context.symbol_table.set(func_name, func_value)
        
        return res.success(func_value)
    
    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res
        
        return_value = res.register(value_to_call.execute(args))
        if res.should_return():
            return res
        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)
    
    def visit_ReturnNode(self, node, context):
        res = RTResult()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
            return res.success_return(value)
        
        return res.success_return(Number.none)
    
    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()
    
    def visit_BreakNode(self, node, context):
        return RTResult().success_break()

##################################
# BUILT-IN VALUES
##################################

global_symbol_table = SymbolTable()
global_symbol_table.set("none", Number.none)
global_symbol_table.set("True", Number.true)
global_symbol_table.set("False", Number.false)
global_symbol_table.set("math_pi", Number.math_pi)

##################################

global_symbol_table.set("print", BuiltInFunction.print)
global_symbol_table.set("print_return", BuiltInFunction.print_return)
global_symbol_table.set("input", BuiltInFunction.input)
global_symbol_table.set("input_int", BuiltInFunction.input_int)
global_symbol_table.set("clear", BuiltInFunction.clear)
global_symbol_table.set("cls", BuiltInFunction.clear)
global_symbol_table.set("is_num", BuiltInFunction.is_num)
global_symbol_table.set("is_str", BuiltInFunction.is_str)
global_symbol_table.set("is_list", BuiltInFunction.is_list)
global_symbol_table.set("is_func", BuiltInFunction.is_func)
global_symbol_table.set("append", BuiltInFunction.append)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("extend", BuiltInFunction.extend)

##################################
# RUN
##################################

def run(file_name, text):
    # Generate tokens
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    # Generate abstract syntax tree(AST)
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error
    
    # Run program
    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error


