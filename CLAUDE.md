# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP_pdf_extract is a Python-based MCP (Model Context Protocol) server implementation for document management with PDF handling capabilities. The project currently consists of two main components that need integration:

1. **mcp_documents_server.py**: MCP server using FastMCP framework with hardcoded document metadata
2. **pdf.py**: PDF loader module with async text extraction capabilities

## Key Architecture Notes

### Current State
- The MCP server (`mcp_documents_server.py`) uses mock/hardcoded document data
- The PDF loader (`pdf.py`) is not yet integrated with the MCP server
- Missing `app.exceptions` module that `pdf.py` expects to import from

### MCP Server Structure
- Uses FastMCP framework for implementing MCP protocol
- Exposes one tool: `read_doc_contents` - reads document contents by ID
- Provides two resources:
  - `docs://documents` - lists all document IDs
  - `docs://documents/{doc_id}` - fetches specific document content
- Runs on stdio transport when executed directly

### PDF Loader Features
- Async PDF text extraction using pdfplumber
- Security features: file size validation, path traversal protection
- Configurable via environment variables:
  - `MAX_PDF_SIZE_KB` (default: 350)
  - `PDF_DIR` (default: ./data/pdfs)

## Development Commands

### Running the MCP Server
```bash
python mcp_documents_server.py
```

### Missing Setup Steps
This project currently lacks standard Python project structure. When developing:

1. **Dependencies Installation**: No requirements.txt exists. The project needs:
   - `mcp` (with server.fastmcp support)
   - `pydantic`
   - `pdfplumber`
   - `python-dotenv`

2. **Exception Module**: Create `app/exceptions.py` with:
   - `DocumentLoadError`
   - `ValidationError`

3. **Environment Setup**: Create `.env` file with:
   ```
   MAX_PDF_SIZE_KB=350
   PDF_DIR=./data/pdfs
   ```

## Integration Considerations

When integrating the PDF loader with the MCP server:
1. Replace hardcoded `docs` dictionary with dynamic PDF loading
2. Use `PDFLoader.list_available_pdfs()` for the documents resource
3. Use `PDFLoader.load_pdf()` in the `read_doc_contents` tool
4. Handle async operations properly within FastMCP framework
5. Ensure proper error handling for PDF loading failures

## File Permissions

The `.claude/settings.local.json` file allows bash commands:
- `find` commands (all variations)
- `ls` commands (all variations)