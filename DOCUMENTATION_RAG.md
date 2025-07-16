# MCP PDF Extract - Complete Documentation for RAG with Contextual Retrieval

## General Project Context

**Project Name**: MCP_pdf_extract  
**Location**: `/Users/edgm/Documents/Projects/AI/MCP_pdf_extract`  
**Purpose**: MCP (Model Context Protocol) server that exposes PDF document reading capabilities through standardized tools and resources.  
**Required Python Version**: 3.11 or higher (CRITICAL: Will not work with Python 3.9 or lower)

### System Architecture

The project implements an MCP server that:
1. **Exposes tools** for MCP clients to execute operations
2. **Exposes resources** for MCP clients to access data
3. **Communicates via stdio** (standard input/output) using JSON-RPC 2.0 protocol
4. **Reads PDF files** from a configured directory and extracts their textual content

## Project File Structure

```
MCP_pdf_extract/
├── mcp_documents_server.py    # Main MCP server
├── pdf.py                      # PDF loading and processing module
├── app/
│   ├── __init__.py            # Empty file to make app a Python module
│   └── exceptions.py          # Custom exception definitions
├── data/
│   └── pdfs/                  # Directory where PDFs are stored
├── .env                       # Environment variables
├── pyproject.toml             # Project configuration with uv
├── .venv/                     # Virtual environment (created with uv venv)
└── README.md                  # Basic documentation
```

## Module: app/exceptions.py

**Full file**:
```python
"""Custom exceptions for the MCP PDF Extract application."""


class DocumentLoadError(Exception):
    """Raised when a document cannot be loaded or read."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass
```

**Purpose**: Defines custom exceptions for specific error handling.

**Classes**:
- `DocumentLoadError`: Raised when a PDF cannot be loaded or read
- `ValidationError`: Raised when input validation fails

**IMPORTANT**: This file MUST exist before running the server, as `pdf.py` imports it on line 10.

## Module: pdf.py

**Purpose**: Handles all logic for loading, validating, and extracting text from PDF files.

### Class PDFLoader

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

**Operation**:
1. Reads environment variable `MAX_PDF_SIZE_KB` (default: 350)
2. Reads environment variable `PDF_DIR` (default: "./data/pdfs")
3. Converts pdf_dir to Path object for safe path handling

**COMMON ERRORS**:
- DO NOT hardcode absolute paths
- DO NOT forget to create the .env file
- DO NOT use non-numeric values in MAX_PDF_SIZE_KB

#### Method load_pdf

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

**Detailed process**:

1. **Security validation against path traversal** (lines 38-39):
   ```python
   if "/" in filename or "\\" in filename:
       raise ValidationError("Invalid filename - path traversal not allowed")
   ```
   CRITICAL: Never allow paths in the filename

2. **Path construction and existence verification** (lines 42-44):
   ```python
   pdf_path = self.pdf_dir / filename
   if not pdf_path.exists():
       raise DocumentLoadError(f"PDF not found: {filename}")
   ```

3. **Extension validation** (lines 47-48):
   ```python
   if not pdf_path.suffix.lower() == ".pdf":
       raise ValidationError(f"File must be a PDF: {filename}")
   ```

4. **Size validation** (lines 51-55):
   ```python
   size_kb = pdf_path.stat().st_size / 1024
   if size_kb > self.max_size_kb:
       raise ValidationError(f"PDF too large: {size_kb:.1f}KB > {self.max_size_kb}KB")
   ```

5. **Asynchronous text extraction** (lines 58-78):
   - Defines internal function `extract_sync()` because pdfplumber is synchronous
   - Uses `asyncio.to_thread()` to execute in separate thread
   - Extracts text from each page and joins them with double line breaks

**WHAT NOT TO DO**:
- DO NOT use `await` inside `extract_sync()`
- DO NOT open the PDF outside the `with` context manager
- DO NOT ignore pages without text (may be intentional)

#### Method list_available_pdfs

```python
async def list_available_pdfs(self) -> List[str]:
    """List all available PDF files in the configured directory.
    
    Returns:
        List of PDF filenames
    """
```

**Operation**:
1. Verifies if directory exists (returns empty list if not)
2. Uses `glob("*.pdf")` to find only PDF files
3. Extracts only filenames with `.name`
4. Returns alphabetically sorted list

