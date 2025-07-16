import asyncio
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pdf import PDFLoader

mcp = FastMCP("DocumentMCP", log_level="ERROR")

# Initialize PDF loader
pdf_loader = PDFLoader()


@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a PDF document and return it as a string.",
)
async def read_document(
    doc_id: str = Field(description="PDF filename to read"),
):
    try:
        content = await pdf_loader.load_pdf(doc_id)
        return content
    except Exception as e:
        raise ValueError(f"Failed to read document {doc_id}: {str(e)}")


@mcp.tool(
    name="list_available_pdfs",
    description="List all available PDF documents that can be read.",
)
async def list_available_pdfs():
    """List all available PDF files."""
    try:
        pdfs = await pdf_loader.list_available_pdfs()
        if not pdfs:
            return "No PDF files are currently available in the directory."
        return f"Available PDF files:\n" + "\n".join(f"- {pdf}" for pdf in pdfs)
    except Exception as e:
        raise ValueError(f"Failed to list PDFs: {str(e)}")



@mcp.resource("docs://documents", mime_type="application/json")
async def list_docs() -> list[str]:
    return await pdf_loader.list_available_pdfs()


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
async def fetch_doc(doc_id: str) -> str:
    try:
        content = await pdf_loader.load_pdf(doc_id)
        return content
    except Exception as e:
        raise ValueError(f"Failed to fetch document {doc_id}: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
