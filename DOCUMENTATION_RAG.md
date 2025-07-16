# MCP PDF Extract - Documentación Completa para RAG con Contextual Retrieval

## Contexto General del Proyecto

**Nombre del Proyecto**: MCP_pdf_extract  
**Ubicación**: `/Users/edgm/Documents/Projects/AI/MCP_pdf_extract`  
**Propósito**: Servidor MCP (Model Context Protocol) que expone capacidades de lectura de documentos PDF a través de herramientas y recursos estandarizados.  
**Versión Python Requerida**: 3.11 o superior (CRÍTICO: No funcionará con Python 3.9 o inferior)

### Arquitectura del Sistema

El proyecto implementa un servidor MCP que:
1. **Expone herramientas (tools)** para que los clientes MCP puedan ejecutar operaciones
2. **Expone recursos (resources)** para que los clientes MCP puedan acceder a datos
3. **Se comunica via stdio** (entrada/salida estándar) usando el protocolo JSON-RPC 2.0
4. **Lee archivos PDF** de un directorio configurado y extrae su contenido textual

## Estructura de Archivos del Proyecto

```
MCP_pdf_extract/
├── mcp_documents_server.py    # Servidor MCP principal
├── pdf.py                      # Módulo de carga y procesamiento de PDFs
├── app/
│   ├── __init__.py            # Archivo vacío para hacer de app un módulo Python
│   └── exceptions.py          # Definición de excepciones personalizadas
├── data/
│   └── pdfs/                  # Directorio donde se almacenan los PDFs
├── .env                       # Variables de entorno
├── pyproject.toml             # Configuración del proyecto con uv
├── .venv/                     # Entorno virtual (creado con uv venv)
└── README.md                  # Documentación básica
```

## Módulo: app/exceptions.py

**Archivo completo**:
```python
"""Custom exceptions for the MCP PDF Extract application."""


class DocumentLoadError(Exception):
    """Raised when a document cannot be loaded or read."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass
```

**Propósito**: Define excepciones personalizadas para manejo de errores específicos.

**Clases**:
- `DocumentLoadError`: Se lanza cuando un PDF no puede ser cargado o leído
- `ValidationError`: Se lanza cuando la validación de entrada falla

**IMPORTANTE**: Este archivo DEBE existir antes de ejecutar el servidor, ya que `pdf.py` lo importa en la línea 10.

## Módulo: pdf.py

**Propósito**: Maneja toda la lógica de carga, validación y extracción de texto de archivos PDF.

### Clase PDFLoader

```python
class PDFLoader:
    """Handles PDF loading and text extraction."""
```

#### Constructor __init__

```python
def __init__(self):
    """Initialize the PDF loader with configuration."""
    self.max_size_kb = int(os.getenv("MAX_PDF_SIZE_KB", "350"))
    self.pdf_dir = Path(os.getenv("PDF_DIR", "./data/pdfs"))
```

**Funcionamiento**:
1. Lee la variable de entorno `MAX_PDF_SIZE_KB` (default: 350)
2. Lee la variable de entorno `PDF_DIR` (default: "./data/pdfs")
3. Convierte pdf_dir a objeto Path para manejo seguro de rutas

**ERRORES COMUNES**:
- NO hardcodear rutas absolutas
- NO olvidar crear el archivo .env
- NO usar valores no numéricos en MAX_PDF_SIZE_KB

#### Método load_pdf

```python
async def load_pdf(self, filename: str) -> str:
    """Load PDF and extract text asynchronously.
    
    Args:
        filename: PDF filename (without path)
        
    Returns:
        Extracted text from all pages
        
    Raises:
        ValidationError: If filename is invalid or file is too large
        DocumentLoadError: If PDF file doesn't exist or cannot be read
    """
```

**Proceso detallado**:

1. **Validación de seguridad contra path traversal** (líneas 38-39):
   ```python
   if "/" in filename or "\\" in filename:
       raise ValidationError("Invalid filename - path traversal not allowed")
   ```
   CRÍTICO: Nunca permitir paths en el filename

