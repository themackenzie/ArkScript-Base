import os
import re


try:
    from pypdf import PdfReader, PdfWriter 
except ImportError:
    PdfReader = None
    PdfWriter = None
    print("ADVERTENCIA: La librería PyPDF2 (pypdf) para lectura/escritura de PDF no está disponible.")
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None    
    print("ADVERTENCIA: La librería FPDF para escritura de PDF no está disponible.")
    


from .parser import VarDeclNode, SearchCommand, FusionCommand, ReplaceOverwriteCommand, CountCommand, EnumerateCommand, ExtractCommand, InvertCommand, FragmentCommand 

class Evaluator:
    FILE_DIR = "."  
    
    def __init__(self):
        self.variables = {} 
        self.generated_files = set()
        self.protected_files = set() 

        self.command_handlers = {
            VarDeclNode: self.handle_var_declaration,
            FusionCommand: self.handle_fusion,
            SearchCommand: self.handle_search,
            CountCommand: self.handle_count,
            ReplaceOverwriteCommand: self.handle_replace_overwrite,
            EnumerateCommand: self.handle_enumerate,
            ExtractCommand: self.handle_extract,
            InvertCommand: self.handle_invert,
            FragmentCommand: self.handle_fragment, 
        }


    def get_all_output_files(self):
        return list(self.generated_files)

    def get_protected_files(self):
        return self.protected_files 
        
    def evaluate(self, ast):
        
        print("--- INICIANDO EJECUCIÓN ---")
        for node in ast:
            try:
                handler = self.command_handlers.get(type(node))
                
                if handler:
                    handler(node)
                else:
                    print(f"    Advertencia: Nodo o Comando no manejado: {type(node).__name__}")
            except Exception as e:
                print(f"    Error de Compilación/Ejecución: {e}")
                
        print("\n--- EJECUCIÓN FINALIZADA ---")


    
    
    def handle_var_declaration(self, node: VarDeclNode):
        """Maneja la declaración de variables."""
        self.variables[node.name] = node.value
        print(f"    [VAR]: Variable '{node.name}' declarada con valor '{node.value}'")

    def resolve_file_path(self, file_name):
        return os.path.join(self.FILE_DIR, file_name)

    def resolve_source(self, source, is_var):
        if is_var:
            resolved_value = self.variables.get(source, None)
            if resolved_value is None:
                raise Exception(f"Variable '{source}' no definida.")
            return resolved_value
        return source

    def _read_content(self, file_name, file_path, allow_pdf_text=True):
        """Lee el contenido de un archivo, manejando TXT y PDF (solo si allow_pdf_text es True)."""
        file_extension = file_name.lower().split('.')[-1]
        content = None
        
        try:
            if file_extension == 'pdf':
                if not allow_pdf_text:
                    
                    return None, True 
                
                if PdfReader is None:
                    print(f"    ERROR de Lectura: No se puede leer PDF '{file_name}'. La librería PyPDF2 no está disponible.")
                    return None
                
                reader = PdfReader(file_path)
                text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
                content = "\n".join(text_parts)
                print(f"    [LECTURA]: Contenido de texto extraído de PDF '{file_name}'.")
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return content
            
        except FileNotFoundError:
            print(f"    ERROR de Archivo: Archivo no encontrado: '{file_name}'.")
            return None
        except Exception as e:
            print(f"    ERROR de Lectura: Fallo al leer '{file_name}': {type(e).__name__}: {e}")
            return None


    def _prepare_modification_command(self, command):
        """
        Resuelve variables de entrada para los comandos de modificación (REEMPLAZAR/SOBREESCRIBIR)
        y lee el contenido del archivo fuente.
        """
        try:
            
            
            source_doc_name = self.resolve_source(command.source_doc, command.source_is_var)
            
            
            original_term = self.resolve_source(command.original, command.original_is_var)
            new_term = self.resolve_source(command.new, command.new_is_var)
            
            
            
            target_file_name = self.resolve_source(command.target_doc, command.target_is_var)

            source_doc_path = self.resolve_file_path(source_doc_name)
            target_file_path = self.resolve_file_path(target_file_name)

            
            
            content = self._read_content(source_doc_name, source_doc_path)

            if content is None:
                
                return None, None, None, None, None

            return (content, original_term, new_term, 
                    target_file_name, target_file_path)

        except Exception as e:
            
            raise Exception(f"Fallo en la resolución de variables del comando de modificación: {e}")



    def _write_output(self, content, target_file_name, target_file_path, command_name, binary_mode=False):
        """Maneja la escritura del contenido (texto o binario para PDF)."""
        
        mode = 'wb' if binary_mode else 'w'
        encoding = None if binary_mode else 'utf-8'

        if target_file_name.lower().endswith('.pdf') and not binary_mode:
            
            if FPDF is None:
                print(f"    ERROR [{command_name}]: No se puede generar PDF (texto). La librería FPDF no está disponible.")
                return

            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 8, content.encode('latin-1', 'replace').decode('latin-1'))  
                pdf.output(target_file_path, dest='F')
                self.generated_files.add(target_file_name)  
                print(f"    [{command_name}]: Archivo PDF (texto) '{target_file_name}' generado exitosamente.")
                return
            except Exception as e:
                print(f"    ERROR [{command_name}]: Al generar PDF (texto): {type(e).__name__}: {e}")
                return
        
        
        try:
            with open(target_file_path, mode, encoding=encoding) as fout:
                if binary_mode:
                    fout.write(content)
                else:
                    fout.write(content)
            
            self.generated_files.add(target_file_name)  
            print(f"    [{command_name}]: Archivo '{target_file_name}' creado exitosamente.")

        except Exception as e:
            print(f"    ERROR [{command_name}]: Al escribir el archivo: {e}")

    

    

    

    

    def handle_fragment(self, command: FragmentCommand):
        """
        Fragmenta un archivo de texto en múltiples archivos usando un delimitador.
        """
        print(f"    [FRAGMENTAR]: Procesando fragmentación de '{command.source_file}'...")

        
        try:
            source_file_name = self.resolve_source(command.source_file, command.source_is_var)
            delimiter = self.resolve_source(command.delimiter, command.delimiter_is_var)
            target_base_name = self.resolve_source(command.target_base_name, command.target_is_var)
            
        except Exception as e:
            print(f"    ERROR de Parámetro: {e}")
            return
            
        
        if source_file_name.lower().endswith('.pdf'):
            print("    ERROR [FRAGMENTAR]: El archivo fuente debe ser TXT, no PDF.")
            return

        source_file_path = self.resolve_file_path(source_file_name)
        content = self._read_content(source_file_name, source_file_path)
        
        if content is None:
            return

        if not delimiter:
            print("    ERROR [FRAGMENTAR]: El delimitador no puede estar vacío.")
            return

        
        
        fragments = content.split(delimiter)
        
        
        base_name, ext = os.path.splitext(target_base_name)
        
        
        generated_names = [] 
        
        
        fragment_count = 0
        for i, fragment in enumerate(fragments):
            
            
            
            
            
            
            
            if fragment.strip() == "":
                
                
                continue 
            
            fragment_count += 1
            
            
            target_file_name = f"{base_name}{fragment_count}{ext}"
            target_file_path = self.resolve_file_path(target_file_name)
            
            
            
            final_fragment_content = fragment
            
            
            
            
            if i < len(fragments) - 1:
                
                
                final_fragment_content = fragment.strip() + f"\n{delimiter}\n"
            else:
                
                final_fragment_content = fragment.rstrip() 
            
            
            
            self._write_output(final_fragment_content, target_file_name, target_file_path, "FRAGMENTAR")
            generated_names.append(target_file_name) 

        if fragment_count > 0:
            print(f"    [FRAGMENTAR]: '{source_file_name}' fragmentado exitosamente.")
            
            
            print("    [FRAGMENTAR] Archivos generados:")
            for name in generated_names:
                print(f"        -> {name}")
        else:
            print("    ADVERTENCIA [FRAGMENTAR]: No se generó ningún archivo. El delimitador no fue encontrado o el archivo estaba vacío.")


    


    

    def handle_invert(self, command: InvertCommand):
        """Invierte el orden de las páginas de un PDF."""
        print(f"    [INVERTIR]: Procesando inversión de '{command.source_file}'...")
        try:
            source_file_name = self.resolve_source(command.source_file, command.source_is_var)
            target_file_name = self.resolve_source(command.target_file, command.target_is_var)
            source_file_path = self.resolve_file_path(source_file_name)
            target_file_path = self.resolve_file_path(target_file_name)
        except Exception as e:
            print(f"    ERROR de Parámetro: {e}")
            return
            
        if not (source_file_name.lower().endswith('.pdf') and target_file_name.lower().endswith('.pdf')):
            print("    ERROR [INVERTIR]: Los archivos fuente y destino deben ser PDF.")
            return

        if PdfReader is None or PdfWriter is None:
            print("    ERROR [INVERTIR]: Las librerías PyPDF2 (pypdf) son necesarias.")
            return

        try:
            reader = PdfReader(source_file_path)
            total_pages = len(reader.pages)
            if total_pages == 0:
                print(f"    ADVERTENCIA [INVERTIR]: El archivo '{source_file_name}' está vacío. No se realizó ninguna acción.")
                return

            writer = PdfWriter()
            for i in range(total_pages - 1, -1, -1):
                writer.add_page(reader.pages[i])
            
            with open(target_file_path, 'wb') as fout:
                writer.write(fout)
            
            self.generated_files.add(target_file_name) 
            print(f"    [INVERTIR]: {total_pages} páginas invertidas y guardadas en '{target_file_name}'.")
                
        except FileNotFoundError:
            print(f"    ERROR de Archivo: Archivo fuente no encontrado: '{source_file_name}'.")
        except Exception as e:
            print(f"    ERROR de Inversión: Fallo al procesar '{source_file_name}': {type(e).__name__}: {e}")


    def handle_extract(self, command: ExtractCommand):
        
        print(f"    [EXTRAER]: Procesando extracción de '{command.source_file}'...")
        try:
            source_file_name = self.resolve_source(command.source_file, command.source_is_var)
            target_file_name = self.resolve_source(command.target_file, command.target_is_var)
            source_file_path = self.resolve_file_path(source_file_name)
            target_file_path = self.resolve_file_path(target_file_name)
            start_page = int(command.start_page)
            end_page = int(command.end_page)
            start_index = start_page - 1 
            end_index = end_page - 1
        except Exception as e:
            print(f"    ERROR de Parámetro: {e}")
            return
            
        if not source_file_name.lower().endswith('.pdf'):
            print("    ERROR [EXTRAER]: El archivo fuente debe ser un PDF.")
            return

        if PdfReader is None or PdfWriter is None:
            print("    ERROR [EXTRAER]: Las librerías PyPDF2 (pypdf) son necesarias.")
            return

        try:
            reader = PdfReader(source_file_path)
            total_pages = len(reader.pages)

            if start_index < 0 or end_index >= total_pages or start_index > end_index:
                print(f"    ERROR [EXTRAER]: Rango de páginas no válido ({start_page} a {end_page}). El documento tiene {total_pages} páginas.")
                return

            if target_file_name.lower().endswith('.pdf'):
                writer = PdfWriter()
                for i in range(start_index, end_index + 1):
                    writer.add_page(reader.pages[i]) 
                
                with open(target_file_path, 'wb') as fout:
                    writer.write(fout)
                
                self.generated_files.add(target_file_name) 
                print(f"    [EXTRAER]: Páginas {start_page}-{end_page} extraídas a '{target_file_name}' (PDF).")

            else:
                extracted_text = []
                for i in range(start_index, end_index + 1):
                    text = reader.pages[i].extract_text()
                    if text:
                        extracted_text.append(f"--- Página {i + 1} ---\n{text}\n")
                
                final_content = "\n".join(extracted_text)
                self._write_output(final_content, target_file_name, target_file_path, "EXTRAER")
                print(f"    [EXTRAER]: Páginas {start_page}-{end_page} extraídas a '{target_file_name}' (TXT).")
                
        except FileNotFoundError:
            print(f"    ERROR de Archivo: Archivo fuente no encontrado: '{source_file_name}'.")
        except Exception as e:
            print(f"    ERROR de Extracción: Fallo al procesar '{source_file_name}': {type(e).__name__}: {e}")

    

    def handle_enumerate(self, command: EnumerateCommand):
        """Enumera las ocurrencias de un término con una secuencia numérica, leyendo de un archivo y escribiendo en otro."""
        print(f"    [ENUMERAR]: Procesando enumeración...")
        
        try:
            source_term = self.resolve_source(command.source, command.source_is_var)
            
            
            source_file_name = self.resolve_source(command.source_doc, command.source_is_var_doc) 
            source_file_path = self.resolve_file_path(source_file_name)
            
            
            target_file_name = self.resolve_source(command.target_file, command.target_is_var)
            target_file_path = self.resolve_file_path(target_file_name)
            
            start = int(command.start_num)
            end = int(command.end_num)
            
        except Exception as e:
            print(f"    ERROR de Parámetro: {e}")
            return
            
        
        content = self._read_content(source_file_name, source_file_path)
        if content is None: return

        if start <= end:
            sequence = [str(i) for i in range(start, end + 1)]
            step_name = "ascendente"
        else:
            sequence = [str(i) for i in range(start, end - 1, -1)]
            step_name = "descendente"
            
        if not sequence:
            print(f"    ADVERTENCIA: Rango de enumeración vacío ({start} a {end}).")
            
            self._write_output(content, target_file_name, target_file_path, "ENUMERAR")
            return 
        
        print(f"    [ENUMERAR]: Secuencia {step_name} de {len(sequence)} números generada.")
        parts = content.split(source_term)
        num_replacements = len(parts) - 1
        
        if num_replacements == 0:
            print(f"    [ENUMERAR]: No se encontró el término '{source_term}' en '{source_file_name}'.")
            
            self._write_output(content, target_file_name, target_file_path, "ENUMERAR")
            return
            
        new_content_list = [parts[0]]
        
        for i, part in enumerate(parts[1:]):
            sequence_index = i % len(sequence)
            replacement_number = sequence[sequence_index]
            new_content_list.append(replacement_number)
            new_content_list.append(part)
        
        new_content = "".join(new_content_list)
        
        
        self._write_output(new_content, target_file_name, target_file_path, "ENUMERAR")
        
        if num_replacements > 0:
            print(f"    [ENUMERAR]: {num_replacements} ocurrencias de '{source_term}' reemplazadas secuencialmente y guardadas en '{target_file_name}'.")
    

    def handle_fusion(self, command: FusionCommand):
        
        doc1_name = self.resolve_source(command.doc1, command.doc1_is_var)
        doc2_name = self.resolve_source(command.doc2, command.doc2_is_var)
        separator = self.resolve_source(command.separator, command.separator_is_var)  
        output_file = self.resolve_source(command.output, command.output_is_var)
        
        path1 = self.resolve_file_path(doc1_name)
        path2 = self.resolve_file_path(doc2_name)
        output_path = self.resolve_file_path(output_file)

        print(f"    [FUSIONAR]: '{doc1_name}' con '{doc2_name}' separador: '{separator[:20]}...' en '{output_file}'")
        
        content1 = self._read_content(doc1_name, path1)
        content2 = self._read_content(doc2_name, path2)

        if content1 is None or content2 is None:
              print("    ERROR: La fusión no pudo completarse debido a errores de lectura de archivos.")
              return
            
        fused_content = content1.strip() + "\n\n" + separator + "\n\n" + content2.strip()
        self._write_output(fused_content, output_file, output_path, "FUSIONAR")


    def handle_search(self, command: SearchCommand):
        
        search_term = self.resolve_source(command.search_term, command.search_term_is_var) 
        target_name = self.resolve_source(command.target, command.target_is_var) 
        file_path = self.resolve_file_path(target_name)
        sensitive = 'si' if command.sensitivity == 'con' else 'no' 

        content = self._read_content(target_name, file_path)
        if content is None: return
            
        count = 0
        if sensitive == 'si':
            count = content.count(search_term)
        else: 
            count = content.lower().count(search_term.lower()) 

        print(f"    [BUSCAR]: Se encontraron {count} repeticiones de '{search_term}' en '{target_name}' (Sensible: {sensitive}).")

    def handle_count(self, command: CountCommand):
        
        source_name = self.variables.get(command.source_var)
        file_path = self.resolve_file_path(source_name)
        
        print(f"    [CONTAR]: Contando frecuencia en '{source_name}' de {command.range_start} a {command.range_end}...")

        content = self._read_content(source_name, file_path)
        if content is None: return

        total_chars = len(content)
        
        if command.range_start <= total_chars <= command.range_end:
             print(f"    RESULTADO: El archivo tiene {total_chars} caracteres. Está DENTRO del rango [{command.range_start}:{command.range_end}].")
        else:
             print(f"    RESULTADO: El archivo tiene {total_chars} caracteres. Está FUERA del rango [{command.range_start}:{command.range_end}].")


    def handle_replace_overwrite(self, command: ReplaceOverwriteCommand):
        
        command_type = command.command_type.upper()
        
        print(f"    [{command_type}]: Procesando en '{command.source_doc}'...")
        
        try:
            (content, original_term, new_term, 
             target_file_name, target_file_path) = self._prepare_modification_command(command)
        except Exception as e:
            print(f"    ERROR al resolver variables de {command_type}: {e}")
            return
            
        if content is None: return
        
        limit = float('inf') if command.replace_range == 'todo' else int(command.replace_range)
        frequency = int(command.frequency)

        if original_term not in content:
            print(f"    [{command_type}]: No se encontraron coincidencias de '{original_term}' en '{target_file_name}'.")
            self._write_output(content, target_file_name, target_file_path, command_type)
            return
            
        replacement_count = 0
        new_content = content
        
        if command_type == 'REEMPLAZAR':
            parts = content.split(original_term)
            new_content_list = [parts[0]]
            match_index = 1
            
            for part in parts[1:]:
                should_replace = (match_index - 1) % frequency == 0
                
                if replacement_count < limit and should_replace:
                    new_content_list.append(new_term)
                    replacement_count += 1
                else:
                    new_content_list.append(original_term) 
                
                new_content_list.append(part)
                match_index += 1
            
            new_content = "".join(new_content_list)
            
        elif command_type == 'SOBREESCRIBIR':
            
            new_term_len = len(new_term)
            original_term_len = len(original_term) 
            temp_content = content
            new_content = ""
            current_search_index = 0
            match_index = 0
            
            print(f"    [SOBREESCRIBIR]: Aplicando modo 'Sobreescribir' (reemplaza {new_term_len} chars por aparición de '{original_term}').")

            while current_search_index < len(temp_content) and replacement_count < limit:
                pos = temp_content.find(original_term, current_search_index)

                if pos == -1:
                    new_content += temp_content[current_search_index:]
                    break

                match_index += 1
                should_replace = (match_index - 1) % frequency == 0

                new_content += temp_content[current_search_index:pos]

                if should_replace:
                    new_content += new_term
                    current_search_index = pos + new_term_len 
                    replacement_count += 1
                else:
                    new_content += original_term
                    current_search_index = pos + original_term_len

            
        self._write_output(new_content, target_file_name, target_file_path, command_type) 
        
        if replacement_count > 0:
            print(f"    [{command_type}]: {replacement_count} modificación(es) realizada(s). Lectura: '{target_file_name}'.")