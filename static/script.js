
let editor; 
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('files');
const inputFileList = document.getElementById('input-file-list');
const outputFileList = document.getElementById('output-file-list');
const outputElement = document.getElementById('output');

let selectedFiles = []; 
let currentView = 'icon'; 






if (typeof CodeMirror !== 'undefined') {
    CodeMirror.defineMode("arkscript", function() {
        console.log("¡Tokenizador de modo arkscript cargado con éxito! (Usando bucle manual de compatibilidad)"); 
        
        
        const tokenMap = {
            
            "var": "keyword",
            "buscar": "keyword",
            "fusionar": "keyword",
            "reemplazar": "keyword",
            "sobreescribir": "keyword",
            "enumerar": "keyword",
            "extraer": "keyword",
            "invertir": "keyword",
            "fragmentar": "keyword",
            
            
            "separado_por": "builtin",
            "todo": "builtin",
            "con": "builtin",
            "sin": "builtin",
            "desde": "builtin",
            "hasta": "builtin",
            "de": "builtin",
            "en": "builtin",
            "por": "builtin"
        };

        
        const wordRegex = /^[a-zA-Z_][a-zA-Z0-9_]*/;


        return {
            startState: function() {return {inString: false};},
            
            token: function(stream, state) {
                
                
                while (stream.peek() && /\s/.test(stream.peek())) {
                    stream.next();
                }
                if (!stream.peek()) return null; 


                
                if (stream.match("//")) {
                    stream.skipToEnd();
                    return "comment";
                }
                
                
                if (stream.peek() === '"') {
                    stream.next(); 
                    
                    stream.skipTo('"') || stream.skipToEnd();
                    stream.next(); 
                    return "string";
                }

                
                if (stream.match(/^[0-9]+/)) {
                    return "number";
                }
                
                
                if (stream.match(wordRegex)) {
                    const word = stream.current();
                    const tokenType = tokenMap[word];
                    
                    if (tokenType) {
                        return tokenType; 
                    }
                    
                    return "variable"; 
                }
                
                
                stream.next();
                return null;
            }
        };
    });
}







function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase(); 
    if (extension === 'pdf') {
        return 'fas fa-file-pdf'; 
    }
    return 'fas fa-file-alt'; 
}


function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    document.getElementById(`content-${tabName}`).style.display = 'block';
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    updateInputFileList(selectedFiles);
    
    updateOutputFileList(outputFileList.dataset.filenames ? JSON.parse(outputFileList.dataset.filenames) : [], true); 
}

function toggleView(viewName) {
    currentView = viewName;
    document.querySelectorAll('.view-button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`view-${viewName}-btn`).classList.add('active');

    const lists = [inputFileList, outputFileList];
    lists.forEach(list => {
        list.classList.remove('icon-view', 'list-view');
        list.classList.add(`${viewName}-view`);
    });
    
    
    updateInputFileList(selectedFiles);
    updateOutputFileList(outputFileList.dataset.filenames ? JSON.parse(outputFileList.dataset.filenames) : [], true); 
}

function updateInputFileList(filenames) {
    inputFileList.innerHTML = '';
    inputFileList.classList.remove('icon-view', 'list-view');
    inputFileList.classList.add(`${currentView}-view`);

    if (filenames.length === 0) {
        inputFileList.innerHTML = '<li style="padding: 10px; color: #888;">No hay archivos cargados.</li>';
        return;
    }

    filenames.forEach(name => {
        const li = document.createElement('li');
        li.className = 'file-item';
        
        const iconClass = currentView === 'icon' ? 'file-icon-large' : 'file-icon-small';
        const fileIcon = getFileIcon(name); 
        li.innerHTML = `
            <i class="${fileIcon} ${iconClass}"></i>
            <span class="file-name">${name}</span>
        `;
        inputFileList.appendChild(li);
    });
}

function updateOutputFileList(filenames, isRerender = false) {
    if (!isRerender) {
        
        outputFileList.dataset.filenames = JSON.stringify(filenames); 
    }
    
    outputFileList.innerHTML = '';
    outputFileList.classList.remove('icon-view', 'list-view');
    outputFileList.classList.add(`${currentView}-view`);
    
    if (filenames.length === 0) {
        outputFileList.innerHTML = '<li style="padding: 10px; color: #888;">No hay archivos generados.</li>';
        return;
    }

    filenames.forEach(filename => {
        const li = document.createElement('li');
        li.className = 'file-item output'; 

        const iconClass = currentView === 'icon' ? 'file-icon-large' : 'file-icon-small';
        const fileIcon = getFileIcon(filename); 
        li.innerHTML = `
            <i class="${fileIcon} ${iconClass}"></i>
            <span class="file-name">${filename}</span>
            <a href="/download/${filename}" class="file-download-link" title="Descargar"><i class="fas fa-download"></i></a>
        `;
        outputFileList.appendChild(li);
    });
    
    
    if (!isRerender && filenames.length > 0) {
        showTab('output');
    }
}


async function uploadFiles(files) {
    const formData = new FormData();

    for (const file of files) {
        formData.append('files', file); 
    }
    
    outputElement.textContent = `Subiendo ${files.length} archivo(s) al servidor...`;
    outputElement.className = '';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData 
        });
        const data = await response.json();

        if (data.error) {
            outputElement.textContent = data.output;
            outputElement.className = 'error';
        } else {
            
            selectedFiles = data.current_files || [];

            outputElement.textContent = data.output;
            outputElement.className = 'success';
            
            updateInputFileList(selectedFiles);
            showTab('input');
        }

    } catch (error) {
        outputElement.textContent = `Error de conexión al subir archivos: ${error}`;
        outputElement.className = 'error';
        console.error('Error:', error);
    }
}


