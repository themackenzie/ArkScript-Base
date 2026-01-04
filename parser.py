class VarDeclNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __repr__(self):
        return f'VarDecl({self.name}={repr(self.value)})'

class CountCommand:
    def __init__(self, source_var, range_start, range_end):
        self.source_var = source_var
        self.range_start = range_start
        self.range_end = range_end
    def __repr__(self):
        return f'Count({self.source_var}, {self.range_start}:{self.range_end})'
        
class SearchCommand:
    def __init__(self, search_term, target, search_term_is_var, target_is_var, sensitivity='sin'):
        self.search_term = search_term
        self.target = target
        self.search_term_is_var = search_term_is_var
        self.target_is_var = target_is_var
        self.sensitivity = sensitivity
    def __repr__(self):
        return f'Search(term={repr(self.search_term)}, target={repr(self.target)}, sens={self.sensitivity})'



class EnumerateCommand:
    def __init__(self, source, source_is_var, start_num, end_num, source_doc, source_is_var_doc, target_file, target_is_var):
        self.source = source
        self.source_is_var = source_is_var
        self.start_num = start_num
        self.end_num = end_num
        self.source_doc = source_doc         
        self.source_is_var_doc = source_is_var_doc
        self.target_file = target_file       
        self.target_is_var = target_is_var
    def __repr__(self):
        return f'ENUMERAR(src={repr(self.source)}, range={self.start_num}-{self.end_num}, read={repr(self.source_doc)}, write={repr(self.target_file)})'


class FusionCommand:
    def __init__(self, doc1, doc2, separator, output, doc1_is_var, doc2_is_var, separator_is_var, output_is_var):
        self.doc1 = doc1
        self.doc2 = doc2
        self.separator = separator
        self.output = output
        self.doc1_is_var = doc1_is_var
        self.doc2_is_var = doc2_is_var
        self.separator_is_var = separator_is_var
        self.output_is_var = output_is_var
    def __repr__(self):
        return f'Fusion(doc1={repr(self.doc1)}, doc2={repr(self.doc2)}, sep={repr(self.separator)}, out={repr(self.output)})'


class ExtractCommand:
    def __init__(self, source_file, source_is_var, start_page, end_page, target_file, target_is_var):
        self.source_file = source_file
        self.source_is_var = source_is_var
        self.start_page = start_page 
        self.end_page = end_page     
        self.target_file = target_file
        self.target_is_var = target_is_var
    def __repr__(self):
        return f'EXTRAER(src={repr(self.source_file)}, pages={self.start_page}:{self.end_page}, target={repr(self.target_file)})'



class ReplaceOverwriteCommand:
    def __init__(self, command_type, replace_range, original, new, source_doc, target_doc, frequency=1, 
                 original_is_var=False, new_is_var=False, source_is_var=False, target_is_var=False):
        self.command_type = command_type
        self.replace_range = replace_range
        self.original = original
        self.new = new
        self.source_doc = source_doc
        self.target_doc = target_doc
        self.frequency = frequency
        self.original_is_var = original_is_var
        self.new_is_var = new_is_var
        self.source_is_var = source_is_var
        self.target_is_var = target_is_var
    def __repr__(self):
        return f'{self.command_type.upper()}(orig={repr(self.original)}, new={repr(self.new)}, src={repr(self.source_doc)}, target={repr(self.target_doc)}, range={self.replace_range}, freq={self.frequency})'


class FragmentCommand:
    def __init__(self, source_file, source_is_var, delimiter, delimiter_is_var, target_base_name, target_is_var):
        self.source_file = source_file
        self.source_is_var = source_is_var
        self.delimiter = delimiter
        self.delimiter_is_var = delimiter_is_var
        self.target_base_name = target_base_name
        self.target_is_var = target_is_var
    def __repr__(self):
        return f'FRAGMENTAR(src={repr(self.source_file)}, delim={repr(self.delimiter)}, base={repr(self.target_base_name)})'



class InvertCommand:
    def __init__(self, source_file, source_is_var, target_file, target_is_var):
        self.source_file = source_file
        self.source_is_var = source_is_var
        self.target_file = target_file
        self.target_is_var = target_is_var
    def __repr__(self):
        return f'INVERTIR(src={repr(self.source_file)}, target={repr(self.target_file)})'



