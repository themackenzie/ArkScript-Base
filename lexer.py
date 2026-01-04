class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f'{self.type}:{repr(self.value)}'

class Lexer:
    
    KEYWORDS = {
        
        'var': 'KW_VAR',      
        
        
        'con': 'KW_CON', 
        'sin': 'KW_SIN',     
        'de': 'KW_DE',
        'por': 'KW_POR',
        'en': 'KW_EN',
        
        'desde': 'KW_DESDE',    
        'hasta': 'KW_HASTA',    
        
        
        'buscar': 'KW_BUSCAR',
        'fusionar': 'KW_FUSIONAR',
        'reemplazar': 'KW_REEMPLAZAR',
        'sobreescribir': 'KW_SOBREESCRIBIR',
        'enumerar': 'KW_ENUMERAR',
        'contar': 'KW_CONTAR',
        'extraer': 'KW_EXTRAER',
        'invertir': 'KW_INVERTIR',
        'fragmentar': 'KW_FRAGMENTAR', 
        
        
        'repeticiones': 'KW_REPETICIONES',
        'sensibilidad': 'KW_SENSIBILIDAD',
        'separado_por': 'KW_SEP_POR',    
        'cada': 'KW_CADA',             
        'todo': 'KW_TODO',             
    }
    
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None

    def error(self, msg="Error léxico"):
        raise Exception(f'{msg} cerca de la posición {self.pos}. Carácter: {repr(self.current_char)}')

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """Ignora todo el texto hasta el final de la línea si ve '//'."""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
        self.advance()
        return Token('COMMENT')

    def _id(self):
        """Maneja Identificadores y Palabras Clave."""
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
            
        
        token_type = self.KEYWORDS.get(result.lower(), 'IDENTIFIER') 
        return Token(token_type, result)

    def _string(self):
        """Maneja Literales de Cadena."""
        self.advance()
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        if self.current_char != '"':
             self.error("Literal de cadena sin cerrar")
        self.advance()
        return Token('STRING', result)

    def _number(self):
        """Maneja números."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token('NUMBER', int(result))

    def tokenize(self):
        tokens = []
        while self.current_char is not None:
            
            self.skip_whitespace()
            if self.current_char is None: break

            
            if self.current_char == '/' and self.peek() == '/':
                self.advance() 
                self.advance() 
                tokens.append(self.skip_comment())
                continue

            if self.current_char.isalpha():
                tokens.append(self._id())
                continue

            if self.current_char.isdigit():
                tokens.append(self._number())
                continue

            if self.current_char == '"':
                tokens.append(self._string())
                continue

            
            if self.current_char == ',': tokens.append(Token('COMMA')); self.advance(); continue
            if self.current_char == '=': tokens.append(Token('EQUALS')); self.advance(); continue
            
            self.error(f'Carácter no reconocido: {repr(self.current_char)}')
            
        tokens.append(Token('EOF'))
        return [t for t in tokens if t.type != 'COMMENT']