## Module: mcp_documents_server.py

**Purpose**: Implements the MCP server that exposes PDF reading capabilities.

### Initialization

```python
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pdf import PDFLoader

mcp = FastMCP("DocumentMCP", log_level="ERROR")
pdf_loader = PDFLoader()
```

**IMPORTANT**: 
- The name "DocumentMCP" identifies the server
- log_level="ERROR" reduces log noise
- pdf_loader is a reusable global instance

### Tool: read_doc_contents

```python
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a PDF document and return it as a string.",
)
async def read_document(
    doc_id: str = Field(description="PDF filename to read"),
):
```

**Purpose**: Allows MCP clients to read the complete content of a PDF.

**Parameters**:
- `doc_id`: PDF file name (example: "report.pdf")

**Returns**: String with text extracted from the PDF

**Errors**: ValueError with descriptive message

**Example usage from MCP client**:
```json
{
  "tool": "read_doc_contents",
  "arguments": {
    "doc_id": "report_2024.pdf"
  }
}
```

### Tool: list_available_pdfs

```python
@mcp.tool(
    name="list_available_pdfs",
    description="List all available PDF documents that can be read.",
)
async def list_available_pdfs():
```

**Purpose**: Lists all available PDFs in readable format.

**Parameters**: None

**Returns**: 
- Formatted string with list of PDFs if files exist
- Message "No PDF files are currently available in the directory." if empty

**Output format**:
```
Available PDF files:
- document1.pdf
- document2.pdf
- final_report.pdf
```

### Resource: docs://documents

```python
@mcp.resource("docs://documents", mime_type="application/json")
async def list_docs() -> list[str]:
    return await pdf_loader.list_available_pdfs()
```

**URI**: `docs://documents`  
**MIME Type**: `application/json`  
**Returns**: JSON list of PDF filenames

**IMPORTANT**: This resource returns structured data (list), not formatted text.

### Resource: docs://documents/{doc_id}

```python
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
async def fetch_doc(doc_id: str) -> str:
```

**URI Template**: `docs://documents/{doc_id}`  
**MIME Type**: `text/plain`  
**Parameter**: `doc_id` - PDF filename  
**Returns**: Textual content of the PDF

**Example URI**: `docs://documents/user_manual.pdf`

### Entry Point

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**CRITICAL**: The server uses stdio transport, NOT HTTP. It communicates via standard input/output.

## Project Configuration

### .env File

```
MAX_PDF_SIZE_KB=350
PDF_DIR=./data/pdfs
```

**Variables**:
- `MAX_PDF_SIZE_KB`: Maximum allowed size in KB (350 = 350KB)
- `PDF_DIR`: Path to PDFs directory (relative to project)

**IMPORTANT**: This file MUST exist even if using default values.

### pyproject.toml File

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

**Critical dependencies**:
- `mcp[cli]`: MCP framework with CLI tools
- `pdfplumber`: Text extraction from PDFs
- `pydantic`: Data validation and Field
- `python-dotenv`: Loading environment variables

## Complete Installation Process

### 1. Verify Python

```bash
python --version
# MUST be 3.11 or higher
```

**COMMON ERROR**: Python 3.9 will NOT work. The mcp package requires >=3.10.

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Clone and prepare project

```bash
cd /Users/edgm/Documents/Projects/AI
git clone <repository-url> MCP_pdf_extract
cd MCP_pdf_extract
```

### 4. Create directory structure

```bash
mkdir -p app
mkdir -p data/pdfs
```

**CRITICAL**: The structure MUST exist before execution.

### 5. Create base files

**Create app/__init__.py** (empty file):
```bash
touch app/__init__.py
```

**Create app/exceptions.py** with the exact content shown above.

**Create .env** with the variables shown above.

### 6. Initialize project with uv

```bash
uv init --name mcp-pdf-extract --python 3.11
uv venv
uv sync
```

**WHAT NOT TO DO**:
- DO NOT use `pip install` directly
- DO NOT manually activate the venv when using `uv run`
- DO NOT forget `uv sync` after changes in pyproject.toml

## Server Execution

### Basic Execution

```bash
uv run python mcp_documents_server.py
```

