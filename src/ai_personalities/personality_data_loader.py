"""
Script to store personality data in database

Loads Markdown files from the chunks folder and stores them
in database along with metadata for AI personality systems.
"""

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Union

import chromadb
# FIXME: frontmatterライブラリの型スタブファイルが見つからない
# 解決方法1: types-python-frontmatterパッケージをインストール: pip install types-python-frontmatter
# 解決方法2: frontmatter モジュールに対して # type: ignore コメントを追加
# 参考: https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-type-hints-for-third-party-library
import frontmatter

from .config import DEFAULT_CHARACTER_NAME, DEFAULT_COLLECTION_NAME, DEFAULT_DB_PATH
from .logger import get_logger

logger = get_logger(__name__)


class PersonalityDataLoader:
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        character_name: str = DEFAULT_CHARACTER_NAME,
        reset_collection: bool = True,
    ) -> None:
        """
        Initialize the data loader

        Args:
            db_path: Path to store database files
            collection_name: Name of the collection
            character_name: Name of the character for identification
            reset_collection: Whether to delete and recreate the collection
        """
        self.db_path: str = db_path
        self.collection_name: str = collection_name
        self.character_name: str = character_name
        self.client = chromadb.PersistentClient(path=db_path)

        if reset_collection:
            try:
                self.client.delete_collection(collection_name)
            # FIXME: chromadb.errorsモジュールが正しくインポートされていない
            # ChromaDBの例外クラスはchromadb.errors.InvalidCollectionExceptionなどの形式
            # 解決方法: from chromadb import errors を追加し、errors.InvalidCollectionExceptionを使用
            # または、一般的な例外処理: except Exception as e:
            # 参考: https://docs.trychroma.com/reference/py-client#errors
            except (ValueError, chromadb.errors.NotFoundError):
                pass  # Collection doesn't exist

            self.collection: chromadb.Collection = self.client.create_collection(
                name=collection_name, metadata={"description": "AI personality data"}
            )
        else:
            try:
                self.collection = self.client.get_collection(collection_name)
            except ValueError:
                self.collection = self.client.create_collection(
                    name=collection_name, metadata={"description": "AI personality data"}
                )

    def _read_markdown_file(self, file_path: Path) -> str:
        """
        Read content from a markdown file

        Args:
            file_path: Path to the markdown file

        Returns:
            File content as string

        Raises:
            Exception: If file reading fails
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_markdown_with_frontmatter(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Parse markdown content with frontmatter metadata

        Args:
            content: Raw markdown content
            file_path: Path to the original file (for metadata)

        Returns:
            Structured file data dictionary
        """
        post: frontmatter.Post = frontmatter.loads(content)

        # Structure file data
        file_data: Dict[str, Any] = {
            "id": file_path.stem,  # Use filename (without extension) as ID
            "filename": file_path.name,
            "content": post.content.strip(),
            "metadata": {
                "filename": file_path.name,
                "created_at": post.metadata.get("createdAt", ""),
                "updated_at": post.metadata.get("updatedAt", ""),
                # FIXME: post.metadata.get("tags", [])の戻り値の型が不明確
                # frontmatterのmetadataはAny型のため、tags がリストであることを保証できない
                # 解決方法1: 型チェックを追加: tags = post.metadata.get("tags", []); if isinstance(tags, list):
                # 解決方法2: 型アノテーションを追加: tags: List[str] = post.metadata.get("tags", [])
                # 参考: https://docs.python.org/3/library/functions.html#isinstance
                "tags": ", ".join(post.metadata.get("tags", [])),  # Convert list to string
                "file_size": file_path.stat().st_size,
                "character": self.character_name,
            },
        }

        return file_data

    def load_markdown_files(self, chunks_dir: str) -> List[Dict[str, Any]]:
        """
        Load and parse Markdown files

        Args:
            chunks_dir: Path to the chunks folder

        Returns:
            List of parsed file data
        """
        chunks_path: Path = Path(chunks_dir)
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks directory not found: {chunks_dir}")

        files_data: List[Dict[str, Any]] = []

        # Target only .md files
        md_files: List[Path] = sorted(chunks_path.glob("*.md"))

        for file_path in md_files:
            try:
                # Read file content
                content: str = self._read_markdown_file(file_path)

                # Parse content with frontmatter
                file_data: Dict[str, Any] = self._parse_markdown_with_frontmatter(content, file_path)

                files_data.append(file_data)
                logger.info(f"Loaded: {file_path.name}")

            except Exception as e:
                logger.error(f"File loading error: {file_path.name} - {e}")
                continue

        return files_data

    def save_to_database(self, files_data: List[Dict[str, Any]]) -> None:
        """
        Save file data to database

        Args:
            files_data: List of parsed file data
        """
        if not files_data:
            logger.warning("No data to save")
            return

        # Prepare data for batch processing
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Mapping[str, Union[str, int, float, bool, None]]] = []

        for file_data in files_data:
            ids.append(file_data["id"])
            documents.append(file_data["content"])
            metadatas.append(file_data["metadata"])

        try:
            # Batch save to database
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

            logger.info(f"Saved {len(files_data)} files to database")
            logger.info(f"Storage path: {self.db_path}")
            logger.info(f"Collection name: {self.collection_name}")

        except Exception as e:
            logger.error(f"Database save error: {e}")

    def query_test(self, query_text: str = "basic information", n_results: int = 3) -> None:
        """
        Test search of stored data

        Args:
            query_text: Search query
            n_results: Number of results to retrieve
        """
        try:
            results = self.collection.query(query_texts=[query_text], n_results=n_results)

            logger.info("\n=== Test Search Results ===")
            logger.info(f"Query: {query_text}")
            # FIXME: ChromaDBのQueryResult型のdocumentsフィールドはOptional[List[List[str]]]型
            # そのため、None可能性があり、型チェッカーが警告を出す
            # 解決方法: results.get("documents")を使用してNoneチェックを行う
            # 参考: https://docs.trychroma.com/reference/py-client#query
            if results["documents"] and len(results["documents"]) > 0:
                logger.info(f"Results count: {len(results['documents'][0])}")

                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                    logger.info(f"\n--- Result {i + 1} ---")
                    logger.info(f"Filename: {metadata['filename']}")
                    logger.info(f"Tags: {metadata.get('tags', [])}")
                    logger.info(f"Content (first 100 chars): {doc[:100]}...")

        except Exception as e:
            logger.error(f"Search error: {e}")

    def get_collection_info(self) -> None:
        """Display collection information"""
        try:
            count: int = self.collection.count()
            logger.info("\n=== Collection Information ===")
            logger.info(f"Collection name: {self.collection_name}")
            logger.info(f"Number of stored documents: {count}")

        except Exception as e:
            logger.error(f"Information retrieval error: {e}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Store AI personality data in database")

    parser.add_argument(
        "--chunks-dir",
        type=str,
        default=os.environ.get("CHUNKS_DIR"),
        required=not os.environ.get("CHUNKS_DIR"),
        help="Path to the chunks directory (required unless CHUNKS_DIR env var is set)",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default=os.environ.get("CHROMA_DB_PATH", DEFAULT_DB_PATH),
        help=f"Path to store database files (default: from CHROMA_DB_PATH env var or {DEFAULT_DB_PATH})",
    )

    parser.add_argument(
        "--collection-name",
        type=str,
        default=os.environ.get("COLLECTION_NAME", DEFAULT_COLLECTION_NAME),
        help=f"Name of the database collection (default: from COLLECTION_NAME env or {DEFAULT_COLLECTION_NAME})",
    )

    parser.add_argument(
        "--character-name",
        type=str,
        default=os.environ.get("CHARACTER_NAME", DEFAULT_CHARACTER_NAME),
        help=f"Name of the character (default: from CHARACTER_NAME env or {DEFAULT_CHARACTER_NAME})",
    )

    return parser.parse_args()


def main() -> None:
    """Main processing"""
    args: argparse.Namespace = parse_arguments()

    # Initialize data loader
    loader: PersonalityDataLoader = PersonalityDataLoader(
        db_path=args.db_path,
        collection_name=args.collection_name,
        character_name=args.character_name,
    )

    try:
        # Load Markdown files
        logger.info("=== Starting Markdown file loading ===")
        files_data: List[Dict[str, Any]] = loader.load_markdown_files(args.chunks_dir)

        # Save to database
        logger.info("\n=== Starting database save ===")
        loader.save_to_database(files_data)

        # Display collection information
        loader.get_collection_info()

        # Execute test searches
        logger.info("\n=== Executing test searches ===")
        loader.query_test("basic information")
        loader.query_test("dialogue style")
        loader.query_test("personality traits")

        logger.info("\n=== Processing completed ===")

    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
