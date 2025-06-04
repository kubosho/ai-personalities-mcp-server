"""
MCP Server for AI personality data access

Provides dynamic access to data stored in database
for use with MCP-compatible tools.
"""

import asyncio
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions

from .config import DEFAULT_COLLECTION_NAME, DEFAULT_DB_PATH, get_server_name
from .logger import get_logger
from .personality_data_loader import PersonalityDataLoader

logger = get_logger(__name__)


class PersonalityMCPServer:
    """MCP Server for AI personality data access"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, collection_name: str = DEFAULT_COLLECTION_NAME) -> None:
        self.server = Server(get_server_name())
        self.db_path: str = db_path
        self.collection_name: str = collection_name
        self.loader: Optional[PersonalityDataLoader] = None

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools"""
        self.server.list_tools()(self._handle_list_tools)
        self.server.call_tool()(self._handle_call_tool)

    async def _handle_list_tools(self) -> List[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="search_personality",
                description="Search personality data for a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for personality traits, dialogue, etc.",
                        },
                        "character": {
                            "type": "string",
                            "description": "Character name to search for",
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 3)",
                            "default": 3,
                        },
                    },
                    "required": ["query", "character"],
                },
            ),
            types.Tool(
                name="get_character_dialogue_style",
                description="Get specific dialogue style information for a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character": {
                            "type": "string",
                            "description": "Character name",
                        }
                    },
                    "required": ["character"],
                },
            ),
            types.Tool(
                name="get_character_traits",
                description="Get personality traits for a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character": {
                            "type": "string",
                            "description": "Character name",
                        }
                    },
                    "required": ["character"],
                },
            ),
        ]

    async def _handle_call_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> List[types.TextContent]:
        """Handle tool calls"""

        if not self.loader:
            self._initialize_loader()

        if name == "search_personality":
            return await self._search_personality(arguments or {})
        elif name == "get_character_dialogue_style":
            return await self._get_dialogue_style(arguments or {})
        elif name == "get_character_traits":
            return await self._get_character_traits(arguments or {})
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _initialize_loader(self) -> None:
        """Initialize database loader"""
        try:
            self.loader = PersonalityDataLoader(db_path=self.db_path, collection_name=self.collection_name)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database: {e}")

    async def _search_personality(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Search personality data"""
        query: str = args.get("query", "")
        character: str = args.get("character", "")
        n_results: int = min(args.get("n_results", 3), 20)

        if not query or not character:
            return [types.TextContent(type="text", text="Error: Both query and character are required")]

        try:
            if not self.loader:
                raise RuntimeError("Database loader not initialized")

            search_query: str = f"{character} {query}"
            results = self.loader.collection.query(
                query_texts=[search_query],
                n_results=n_results,
                where={"character": character},
            )

            documents_list = results.get("documents")
            if not documents_list or not documents_list[0]:
                return [
                    types.TextContent(
                        type="text",
                        text=f"No personality data found for {character} with query: {query}",
                    )
                ]

            formatted_results: List[str] = []
            documents = documents_list[0]
            metadatas_list = results.get("metadatas", [[]])
            metadatas = metadatas_list[0] if metadatas_list else []

            for i, doc in enumerate(documents):
                # FIXME: metadataの型が不明確なため、型チェッカーが警告を出している
                # ChromaDBのmetadatasは Optional[List[List[Mapping[str, Union[str, int, float, bool, None]]]]] 型
                # 解決方法1: 型アサーションを使用: cast(Dict[str, Any], metadata)
                # 解決方法2: 型ガードを実装: if isinstance(metadata, dict):
                # 参考: https://docs.python.org/3/library/typing.html#typing.cast
                metadata = metadatas[i] if i < len(metadatas) else {}
                filename = str(metadata.get("filename", "unknown")) if metadata else "unknown"
                tags = str(metadata.get("tags", "")) if metadata else ""

                result_text: str = f"""
**Source:** {filename}
**Tags:** {tags}
**Content:**
{doc}

---
"""
                formatted_results.append(result_text)

            return [
                types.TextContent(
                    type="text",
                    text=f"**Personality data for {character}:**\n\n" + "\n".join(formatted_results),
                )
            ]

        except Exception as e:
            logger.error(f"Error searching personality data: {e}")
            return [types.TextContent(type="text", text="Error searching personality data")]

    async def _get_dialogue_style(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get dialogue style information"""
        character: str = args.get("character", "")

        if not character:
            return [types.TextContent(type="text", text="Error: Character name is required")]

        # Search for dialogue-specific information
        args_with_query: Dict[str, Any] = {
            "query": "dialogue style speech patterns talking",
            "character": character,
            "n_results": 5,
        }

        return await self._search_personality(args_with_query)

    async def _get_character_traits(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get character traits"""
        character: str = args.get("character", "")

        if not character:
            return [types.TextContent(type="text", text="Error: Character name is required")]

        # Search for personality traits
        args_with_query: Dict[str, Any] = {
            "query": "personality traits character behavior",
            "character": character,
            "n_results": 5,
        }

        return await self._search_personality(args_with_query)

    async def run(self) -> None:
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=get_server_name(),
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def async_main() -> None:
    """Main entry point"""
    import argparse

    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="AI Personality MCP Server")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help=f"Path to database (default: {DEFAULT_DB_PATH})")
    parser.add_argument(
        "--collection", default=DEFAULT_COLLECTION_NAME, help=f"Collection name (default: {DEFAULT_COLLECTION_NAME})"
    )

    args: argparse.Namespace = parser.parse_args()

    logger.info("🚀 AI Personality MCP Server starting...")
    logger.info(f"📁 Database path: {args.db_path}")
    logger.info(f"📚 Collection: {args.collection}")
    logger.info("💡 Server is running in stdio mode - waiting for MCP client connection")
    logger.info("🔗 To test: Use MCP Inspector or connect via Claude Desktop")
    logger.info("⏹️ To stop: Press Ctrl+C")

    server: PersonalityMCPServer = PersonalityMCPServer(db_path=args.db_path, collection_name=args.collection)

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Server error: {e}")
        raise


def main() -> None:
    """Entry point that runs the async main"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