2. **Construcción de ruta y verificación de existencia** (líneas 42-44):
   ```python
   pdf_path = self.pdf_dir / filename
   if not pdf_path.exists():
       raise DocumentLoadError(f"PDF not found: {filename}")
   ```

3. **Validación de extensión** (líneas 47-48):
   ```python
   if not pdf_path.suffix.lower() == ".pdf":
       raise ValidationError(f"File must be a PDF: {filename}")
   ```

4. **Validación de tamaño** (líneas 51-55):
   ```python
   size_kb = pdf_path.stat().st_size / 1024
   if size_kb > self.max_size_kb:
       raise ValidationError(f"PDF too large: {size_kb:.1f}KB > {self.max_size_kb}KB")
   ```

5. **Extracción asíncrona de texto** (líneas 58-78):
   - Define función interna `extract_sync()` porque pdfplumber es síncrono
   - Usa `asyncio.to_thread()` para ejecutar en thread separado
   - Extrae texto de cada página y las une con doble salto de línea

**QUÉ NO HACER**:
- NO usar `await` dentro de `extract_sync()`
- NO abrir el PDF fuera del context manager `with`
- NO ignorar páginas sin texto (puede ser intencional)

#### Método list_available_pdfs

```python
async def list_available_pdfs(self) -> List[str]:
    """List all available PDF files in the configured directory.
    
    Returns:
        List of PDF filenames
    """
```

**Funcionamiento**:
1. Verifica si el directorio existe (retorna lista vacía si no)
2. Usa `glob("*.pdf")` para encontrar solo archivos PDF
3. Extrae solo nombres de archivo con `.name`
4. Retorna lista ordenada alfabéticamente

## Módulo: mcp_documents_server.py

**Propósito**: Implementa el servidor MCP que expone las capacidades de lectura de PDFs.

### Inicialización

```python
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pdf import PDFLoader

mcp = FastMCP("DocumentMCP", log_level="ERROR")
pdf_loader = PDFLoader()
```

**IMPORTANTE**: 
- El nombre "DocumentMCP" identifica al servidor
- log_level="ERROR" reduce el ruido en los logs
- pdf_loader es una instancia global reutilizada

### Herramienta: read_doc_contents

```python
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a PDF document and return it as a string.",
)
async def read_document(
    doc_id: str = Field(description="PDF filename to read"),
):
```

**Propósito**: Permite a clientes MCP leer el contenido completo de un PDF.

**Parámetros**:
- `doc_id`: Nombre del archivo PDF (ejemplo: "reporte.pdf")

**Retorna**: String con el texto extraído del PDF

**Errores**: ValueError con mensaje descriptivo

**Ejemplo de uso desde cliente MCP**:
```json
{
  "tool": "read_doc_contents",
  "arguments": {
    "doc_id": "informe_2024.pdf"
  }
}
```

### Herramienta: list_available_pdfs

```python
@mcp.tool(
    name="list_available_pdfs",
    description="List all available PDF documents that can be read.",
)
async def list_available_pdfs():
```

**Propósito**: Lista todos los PDFs disponibles en formato legible.

**Parámetros**: Ninguno

**Retorna**: 
- String formateado con lista de PDFs si hay archivos
- Mensaje "No PDF files are currently available in the directory." si está vacío

**Formato de salida**:
```
Available PDF files:
- documento1.pdf
- documento2.pdf
- informe_final.pdf
```

### Recurso: docs://documents

```python
@mcp.resource("docs://documents", mime_type="application/json")
async def list_docs() -> list[str]:
    return await pdf_loader.list_available_pdfs()
```

**URI**: `docs://documents`  
**MIME Type**: `application/json`  
**Retorna**: Lista JSON de nombres de archivos PDF

**IMPORTANTE**: Este recurso retorna datos estructurados (lista), no texto formateado.

### Recurso: docs://documents/{doc_id}