class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = 0
        self.current_token = self.tokens[self.token_index] if self.tokens else None

    def error(self, expected_types=None):
        token_info = f"Tipo: {self.current_token.type}, Valor: '{self.current_token.value}'" if self.current_token and self.current_token.type != 'EOF' else "Final del archivo"
        msg = f"Error de sintaxis en el token {self.token_index} ({token_info})."
        if expected_types:
            msg += f" Se esperaba uno de: {', '.join(expected_types)}"
        raise Exception(msg)

    def consume(self, token_type=None):
        if token_type is not None and (self.current_token is None or self.current_token.type != token_type):
            self.error([token_type] if token_type else None)
        
        token = self.current_token
        self.token_index += 1
        self.current_token = self.tokens[self.token_index] if self.token_index < len(self.tokens) else None
        return token


    def _parse_string_or_identifier(self):
        """Analiza un valor que puede ser una cadena literal (STRING) o una variable (IDENTIFIER)."""
        is_var = False
        if self.current_token and self.current_token.type == 'STRING':
            source = self.consume('STRING').value
        elif self.current_token and self.current_token.type == 'IDENTIFIER':
            source = self.consume('IDENTIFIER').value
            is_var = True
        else:
            self.error(['STRING', 'IDENTIFIER']) 
        return source, is_var
    
    
    def parse_program(self):
        nodes = []
        while self.current_token and self.current_token.type != 'EOF':
            
            
            if self.current_token.type == 'KW_VAR':
                nodes.extend(self.parse_var_declaration())
            elif self.current_token.type == 'KW_BUSCAR':
                nodes.append(self.parse_search_command())
            elif self.current_token.type == 'KW_FUSIONAR':
                nodes.append(self.parse_fusion_command())
            elif self.current_token.type in ('KW_REEMPLAZAR', 'KW_SOBREESCRIBIR'):
                nodes.append(self.parse_replace_overwrite_command())
            elif self.current_token.type == 'KW_ENUMERAR':
                nodes.append(self.parse_enumerate_command()) 
            elif self.current_token.type == 'KW_CONTAR':
                 self.error(['Comando CONTAR no implementado.'])
            elif self.current_token.type == 'KW_INVERTIR':  
                nodes.append(self.parse_invert_command())   
            elif self.current_token.type == 'KW_EXTRAER': 
                nodes.append(self.parse_extract_command()) 
            elif self.current_token.type == 'KW_FRAGMENTAR': 
                nodes.append(self.parse_fragment_command())   
            else:
                self.error(['KW_VAR', 'Comando'])
            
            
            if self.current_token and self.current_token.type == 'COMMA':
                self.consume('COMMA')
        
        return nodes

    
    def parse_var_declaration(self):
        self.consume('KW_VAR')
        declarations = []
        
        if self.current_token is None or self.current_token.type != 'IDENTIFIER':
            self.error(['IDENTIFIER'])
        
        var_name = self.consume('IDENTIFIER').value
        self.consume('EQUALS')
        
        if self.current_token.type == 'STRING':
            var_value = self.consume('STRING').value
        elif self.current_token.type == 'IDENTIFIER':
            var_value = self.consume('IDENTIFIER').value 
        else:
            self.error(['STRING', 'IDENTIFIER'])

        declarations.append(VarDeclNode(var_name, var_value))
        
        if self.current_token and self.current_token.type not in ('COMMA', 'EOF', 'KW_BUSCAR', 'KW_FUSIONAR', 'KW_REEMPLAZAR', 'KW_SOBREESCRIBIR', 'KW_ENUMERAR'):
             self.error(['COMMA', 'Inicio de Comando'])

        return declarations


    def parse_fragment_command(self):
        

        self.consume('KW_FRAGMENTAR')
        self.consume('KW_DE')
        
        
        source_file, source_is_var = self._parse_string_or_identifier()

        self.consume('KW_POR')
        
        
        delimiter, delimiter_is_var = self._parse_string_or_identifier()
        
        self.consume('KW_EN')
        
        
        target_base_name, target_is_var = self._parse_string_or_identifier()
        
        return FragmentCommand(
            source_file, source_is_var,
            delimiter, delimiter_is_var,
            target_base_name, target_is_var
        )



    def parse_extract_command(self):
        

        self.consume('KW_EXTRAER')
        self.consume('KW_DE')
        
        
        source_file, source_is_var = self._parse_string_or_identifier()

        self.consume('KW_DESDE')
        
        
        start_token = self.consume('NUMBER')
        
        self.consume('KW_HASTA')
        
        
        end_token = self.consume('NUMBER')

        self.consume('KW_EN')
        
        
        target_file, target_is_var = self._parse_string_or_identifier()
        
        return ExtractCommand(
            source_file, source_is_var,
            start_token.value, end_token.value,
            target_file, target_is_var
        )


    def parse_invert_command(self):
        

        self.consume('KW_INVERTIR')
        self.consume('KW_DE')
        
        
        source_file, source_is_var = self._parse_string_or_identifier()

        self.consume('KW_EN')
        
        
        target_file, target_is_var = self._parse_string_or_identifier()
        
        return InvertCommand(
            source_file, source_is_var,
            target_file, target_is_var
        )



    def parse_enumerate_command(self):
        
        
        self.consume('KW_ENUMERAR')
        
        
        source, source_is_var = self._parse_string_or_identifier()
        
        self.consume('KW_DESDE')
        
        
        start_num = self.current_token.value
        self.consume('NUMBER')
        
        self.consume('KW_HASTA')
        
        
        end_num = self.current_token.value
        self.consume('NUMBER')
        
        self.consume('KW_DE')
        
        
        source_doc, source_is_var_doc = self._parse_string_or_identifier()
        
        self.consume('KW_EN')
        
        
        target_file, target_is_var = self._parse_string_or_identifier()
        
        return EnumerateCommand(
            source, source_is_var,
            start_num, end_num,
            source_doc, source_is_var_doc, 
            target_file, target_is_var    
        )
        
        
    def parse_search_command(self):
        
        self.consume('KW_BUSCAR')
        self.consume('KW_REPETICIONES')
        self.consume('KW_DE')
        
        search_term, search_term_is_var = self._parse_string_or_identifier()

        self.consume('KW_DE') 
        target, target_is_var = self._parse_string_or_identifier()

        sensitivity = 'sin'
        
        if self.current_token and self.current_token.type in ['KW_CON', 'KW_SIN']:
            if self.current_token.type == 'KW_CON':
                self.consume('KW_CON')
                self.consume('KW_SENSIBILIDAD')
                sensitivity = 'con'
            elif self.current_token.type == 'KW_SIN':
                self.consume('KW_SIN')
                self.consume('KW_SENSIBILIDAD')
                sensitivity = 'sin'
                
        return SearchCommand(search_term, target, search_term_is_var, target_is_var, sensitivity)


    def parse_fusion_command(self):
        
        self.consume('KW_FUSIONAR')
        
        doc1, doc1_is_var = self._parse_string_or_identifier()
        self.consume('KW_CON')
        doc2, doc2_is_var = self._parse_string_or_identifier()
        
        self.consume('KW_SEP_POR')
        separator, separator_is_var = self._parse_string_or_identifier()

        self.consume('KW_EN')
        output, output_is_var = self._parse_string_or_identifier()

        return FusionCommand(doc1, doc2, separator, output, doc1_is_var, doc2_is_var, separator_is_var, output_is_var)


    def parse_replace_overwrite_command(self):
        
        command_token = self.current_token
        
        if command_token.type == 'KW_REEMPLAZAR':
            self.consume('KW_REEMPLAZAR')
        elif command_token.type == 'KW_SOBREESCRIBIR':
            self.consume('KW_SOBREESCRIBIR')
        
        command_type = command_token.value
        
        
        if self.current_token.type == 'KW_TODO':
            replace_range = self.consume('KW_TODO').value 
        elif self.current_token.type == 'NUMBER':
            replace_range = self.consume('NUMBER').value 
        else:
            self.error(['KW_TODO', 'NUMBER'])

        
        original, original_is_var = self._parse_string_or_identifier()
        self.consume('KW_CON')
        new, new_is_var = self._parse_string_or_identifier()

        
        frequency = 1 
        if self.current_token and self.current_token.type == 'KW_CADA':
            self.consume('KW_CADA')
            frequency = int(self.consume('NUMBER').value)

        
        self.consume('KW_DE') 
        source_doc, source_is_var = self._parse_string_or_identifier()
        
        self.consume('KW_EN')
        target_doc, target_is_var = self._parse_string_or_identifier()

        return ReplaceOverwriteCommand(
            command_type, replace_range, original, new, source_doc, target_doc, frequency,
            original_is_var, new_is_var, source_is_var, target_is_var
        )

    def parse(self):
        return self.parse_program()