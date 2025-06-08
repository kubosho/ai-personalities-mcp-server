"""Multilingual E5 Base モデルの使用例"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List


def load_multilingual_e5_model() -> SentenceTransformer:
    """multilingual-e5-baseモデルをロード"""
    model = SentenceTransformer('intfloat/multilingual-e5-base')
    return model


def encode_texts(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    """テキストを埋め込みベクトルに変換"""
    # E5モデルでは、クエリには"query: "、パッセージには"passage: "のプレフィックスを推奨
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


def compute_similarity(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
    """埋め込みベクトル間のコサイン類似度を計算"""
    # 正規化済みの場合、内積がコサイン類似度になる
    similarity = np.dot(embeddings1, embeddings2.T)
    return similarity


def main():
    # モデルをロード
    model = load_multilingual_e5_model()
    
    # クエリ用のテキスト
    queries = [
        "query: 機械学習とは何ですか？",
        "query: What is artificial intelligence?",
        "query: 什么是深度学习？"
    ]
    
    # パッセージ（文書）用のテキスト
    passages = [
        "passage: 機械学習は、データから自動的にパターンを学習するAIの手法です。",
        "passage: Machine learning is a method of AI that learns patterns from data automatically.",
        "passage: 深度学习是一种使用多层神经网络的机器学习方法。",
        "passage: ディープラーニングは多層ニューラルネットワークを使用する機械学習手法です。"
    ]
    
    # 埋め込みを生成
    query_embeddings = encode_texts(model, queries)
    passage_embeddings = encode_texts(model, passages)
    
    # 類似度を計算
    similarities = compute_similarity(query_embeddings, passage_embeddings)
    
    # 結果を表示
    print("クエリとパッセージ間の類似度スコア:")
    print("-" * 50)
    for i, query in enumerate(queries):
        print(f"\n{query}")
        for j, passage in enumerate(passages):
            score = similarities[i, j]
            print(f"  {passage[:50]}... : {score:.4f}")


if __name__ == "__main__":
    main()