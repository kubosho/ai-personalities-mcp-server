"""テキストファイルをMultilingual E5 Baseでベクトル化"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer


def load_multilingual_e5_model() -> SentenceTransformer:
    """multilingual-e5-baseモデルをロード"""
    model = SentenceTransformer('intfloat/multilingual-e5-base')
    return model


def read_text_files(directory: str) -> List[Dict[str, Any]]:
    """指定ディレクトリからテキストファイルを読み込む"""
    files_data = []
    directory_path = Path(directory)
    
    # .txt, .md ファイルを検索
    for file_path in directory_path.glob("**/*"):
        if file_path.suffix in ['.txt', '.md'] and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                files_data.append({
                    'path': str(file_path),
                    'filename': file_path.name,
                    'content': content,
                    'size': len(content)
                })
                print(f"読み込み: {file_path.name}")
            except Exception as e:
                print(f"エラー: {file_path.name} - {e}")
    
    return files_data


def vectorize_documents(model: SentenceTransformer, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ドキュメントをベクトル化"""
    vectorized_docs = []
    
    for doc in documents:
        # E5モデルのpassageプレフィックスを追加
        prefixed_content = f"passage: {doc['content']}"
        
        # ベクトル化
        embedding = model.encode(
            prefixed_content,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        vectorized_docs.append({
            'path': doc['path'],
            'filename': doc['filename'],
            'size': doc['size'],
            'embedding': embedding.tolist()  # JSONシリアライズのためリストに変換
        })
        
        print(f"ベクトル化完了: {doc['filename']} (次元: {len(embedding)})")
    
    return vectorized_docs


def save_vectors(vectorized_docs: List[Dict[str, Any]], output_path: str):
    """ベクトルデータをJSONとして保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vectorized_docs, f, ensure_ascii=False, indent=2)
    print(f"\nベクトルデータを保存: {output_path}")


def save_vectors_npz(vectorized_docs: List[Dict[str, Any]], output_path: str):
    """ベクトルデータをNumPy形式で保存（効率的）"""
    # ベクトルを配列として抽出
    embeddings = np.array([doc['embedding'] for doc in vectorized_docs])
    
    # メタデータ
    metadata = [{
        'path': doc['path'],
        'filename': doc['filename'],
        'size': doc['size']
    } for doc in vectorized_docs]
    
    # .npz形式で保存
    np.savez_compressed(
        output_path,
        embeddings=embeddings,
        metadata=json.dumps(metadata, ensure_ascii=False)
    )
    print(f"ベクトルデータを保存（圧縮形式）: {output_path}")


def search_similar(query: str, model: SentenceTransformer, vectorized_docs: List[Dict[str, Any]], top_k: int = 5):
    """類似ドキュメントを検索"""
    # クエリをベクトル化
    query_embedding = model.encode(
        f"query: {query}",
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # 各ドキュメントとの類似度を計算
    similarities = []
    for doc in vectorized_docs:
        doc_embedding = np.array(doc['embedding'])
        similarity = np.dot(query_embedding, doc_embedding)
        similarities.append({
            'filename': doc['filename'],
            'path': doc['path'],
            'similarity': similarity
        })
    
    # 類似度でソート
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities[:top_k]


def main():
    # 対象ディレクトリ
    target_directory = "/Users/a14816/Documents/Obsidian/kubosho_vault/02_Evergreen/AI-Personalities/Shinosawa-Hiro/chunks"
    
    # モデルをロード
    print("モデルをロード中...")
    model = load_multilingual_e5_model()
    
    # テキストファイルを読み込み
    print(f"\nディレクトリをスキャン: {target_directory}")
    documents = read_text_files(target_directory)
    print(f"読み込んだファイル数: {len(documents)}")
    
    if not documents:
        print("テキストファイルが見つかりませんでした。")
        return
    
    # ベクトル化
    print("\nベクトル化を開始...")
    vectorized_docs = vectorize_documents(model, documents)
    
    # 保存
    output_dir = "./vectorized_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # JSON形式で保存
    save_vectors(vectorized_docs, f"{output_dir}/shinosawa_hiro_vectors.json")
    
    # NumPy形式で保存（より効率的）
    save_vectors_npz(vectorized_docs, f"{output_dir}/shinosawa_hiro_vectors.npz")
    
    # 検索例
    print("\n=== 検索例 ===")
    test_query = "篠澤広の性格について"
    results = search_similar(test_query, model, vectorized_docs, top_k=3)
    
    print(f"クエリ: {test_query}")
    print("類似ドキュメント:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['filename']} (類似度: {result['similarity']:.4f})")


if __name__ == "__main__":
    main()