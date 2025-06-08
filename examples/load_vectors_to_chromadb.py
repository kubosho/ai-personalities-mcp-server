"""保存されたベクトルデータをChromaDBに読み込む"""

import json
import numpy as np
import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings, Documents
from typing import List, Dict, Any
from pathlib import Path


class PrecomputedEmbeddingFunction(EmbeddingFunction):
    """事前計算済みの埋め込みを使用するカスタム埋め込み関数"""
    
    def __init__(self, precomputed_embeddings: Dict[str, List[float]]):
        self.embeddings_map = precomputed_embeddings
    
    def __call__(self, input: Documents) -> Embeddings:
        """ドキュメントIDから埋め込みを返す"""
        embeddings = []
        for doc in input:
            # ドキュメントがIDとして渡されることを想定
            if doc in self.embeddings_map:
                embeddings.append(self.embeddings_map[doc])
            else:
                # 見つからない場合はゼロベクトル（実際の使用では適切なエラー処理を）
                embeddings.append([0.0] * 768)  # E5モデルの次元数
        return embeddings


def load_vectors_to_chromadb_from_json(json_path: str, collection_name: str = "shinosawa_hiro"):
    """JSON形式のベクトルデータをChromaDBに読み込む"""
    # ベクトルデータを読み込み
    with open(json_path, 'r', encoding='utf-8') as f:
        vectorized_docs = json.load(f)
    
    # ChromaDBクライアントを作成
    client = chromadb.PersistentClient(path="./chroma_db_with_vectors")
    
    # 既存のコレクションがあれば削除
    try:
        client.delete_collection(name=collection_name)
    except:
        pass
    
    # コレクションを作成（埋め込み関数なし）
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Pre-computed E5 embeddings"}
    )
    
    # データを準備
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for i, doc in enumerate(vectorized_docs):
        doc_id = f"doc_{i}"
        ids.append(doc_id)
        
        # ファイル名をドキュメントとして保存
        documents.append(doc['filename'])
        
        # 埋め込みベクトル
        embeddings.append(doc['embedding'])
        
        # メタデータ
        metadatas.append({
            'path': doc['path'],
            'filename': doc['filename'],
            'size': doc['size']
        })
    
    # ChromaDBに追加（埋め込みを直接提供）
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    print(f"ChromaDBに{len(ids)}個のドキュメントを追加しました")
    return client, collection


def load_vectors_to_chromadb_from_npz(npz_path: str, collection_name: str = "shinosawa_hiro_npz"):
    """NumPy形式のベクトルデータをChromaDBに読み込む"""
    # ベクトルデータを読み込み
    data = np.load(npz_path)
    embeddings_array = data['embeddings']
    metadata_list = json.loads(str(data['metadata']))
    
    # ChromaDBクライアントを作成
    client = chromadb.PersistentClient(path="./chroma_db_with_vectors")
    
    # 既存のコレクションがあれば削除
    try:
        client.delete_collection(name=collection_name)
    except:
        pass
    
    # コレクションを作成
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Pre-computed E5 embeddings from NPZ"}
    )
    
    # データを準備
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for i, (embedding, metadata) in enumerate(zip(embeddings_array, metadata_list)):
        doc_id = f"doc_{i}"
        ids.append(doc_id)
        documents.append(metadata['filename'])
        embeddings.append(embedding.tolist())
        metadatas.append(metadata)
    
    # ChromaDBに追加
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    print(f"ChromaDBに{len(ids)}個のドキュメントを追加しました（NPZ形式から）")
    return client, collection


def search_in_chromadb(collection: chromadb.Collection, query_embedding: List[float], n_results: int = 5):
    """事前計算済みのクエリ埋め込みでChromaDBを検索"""
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results


def main():
    from sentence_transformers import SentenceTransformer
    
    # 検索用のモデルをロード
    print("モデルをロード中...")
    model = SentenceTransformer('intfloat/multilingual-e5-base')
    
    # JSON形式からChromaDBに読み込み
    print("\n=== JSON形式からChromaDBに読み込み ===")
    json_path = "./vectorized_data/shinosawa_hiro_vectors.json"
    client, collection_json = load_vectors_to_chromadb_from_json(json_path)
    
    # 検索テスト
    query = "アイドルになった理由"
    query_embedding = model.encode(
        f"query: {query}",
        convert_to_numpy=True,
        normalize_embeddings=True
    ).tolist()
    
    results = search_in_chromadb(collection_json, query_embedding, n_results=3)
    
    print(f"\nクエリ: {query}")
    print("検索結果:")
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"  {i+1}. {doc}")
        print(f"     パス: {metadata['path']}")
        print(f"     距離: {distance:.4f}")
    
    # NPZ形式からもテスト
    print("\n=== NPZ形式からChromaDBに読み込み ===")
    npz_path = "./vectorized_data/shinosawa_hiro_vectors.npz"
    client, collection_npz = load_vectors_to_chromadb_from_npz(npz_path)
    
    # コレクション統計を表示
    print(f"\n保存されたコレクション:")
    for col in client.list_collections():
        count = client.get_collection(col.name).count()
        print(f"  - {col.name}: {count}個のドキュメント")


if __name__ == "__main__":
    main()