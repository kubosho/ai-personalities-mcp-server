"""ChromaDBでMultilingual E5 Baseモデルを使用する例"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any


def create_chroma_client_with_e5():
    """multilingual-e5-baseを使用するChromaDBクライアントを作成"""
    # SentenceTransformerEmbeddingFunctionを使用
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-base"
    )
    
    # ChromaDBクライアントを作成
    client = chromadb.PersistentClient(path="./chroma_e5_db")
    
    # コレクションを作成または取得
    collection = client.get_or_create_collection(
        name="multilingual_documents",
        embedding_function=ef
    )
    
    return client, collection


def add_documents_with_prefix(
    collection: chromadb.Collection,
    documents: List[str],
    metadatas: List[Dict[str, Any]] = None,
    ids: List[str] = None
):
    """E5モデル用のプレフィックスを付けてドキュメントを追加"""
    # E5モデルでは、パッセージには"passage: "プレフィックスを推奨
    prefixed_docs = [f"passage: {doc}" for doc in documents]
    
    collection.add(
        documents=prefixed_docs,
        metadatas=metadatas,
        ids=ids
    )


def query_with_prefix(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = 5
) -> Dict[str, Any]:
    """E5モデル用のプレフィックスを付けてクエリを実行"""
    # E5モデルでは、クエリには"query: "プレフィックスを推奨
    prefixed_query = f"query: {query_text}"
    
    results = collection.query(
        query_texts=[prefixed_query],
        n_results=n_results
    )
    
    return results


def main():
    # ChromaDBクライアントとコレクションを作成
    client, collection = create_chroma_client_with_e5()
    
    # サンプルドキュメント（多言語）
    documents = [
        "人工知能は人間の知能を模倣する技術です。",
        "機械学習はデータからパターンを学習します。",
        "深層学習は多層ニューラルネットワークを使用します。",
        "Natural language processing enables computers to understand human language.",
        "Computer vision allows machines to interpret visual information.",
        "强化学习通过试错来学习最优策略。"
    ]
    
    # メタデータ
    metadatas = [
        {"category": "AI", "language": "ja"},
        {"category": "ML", "language": "ja"},
        {"category": "DL", "language": "ja"},
        {"category": "NLP", "language": "en"},
        {"category": "CV", "language": "en"},
        {"category": "RL", "language": "zh"}
    ]
    
    # ドキュメントID
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    # ドキュメントを追加
    add_documents_with_prefix(collection, documents, metadatas, ids)
    print(f"追加されたドキュメント数: {collection.count()}")
    
    # クエリ例
    queries = [
        "AIについて教えてください",
        "What is machine learning?",
        "深度学习是什么？"
    ]
    
    print("\n検索結果:")
    print("-" * 50)
    
    for query in queries:
        results = query_with_prefix(collection, query, n_results=3)
        
        print(f"\nクエリ: {query}")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            # プレフィックスを除去して表示
            clean_doc = doc.replace("passage: ", "")
            print(f"  {i+1}. {clean_doc}")
            print(f"     言語: {metadata['language']}, カテゴリ: {metadata['category']}")
            print(f"     距離: {distance:.4f}")


if __name__ == "__main__":
    main()