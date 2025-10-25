##################################
# CONSTANTS
##################################

DIGITS = "0123456789"

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
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)

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

    def advance(self, current_char):
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
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
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
            match self.current_char:
                case " ":
                    self.advance()
                case "\t":
                    self.advance()
                case "+":
                    tokens.append(Token(TT_PLUS))
                    self.advance()
                case "-":
                    tokens.append(Token(TT_MINUS))
                    self.advance()
                case "*":
                    tokens.append(Token(TT_MUL))
                    self.advance()
                case "/":
                    tokens.append(Token(TT_DIV))
                    self.advance()
                case "(":
                    tokens.append(Token(TT_LPAREN))
                    self.advance()
                case ")":
                    tokens.append(Token(TT_RPAREN))
                    self.advance()
                case _ if self.current_char in DIGITS:
                    tokens.append(self.make_number())
                case _:
                    pos_start = self.pos.copy()
                    char = self.current_char
                    self.advance()
                    return [], IllegalCharError(pos_start, self.pos, char)
        return tokens, None

    def make_number(self):
        num_str = ""
        dot_count = 0
        
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
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

##################################
# NODES
##################################

class NumberNode:
    def __init__(self, token):
        self.token = token
    
    def __repr__(self):
        return f"{self.token}"

class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.right_node = right_node
        self.op_token = op_token
    
    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"
       
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
        if self.token_idx < len(self.tokens):
            self.current_token = self.tokens[self.token_idx]
        return self.current_token
    
    ##################################

    def parse(self):
        res = self.expr()
        return res
    
    def factor(self):
        token = self.current_token

        if token.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(token)

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV)) #both term and expr use bin_op()

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def bin_op(self, func, ops):
        left = func()

        while self.current_token.type in ops:
            op_token = self.current_token
            self.advance()
            right = func()
            left = BinOpNode(left, op_token, right)
        
        return left


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

    return ast, None