function runCode() {
    
    const code = editor.getValue(); 
    const formData = new FormData();
    formData.append('code', code); 
    
    if (selectedFiles.length === 0) {
        outputElement.textContent = 'Error: No se han subido archivos de entrada en el servidor.';
        outputElement.className = 'error';
        return;
    }
    
    outputElement.textContent = 'Ejecutando intérprete...';
    outputElement.className = '';

    fetch('/execute', {
        method: 'POST',
        body: formData 
    })
    .then(response => response.json())
    .then(data => {
        outputElement.textContent = data.output;
        outputElement.className = data.error ? 'error' : 'success';

        const newOutputFiles = data.output_files || [];
        
        
        const oldOutputFiles = outputFileList.dataset.filenames 
            ? JSON.parse(outputFileList.dataset.filenames) 
            : [];
        
        
        const combinedFiles = Array.from(new Set([...oldOutputFiles, ...newOutputFiles]));
        
        
        updateOutputFileList(combinedFiles, false); 
        
        if (!data.error && newOutputFiles.length > 0) {
            outputElement.textContent += `\n\n¡${newOutputFiles.length} archivo(s) de resultado gestionados!`;
        }
    })
    .catch(error => {
        outputElement.textContent = `Error de conexión con el servidor: ${error}`;
        outputElement.className = 'error';
        console.error('Error:', error);
    });
}


function preventDefaults (e) {
    e.preventDefault();
    e.stopPropagation();
}

dropZone.addEventListener('dragenter', highlight, false);
dropZone.addEventListener('dragover', highlight, false);
dropZone.addEventListener('dragleave', unhighlight, false);
dropZone.addEventListener('drop', handleDrop, false);

function highlight() {
    dropZone.classList.add('drag-over');
}

function unhighlight() {
    dropZone.classList.remove('drag-over');
}


function handleDrop(e) {
    unhighlight();
    const dt = e.dataTransfer;
    
    const files = Array.from(dt.files).filter(file => file.name.endsWith('.txt') || file.name.endsWith('.pdf'));
    
    if (files.length > 0) {
        uploadFiles(files); 
    }
}

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    
    const files = Array.from(e.target.files).filter(file => file.name.endsWith('.txt') || file.name.endsWith('.pdf'));
    if (files.length > 0) {
        uploadFiles(files); 
    }
    e.target.value = ''; 
});




async function initializeApp() {
    
    try {
        const response = await fetch('/get_input_files');
        const data = await response.json();
        if (data.current_files) {
            selectedFiles = data.current_files;
        }
    } catch (error) {
        console.error("No se pudo sincronizar la lista de archivos con el servidor.", error);
    }
    
    
    outputFileList.dataset.filenames = JSON.stringify([]); 
    
    
    updateInputFileList(selectedFiles); 
    toggleView('icon'); 
}

document.addEventListener('DOMContentLoaded', () => {
    
    const textarea = document.getElementById('code-editor');
    if (typeof CodeMirror !== 'undefined') {
        editor = CodeMirror.fromTextArea(textarea, {
            lineNumbers: true, 
            mode: "arkscript", 
            theme: "dracula" 
        });
        
        console.log("CodeMirror transformado con modo de estado 'arkscript'.");
        
    } else {
         console.error("ERROR: CodeMirror no está definido.");
    }
    
    
    initializeApp(); 
});
