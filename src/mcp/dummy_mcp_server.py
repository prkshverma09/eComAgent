import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

server = Server("python-echo")

@server.tool("echo")
async def echo(message: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"You said: {message}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options=None,
        )

if __name__ == "__main__":
    asyncio.run(main())
