# Multilingual E5 Base モデル使用ガイド

このディレクトリには、Hugging Faceの`intfloat/multilingual-e5-base`モデルを使用したテキスト埋め込み生成と検索の実装例が含まれています。

## 概要

`intfloat/multilingual-e5-base`は、100以上の言語に対応した多言語テキスト埋め込みモデルです。768次元のベクトル表現を生成し、意味的な類似性に基づいたテキスト検索を可能にします。

### 主な特徴

- **多言語対応**: 日本語、英語、中国語など100以上の言語をサポート
- **プレフィックスの使用**: クエリには`"query: "`、文書には`"passage: "`を付けることで精度向上
- **正規化済み埋め込み**: `normalize_embeddings=True`でコサイン類似度計算が簡単

## 実装例

### 1. 基本的な使用方法 (`multilingual_e5_usage.py`)

最も基本的な使用例です。モデルのロード、テキストの埋め込み生成、類似度計算を実装しています。

```python
# モデルのロード
model = SentenceTransformer('intfloat/multilingual-e5-base')

# テキストの埋め込み生成（プレフィックス付き）
query_embedding = model.encode("query: 検索したいテキスト")
passage_embedding = model.encode("passage: 文書のテキスト")

# 類似度計算（正規化済みなので内積で計算）
similarity = np.dot(query_embedding, passage_embedding)
```

### 2. ChromaDBとの統合 (`multilingual_e5_chromadb.py`)

ChromaDBベクトルデータベースとの統合例です。永続的なベクトルストレージと高速検索を実現します。

```python
# E5モデルを使用するChromaDBクライアントの作成
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="intfloat/multilingual-e5-base"
)
collection = client.create_collection(
    name="multilingual_documents",
    embedding_function=ef
)
```

### 3. ディレクトリ内ファイルのベクトル化 (`vectorize_text_files.py`)

指定ディレクトリ内のテキストファイルを一括でベクトル化し、保存します。

主な機能：

- `.txt`と`.md`ファイルの自動検出
- JSON形式とNumPy圧縮形式での保存
- 類似文書検索機能

```bash
# 実行例
python vectorize_text_files.py
```

### 4. 保存済みベクトルの使用 (`use_saved_vectors.py`)

事前計算済みのベクトルデータを読み込んで検索する例です。

```python
# JSON形式から読み込み
vectorized_docs = load_vectors_from_json("./vectorized_data/vectors.json")

# NumPy形式から読み込み（より効率的）
embeddings, metadata = load_vectors_from_npz("./vectorized_data/vectors.npz")
```

### 5. ChromaDBへのベクトルインポート (`load_vectors_to_chromadb.py`)

事前計算済みのベクトルをChromaDBに効率的にインポートします。

```python
# 埋め込みを再計算せずに高速インポート
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,  # 事前計算済みベクトル
    metadatas=metadatas
)
```

## 使用フロー

1. **ベクトル化**: `vectorize_text_files.py`でテキストファイルをベクトル化
2. **検索**: 以下のいずれかの方法で検索
   - `use_saved_vectors.py`: 直接ベクトルファイルを使用
   - `load_vectors_to_chromadb.py`: ChromaDBにインポートして使用

## インストール

### 必要なパッケージ

```bash
pip install sentence-transformers chromadb numpy
```

### モデルについて

`intfloat/multilingual-e5-base`はHugging Face上のモデルであり、別途インストールする必要はありません。`sentence-transformers`パッケージを通じて、初回使用時に自動的にダウンロードされます。

```python
from sentence_transformers import SentenceTransformer

# 初回実行時にモデルが自動的にダウンロードされる
model = SentenceTransformer('intfloat/multilingual-e5-base')
```

モデルのキャッシュ場所：

- Linux/Mac: `~/.cache/torch/sentence_transformers/`
- Windows: `C:\Users\{username}\.cache\torch\sentence_transformers\`

モデルサイズは約1.1GBです。初回ダウンロードには時間がかかる場合があります。

## パフォーマンスのヒント

1. **バッチ処理**: 複数のテキストを一度にエンコード

   ```python
   embeddings = model.encode(texts, batch_size=32)
   ```

2. **GPUの使用**: CUDAが利用可能な場合は自動的にGPUを使用

   ```python
   model = SentenceTransformer('intfloat/multilingual-e5-base', device='cuda')
   ```

3. **ベクトルの保存**:
   - JSON形式: 可読性重視、デバッグ用
   - NumPy圧縮形式: 効率性重視、本番環境用

## モデル選択の重要性

実際の使用例では、埋め込みモデルの選択が検索品質に大きく影響します。例えば：

- **固有名詞の扱い**: 日本語の固有名詞を多く含むデータセットでは、`multilingual-e5-base`が`sentence-bert-base-ja-mean-tokens-v2`よりも優れた性能を示すことがあります
- **モデルの実験**: 複数のモデルを試して、自分のユースケースに最適なものを選ぶことが重要です

## 注意事項

- E5モデルは**プレフィックスが重要**です。必ず適切なプレフィックスを使用してください
  - クエリ: `"query: "`
  - 文書: `"passage: "`
- 埋め込みは768次元のベクトルです
- 正規化済みの埋め込みを使用する場合、コサイン類似度は単純な内積で計算できます
- **日本語テキストの処理**: 特に固有名詞や専門用語を含む日本語テキストでは、multilingual-e5-baseが良好な結果を示します

## 参考リンク

- [Hugging Face - intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base)
- [実装例: Precureデータセットでの使用例](https://memo.sugyan.com/entry/2025/06/05/090000)