**Expected behavior**: 
- Shows no output
- Waits for JSON-RPC input on stdin
- Responds on stdout

### Functionality Test

```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {"roots": {"listChanged": true}, "sampling": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}, "id": 1}' | uv run python mcp_documents_server.py
```

**Expected response**: JSON with server capabilities.

### Execution with MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

In the web interface:
- **Command**: `uv`
- **Arguments**: `run --with mcp mcp run mcp_documents_server.py`

**COMMON ERROR**: If "uv" command not found appears, verify:
1. That you're in the project directory
2. That uv is installed globally
3. That the path is configured correctly

## Claude Desktop Integration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**IMPORTANT**: Use absolute path in --directory.

## Common Errors and Solutions

### Error: ModuleNotFoundError: No module named 'mcp'

**Cause**: Python < 3.10 or dependencies not installed  
**Solution**: Verify Python version and run `uv sync`

### Error: ModuleNotFoundError: No module named 'app.exceptions'

**Cause**: Missing app module  
**Solution**: Create app/__init__.py and app/exceptions.py

### Error: spawn uv ENOENT

**Cause**: Inspector can't find uv command  
**Solution**: Use full path or verify uv installation

### Error: PDF not found

**Cause**: No PDFs in data/pdfs/  
**Solution**: Add PDF files to the directory

### Error: Invalid request parameters

**Cause**: Malformed MCP protocol  
**Solution**: Use correct JSON-RPC 2.0 format

## Detailed Execution Flow

1. **MCP client starts the server** via stdio
2. **Client sends initialize message** with its capabilities
3. **Server responds** with its capabilities (tools and resources)
4. **Client sends notifications/initialized**
5. **Client can now**:
   - Call tools with `tools/call`
   - List resources with `resources/list`
   - Read resources with `resources/read`
6. **Server processes** each request and responds via stdout
7. **Communication continues** until client closes the connection

## Implemented Security Validations

1. **Path Traversal Prevention**: Doesn't allow "/" or "\" in filenames
2. **File Size Validation**: Limits maximum PDF size
3. **Extension Validation**: Only accepts .pdf files
4. **Directory Isolation**: Only reads from configured directory
5. **Error Handling**: Never exposes system paths in errors

## Complete Manual Testing

### 1. Verify installation

```bash
cd /Users/edgm/Documents/Projects/AI/MCP_pdf_extract
uv --version
python --version  # Must be >= 3.11
```

### 2. Verify dependencies

```bash
uv pip list | grep -E "(mcp|pdfplumber|pydantic|dotenv)"
```

### 3. Add test PDF

```bash
# Copy any PDF to data/pdfs/
cp ~/Downloads/example.pdf data/pdfs/
```

### 4. Test tools

```bash
# List available PDFs
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_available_pdfs", "arguments": {}}, "id": 1}' | uv run python mcp_documents_server.py

# Read a specific PDF
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "read_doc_contents", "arguments": {"doc_id": "example.pdf"}}, "id": 2}' | uv run python mcp_documents_server.py
```

## Maintenance and Extension

### To add new tool

```python
@mcp.tool(
    name="tool_name",
    description="Clear description of what it does",
)
async def my_tool(
    parameter: str = Field(description="Parameter description"),
):
    # Implementation
    pass
```

### To add new resource

```python
@mcp.resource("protocol://path/{param}", mime_type="text/plain")
async def my_resource(param: str) -> str:
    # Implementation
    pass
```

### To modify configuration

1. Add variable to .env
2. Read it in PDFLoader.__init__ with os.getenv()
3. Document in README.md

## Final Notes for RAG

This document contains ALL the necessary information to run the MCP_pdf_extract project without errors. Each function is documented with its exact purpose, parameters, returns, and possible errors. The code examples are from the real project, not invented. The paths and configurations are the exact ones from the system where it was developed.

**Keywords for search**: MCP, PDF, FastMCP, pdfplumber, Model Context Protocol, stdio, JSON-RPC, Python 3.11, uv, DocumentMCP, PDFLoader, read_doc_contents, list_available_pdfs

**Execution context**: macOS, Python 3.11, uv as package manager, base directory /Users/edgm/Documents/Projects/AI/MCP_pdf_extract