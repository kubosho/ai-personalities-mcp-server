"""保存されたベクトルデータを使用する例"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any


def load_vectors_from_json(json_path: str) -> List[Dict[str, Any]]:
    """JSON形式のベクトルデータを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        vectorized_docs = json.load(f)
    return vectorized_docs


def load_vectors_from_npz(npz_path: str) -> tuple:
    """NumPy形式のベクトルデータを読み込む"""
    data = np.load(npz_path)
    embeddings = data['embeddings']
    metadata = json.loads(str(data['metadata']))
    return embeddings, metadata


def search_with_saved_vectors(
    query: str, 
    model: SentenceTransformer,
    embeddings: np.ndarray,
    metadata: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """保存されたベクトルを使って類似検索"""
    # クエリをベクトル化
    query_embedding = model.encode(
        f"query: {query}",
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # コサイン類似度を計算（正規化済みなので内積で計算）
    similarities = np.dot(embeddings, query_embedding)
    
    # 上位k個のインデックスを取得
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # 結果を作成
    results = []
    for idx in top_indices:
        results.append({
            'filename': metadata[idx]['filename'],
            'path': metadata[idx]['path'],
            'similarity': float(similarities[idx])
        })
    
    return results


def main():
    # モデルをロード（クエリのベクトル化に必要）
    print("モデルをロード中...")
    model = SentenceTransformer('intfloat/multilingual-e5-base')
    
    # 方法1: JSON形式から読み込み
    print("\n=== JSON形式のベクトルデータを使用 ===")
    json_path = "./vectorized_data/shinosawa_hiro_vectors.json"
    vectorized_docs = load_vectors_from_json(json_path)
    
    # ベクトルとメタデータを分離
    embeddings_list = [np.array(doc['embedding']) for doc in vectorized_docs]
    embeddings_json = np.array(embeddings_list)
    metadata_json = [{
        'filename': doc['filename'],
        'path': doc['path']
    } for doc in vectorized_docs]
    
    # 検索実行
    query = "篠澤広の趣味は何ですか？"
    results_json = search_with_saved_vectors(
        query, model, embeddings_json, metadata_json, top_k=3
    )
    
    print(f"クエリ: {query}")
    print("検索結果:")
    for i, result in enumerate(results_json, 1):
        print(f"  {i}. {result['filename']} (類似度: {result['similarity']:.4f})")
    
    # 方法2: NumPy形式から読み込み（より効率的）
    print("\n=== NumPy形式のベクトルデータを使用 ===")
    npz_path = "./vectorized_data/shinosawa_hiro_vectors.npz"
    embeddings_npz, metadata_npz = load_vectors_from_npz(npz_path)
    
    # 別のクエリで検索
    query2 = "困難に立ち向かう性格について"
    results_npz = search_with_saved_vectors(
        query2, model, embeddings_npz, metadata_npz, top_k=3
    )
    
    print(f"クエリ: {query2}")
    print("検索結果:")
    for i, result in enumerate(results_npz, 1):
        print(f"  {i}. {result['filename']} (類似度: {result['similarity']:.4f})")


if __name__ == "__main__":
    main()