```python
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
async def fetch_doc(doc_id: str) -> str:
```

**URI Template**: `docs://documents/{doc_id}`  
**MIME Type**: `text/plain`  
**Parámetro**: `doc_id` - nombre del archivo PDF  
**Retorna**: Contenido textual del PDF

**Ejemplo de URI**: `docs://documents/manual_usuario.pdf`

### Punto de Entrada

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**CRÍTICO**: El servidor usa transporte stdio, NO HTTP. Se comunica via entrada/salida estándar.

## Configuración del Proyecto

### Archivo .env

```
MAX_PDF_SIZE_KB=350
PDF_DIR=./data/pdfs
```

**Variables**:
- `MAX_PDF_SIZE_KB`: Tamaño máximo permitido en KB (350 = 350KB)
- `PDF_DIR`: Ruta al directorio de PDFs (relativa al proyecto)

**IMPORTANTE**: Este archivo DEBE existir aunque uses valores por defecto.

### Archivo pyproject.toml

```toml
[project]
name = "mcp-pdf-extract"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.11.0",
    "pdfplumber>=0.11.7",
    "pydantic>=2.11.7",
    "python-dotenv>=1.1.1",
]
```

**Dependencias críticas**:
- `mcp[cli]`: Framework MCP con herramientas CLI
- `pdfplumber`: Extracción de texto de PDFs
- `pydantic`: Validación de datos y Field
- `python-dotenv`: Carga de variables de entorno

## Proceso de Instalación Completo

### 1. Verificar Python

```bash
python --version
# DEBE ser 3.11 o superior
```

**ERROR COMÚN**: Python 3.9 NO funcionará. El paquete mcp requiere >=3.10.

### 2. Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Clonar y preparar proyecto

```bash
cd /Users/edgm/Documents/Projects/AI
git clone <repository-url> MCP_pdf_extract
cd MCP_pdf_extract
```

### 4. Crear estructura de directorios

```bash
mkdir -p app
mkdir -p data/pdfs
```

**CRÍTICO**: La estructura DEBE existir antes de ejecutar.

### 5. Crear archivos base

**Crear app/__init__.py** (archivo vacío):
```bash
touch app/__init__.py
```

**Crear app/exceptions.py** con el contenido exacto mostrado arriba.

**Crear .env** con las variables mostradas arriba.

### 6. Inicializar proyecto con uv

```bash
uv init --name mcp-pdf-extract --python 3.11
uv venv
uv sync
```

**QUÉ NO HACER**:
- NO usar `pip install` directamente
- NO activar el venv manualmente cuando uses `uv run`
- NO olvidar `uv sync` después de cambios en pyproject.toml

## Ejecución del Servidor

### Ejecución Básica

```bash
uv run python mcp_documents_server.py
```

**Comportamiento esperado**: 
- No muestra output
- Espera entrada JSON-RPC en stdin
- Responde en stdout

### Prueba de Funcionamiento

```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {"roots": {"listChanged": true}, "sampling": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}, "id": 1}' | uv run python mcp_documents_server.py
```

**Respuesta esperada**: JSON con capabilities del servidor.

### Ejecución con MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

En la interfaz web:
- **Command**: `uv`
- **Arguments**: `run --with mcp mcp run mcp_documents_server.py`

**ERROR COMÚN**: Si aparece "uv" command not found, verificar:
1. Que estés en el directorio del proyecto
2. Que uv esté instalado globalmente
3. Que el path esté configurado correctamente

## Integración con Claude Desktop

Editar `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdf-extractor": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/edgm/Documents/Projects/AI/MCP_pdf_extract",
        "run",
        "python",
        "mcp_documents_server.py"
      ],
      "env": {}
    }
  }
}
```

**IMPORTANTE**: Usar ruta absoluta en --directory.

## Errores Comunes y Soluciones

### Error: ModuleNotFoundError: No module named 'mcp'

