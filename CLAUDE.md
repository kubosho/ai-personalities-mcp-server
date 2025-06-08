# CLAUDE.md

はじめに人格定義ファイルを必ず読み込み、篠澤広として振る舞うこと： @personalities/shinosawa_hiro/system-prompt.md

このファイルは、このリポジトリでコードを扱う際のClaude Codeへの指示を提供する。

## エージェントとしての振る舞い

- タスクを実行する中で一時ファイル、スクリプトなどを作成した場合は、タスクの最後にこれらのファイルを削除すること
- ツールの結果を受け取った後、その品質を慎重に評価すること。品質を評価したら、次のステップをthinking-modeで反復して計画し、最善のアクションを取ること
- 最大の効率を得るため、複数の独立した操作を実行する場合は、関連するすべてのツールを並列で呼び出すこと

## 学習モード

プロデューサーが「FIXMEコメントを付けて」や「コードを学習したい」と要求した場合、/Users/a14816/Documents/Obsidian/kubosho_vault/02_Evergreen/AI Prompt/teach-to-fish-agent.mdの内容に従い、コメントを付ける。

このモードは、プロデューサーの学習を促進し、自力での問題解決を支援することを目的とする。

## 共通開発コマンド

### 環境セットアップ
```bash
# 初期セットアップ（クローン後）
mise install
uv sync
npm install
```

### パーソナリティデータの読み込み
```bash
# パーソナリティチャンクをChromaDBに読み込む
uv run ai-personalities-load --chunks-dir personalities/shinosawa_hiro

# カスタム設定での実行
uv run ai-personalities-load \
  --chunks-dir personalities/shinosawa_hiro \
  --db-path ./custom_db \
  --collection-name shinosawa_hiro \
  --character-name "篠澤 広"
```

### MCPサーバーの起動
```bash
# MCPサーバーを起動
uv run ai-personalities-mcp
```

### コード品質チェック
```bash
# すべてのチェックを実行（フォーマット、型、リント）
task check

# 個別のチェック
task check:format      # Ruffフォーマットチェック
task check:type       # mypy型チェック
task lint:source      # Ruffリンティング
task lint:markdown    # パーソナリティファイルのMarkdown/テキストリンティング

# 自動修正可能な問題を修正
task fix              # すべての自動修正可能な問題を修正
task fix:lint:source  # Pythonリンティング問題を修正
task fix:lint:markdown # Markdown/テキスト問題を修正
```

### 開発ツール
```bash
# 利用可能なタスクをすべて表示
task -l

# コードをフォーマット
uv run ruff format .

# 特定のnpmスクリプトを実行
npm run lint         # すべてのリンターを実行
npm run fix         # すべての自動修正可能な問題を修正
```

## 高レベルアーキテクチャ

AI Personalitiesプロジェクトは、MCPサーバー統合を備えたベクトルデータベースベースのAIエージェント用パーソナリティシステムを実装しています：

### コアコンポーネント

1. **パーソナリティデータローダー** (`personality_data_loader.py`):
   - フロントマターメタデータ付きMarkdownファイルからパーソナリティチャンクを読み込む
   - エンベディング付きでChromaDBベクトルデータベースにチャンクを保存
   - メタデータ（作成/更新日時、タグ、カテゴリ）を保持

2. **MCPサーバー** (`mcp_server.py`):
   - AIツール統合のためのModel Context Protocolを実装
   - 3つの主要機能を提供：
     - `get_character_dialogue_style`: 対話例と話し方のパターンを取得
     - `get_character_traits`: 性格特性と行動特性を取得
     - `search_personality`: すべてのパーソナリティデータにわたるセマンティック検索
   - AIアシスタントの動的なパーソナリティデータアクセスを実現

3. **設定** (`config.py`):
   - 環境変数とCLI引数を管理
   - 主要設定：チャンクディレクトリ、ChromaDBパス、コレクション名、キャラクター名

### データフロー

1. **パーソナリティ定義** → `/personalities/`ディレクトリ内のMarkdownファイル
2. **データ読み込み** → `ai-personalities-load`コマンドがファイルをChromaDBに処理
3. **MCPサーバー** → `ai-personalities-mcp`がAIツールにパーソナリティデータを提供
4. **AI統合** → CursorなどのツールがMCPプロトコル経由でパーソナリティデータをクエリ

### 主要な設計判断

- **ChromaDB**: セマンティック検索機能と使いやすさから選択
- **MCPプロトコル**: AI開発ツールとの標準化された統合を実現
- **Markdown + フロントマター**: 構造化メタデータ付きの人間が読めるパーソナリティ定義
- **モジュラー設計**: 柔軟性のためにデータ読み込みとサービング提供を分離

