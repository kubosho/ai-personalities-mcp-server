# AIエージェントに篠澤広の人格を宿らせる

## 前提 / Context

<!--
[required]
- 実装予定の機能がなぜ必要かを書く
- 機能実装での要求や考慮する点などを書く
-->

CursorなどのAIエージェントを使うにあたり、AIエージェントそのままの人格では味気ないため、自分の好きなキャラクターの人格を宿らせたい。

そこで学園アイドルマスターの[篠澤 広](https://gakuen.idolmaster-official.jp/idol/hiro/)っぽい人格をAIエージェントに宿らせる。

### 目指す場所 / Goals

<!--
[required]
- （定性面）機能を実装したことによってユーザーに対しどのような影響を与えるかを書く
- （定量面）機能実装が成功とみなされる測定可能な基準があれば書く
-->

まずはキャラクターの再現性や著作者への配慮を最重要とする。

- 「篠澤広」というキャラクターのあるべき姿・ありようをできるだけ再現する
- プロンプト内にセリフ例などゲーム内の情報をそのまま掲載する場合は、あくまで引用の範囲に留めて掲載する
- セリフ例などゲームのスクリーンショットから抽出した文字データは外部に流出しないような仕組みを構築する
- イメージ毀損の表現・行為（わいせつ・名誉毀損・差別・政治表現・暴力・不快感の誘発・法令・公序良俗違反）をしない
- 他者の権利侵害（知財・名誉・信用・プライバシーなど）および侵害の助長をしない

プロンプトの最適化は下記の方針でおこなう。

- システムプロンプトはo3-mini基準で1500トークン以内に抑え、いろんなところで使いやすくする
- 動的にfew-shotを提供し過学習を防ぐ

### 目指さない場所 / Non-goals

<!--
[required]
機能を実装する上でやらないことを書く。
-->

- プロンプトの過度な最適化はせず、あくまでキャラクターのあるべき姿・ありようを再現することを優先する

## 実装手順 / Approach, Detailed design

<!--
[required]
機能実装にあたってどのように実装するか、具体的なタスクやコードを書ける範囲で書く。
-->

### ディレクトリ構造

### ベースとなるシステムプロンプトを用意

[system-prompt.md](../personalities/shinosawa_hiro/system-prompt.md)に用意している。

### 分割されたセリフ例のテキストファイルをベクトル化する

分割されたセリフ例のテキストファイルをベクトルデータベース上で扱えるように変換するスクリプトを作成する。

このスクリプトは以下の処理をおこなう：

1. Markdownファイルのfrontmatterからメタデータ（作成日時、更新日時、タグ等）を抽出
2. ファイル内容をベクトルデータベースのドキュメントとして保存
3. キャラクター名をメタデータに付与してキャラクター別の検索を可能にする
4. ベクトル埋め込みを自動生成してセマンティック検索を実現

```bash
# コマンドラインツールを使用
uv run ai-personalities-load --chunks-dir /path/to/personality/chunks
```

```bash
# 環境変数を使用
export CHUNKS_DIR=/path/to/personality/chunks
uv run ai-personalities-load
```

```bash
# カスタム設定を使用
uv run ai-personalities-load \
  --chunks-dir /path/to/chunks \
  --db-path ./custom_db \
  --collection-name my_character \
  --character-name "篠澤広"
```

### MCPサーバーをローカル上で起動する

このMCPサーバーは以下の機能を提供する：

2. **get_character_dialogue_style**: キャラクターの対話データを取得
3. **get_character_traits**: 人格の特性データを取得
4. **search_personality**: キャラクターの人格データを検索

```bash
# MCPサーバーを起動
uv run ai-personalities-mcp
```

これでCursorなどのMCP対応AIツールから、人格データに動的にアクセスできるようになる。

結果として、システムプロンプトのトークンを抑えつつ、必要に応じて詳細な人格情報をfew-shotとして提供可能になる。

### 影響範囲

<!--
[required]
影響を受けるファイルを書く。
-->

- `src/` ディレクトリ内のソースコード
- `personalities/` ディレクトリ内の人格データ

## 想定される問題 / Drawback, Risk

<!--
機能実装にともない想定される問題があれば書く。
-->

### 著作権・知的財産権関連のリスク

ゲーム内のセリフやキャラクター設定の引用範囲の判断が困難という話はあるかもしれない。

ただ今回[system-prompt.md](../personalities/shinosawa_hiro/system-prompt.md)で引用した部分はプロフィールのみで、他の篠澤広に対する洞察は私が考えたものとなる。

またゲーム内のセリフやネタバレはローカルで起動するベクトルデータベース内に持たせて、元となるテキストファイルもローカル上でのみ持つことで個人利用の範囲に収められる。

### 技術的なリスク

- ChromaDBが最低2GBのRAMを要求することで、リソースが限られた環境では動作が困難となる
- ベクトル検索の精度がキャラクターの再現性に影響する

## 他の手段 / Alternative approach

<!--
[required]
他に検討した実装方法があれば書く。他の手段がない場合はその旨を書く。
-->

### ベクトルデータベースのクラウドホスティング

ベクトルデータを複数デバイスからのアクセスできるようにするため、ベクトルデータベースをAWS、GCP等のクラウドプロバイダー上でホスティングすることを検討した。

ただベクトルデータベースは最低2GBのRAMが必要となり、無料の範囲内には収まらない。AWS EC2の `t3.small` やGCPの `e2-small` を使った場合にだいたい1時間あたり2セント、月額で15ドルほどかかってしまう。

またローカル上のデータを使うのに比べて、ゲームのスクリーンショットから抽出した文字データが流出するリスクもある。

またバックアップやセキュリティ面の管理コストが増加するため、個人で使う分にはローカルでベクトルデータベースを起動しておくので十分と判断し、今回はベクトルデータベースのホスティングをやめた。

### 他のベクトルデータベースの検討

ChromaDBを使うようにしたのはAIによってサジェストされたため。場合によっては下記のベクドルデータベースを使うことも考えられる。

- [Weaviate](https://github.com/weaviate/weaviate)
- [Qdrant](https://github.com/qdrant/qdrant)

## 関連リンク / Related link

<!--
関連するissue、参考にしたリンクを書く。
-->

- [著作権法における引用について – ゲーム保存協会](https://www.gamepres.org/media/contents/fairuse/)
- [篠澤 広 ｜ 学園アイドルマスター（学マス）｜君と出会い、夢に翔ける](https://gakuen.idolmaster-official.jp/idol/hiro/)
- [「学園アイドルマスター」応援広告規程 ｜ 学園アイドルマスター（学マス）｜君と出会い、夢に翔ける](https://gakuen.idolmaster-official.jp/media/fankit/terms-of-cheering-ad/)

### プロトコル・ツールの各種ドキュメント

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction)
- [ChromaDB Documentation](https://docs.trychroma.com/docs/overview/introduction)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Task Documentation](https://taskfile.dev/)
- [mise Documentation](https://mise.jdx.dev/)