**Causa**: Python < 3.10 o dependencias no instaladas  
**Solución**: Verificar Python version y ejecutar `uv sync`

### Error: ModuleNotFoundError: No module named 'app.exceptions'

**Causa**: Falta crear el módulo app  
**Solución**: Crear app/__init__.py y app/exceptions.py

### Error: spawn uv ENOENT

**Causa**: Inspector no encuentra el comando uv  
**Solución**: Usar ruta completa o verificar instalación de uv

### Error: PDF not found

**Causa**: No hay PDFs en data/pdfs/  
**Solución**: Agregar archivos PDF al directorio

### Error: Invalid request parameters

**Causa**: Protocolo MCP mal formado  
**Solución**: Usar formato correcto de JSON-RPC 2.0

## Flujo de Ejecución Detallado

1. **Cliente MCP inicia el servidor** via stdio
2. **Cliente envía mensaje initialize** con sus capacidades
3. **Servidor responde** con sus capacidades (tools y resources)
4. **Cliente envía notifications/initialized**
5. **Cliente puede ahora**:
   - Llamar tools con `tools/call`
   - Listar resources con `resources/list`
   - Leer resources con `resources/read`
6. **Servidor procesa** cada request y responde via stdout
7. **Comunicación continúa** hasta que el cliente cierra la conexión

## Validaciones de Seguridad Implementadas

1. **Path Traversal Prevention**: No permite "/" o "\" en nombres de archivo
2. **File Size Validation**: Limita tamaño máximo de PDFs
3. **Extension Validation**: Solo acepta archivos .pdf
4. **Directory Isolation**: Solo lee del directorio configurado
5. **Error Handling**: Nunca expone rutas del sistema en errores

## Testing Manual Completo

### 1. Verificar instalación

```bash
cd /Users/edgm/Documents/Projects/AI/MCP_pdf_extract
uv --version
python --version  # Debe ser >= 3.11
```

### 2. Verificar dependencias

```bash
uv pip list | grep -E "(mcp|pdfplumber|pydantic|dotenv)"
```

### 3. Agregar PDF de prueba

```bash
# Copiar cualquier PDF a data/pdfs/
cp ~/Downloads/ejemplo.pdf data/pdfs/
```

### 4. Probar herramientas

```bash
# Listar PDFs disponibles
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_available_pdfs", "arguments": {}}, "id": 1}' | uv run python mcp_documents_server.py

# Leer un PDF específico
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "read_doc_contents", "arguments": {"doc_id": "ejemplo.pdf"}}, "id": 2}' | uv run python mcp_documents_server.py
```

## Mantenimiento y Extensión

### Para agregar nueva herramienta

```python
@mcp.tool(
    name="nombre_herramienta",
    description="Descripción clara de qué hace",
)
async def mi_herramienta(
    parametro: str = Field(description="Descripción del parámetro"),
):
    # Implementación
    pass
```

### Para agregar nuevo recurso

```python
@mcp.resource("protocol://path/{param}", mime_type="text/plain")
async def mi_recurso(param: str) -> str:
    # Implementación
    pass
```

### Para modificar configuración

1. Agregar variable a .env
2. Leerla en PDFLoader.__init__ con os.getenv()
3. Documentar en README.md

## Notas Finales para RAG

Este documento contiene TODA la información necesaria para ejecutar el proyecto MCP_pdf_extract sin errores. Cada función está documentada con su propósito exacto, parámetros, retornos y errores posibles. Los ejemplos de código son del proyecto real, no inventados. Las rutas y configuraciones son las exactas del sistema donde se desarrolló.

**Palabras clave para búsqueda**: MCP, PDF, FastMCP, pdfplumber, Model Context Protocol, stdio, JSON-RPC, Python 3.11, uv, DocumentMCP, PDFLoader, read_doc_contents, list_available_pdfs

**Contexto de ejecución**: macOS, Python 3.11, uv como gestor de paquetes, directorio base /Users/edgm/Documents/Projects/AI/MCP_pdf_extract