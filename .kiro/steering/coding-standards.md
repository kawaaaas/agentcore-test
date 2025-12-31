# コーディング規約

## 言語・ドキュメント

- **ドキュメント言語**: 日本語（spec、README、コメント等）
- **インフラコード**: TypeScript（AWS CDK）
- **エージェントコード**: Python（Strands Agents SDK）

## AWS CDK 規約

### 基本方針

- **L2 コンストラクト優先**: 可能な限り L2 コンストラクトを使用する
- **L1 は最終手段**: L2 で実現できない場合のみ Cfn リソースを使用

### スタック分割

- 単一の stack が肥大化しないよう、関心ごとに Construct に分割する
- 各 Construct は単一責任の原則に従う
- CDK（TypeScript）と Strands Agents（Python）は同一リポジトリで管理する

```
lib/
├── stacks/
│   └── main-stack.ts          # メインスタック（Constructを組み合わせる）
├── constructs/
│   ├── storage/               # S3, DynamoDB等
│   ├── agent/                 # AgentCore関連
│   ├── notification/          # Slack連携
│   └── integration/           # GitHub連携
└── shared/
    └── types.ts               # 共通型定義（CDK用）

agents/
├── meeting_agent.py           # メインエージェント定義
├── tools/                     # エージェントツール
│   ├── summarize.py           # 議事録要約ツール
│   ├── extract_tasks.py       # タスク抽出ツール
│   └── __init__.py            # ツールエクスポート
├── requirements.txt           # Python依存関係
└── .bedrock_agentcore.yaml    # AgentCore設定
```

### 命名規則

- スタック: `PascalCase` + `Stack` suffix (例: `MeetingAgentStack`)
- コンストラクト: `PascalCase` + `Construct` suffix (例: `StorageConstruct`)
- リソース ID: `PascalCase` (例: `TranscriptBucket`)

### 検証環境対応

- **一括削除可能な設計**: `removalPolicy: RemovalPolicy.DESTROY` を設定
- S3 バケットには `autoDeleteObjects: true` を設定
- DynamoDB には `deletionProtection: false` を設定

## Strands Agents 規約（Python）

### ディレクトリ構成

- `agents/` 配下にエージェント関連コードを配置
- ツールは `agents/tools/` に機能単位で分割

### 命名規則

- エージェント: `snake_case` + `.py` (例: `meeting_agent.py`)
- ツール: `snake_case` + `.py` (例: `extract_tasks.py`)
- クラス/型定義: `PascalCase` (例: `MeetingMinutes`, `TaskItem`)

### 実装規約

- ツール定義は `@tool` デコレータと Pydantic スキーマで型安全に実装
- 各ツールは単一責任の原則に従う
- エラーハンドリングを適切に実装（try-except + 意味のあるエラーメッセージ）
- ログ出力を充実させる（処理開始・終了・エラー時）
- AgentCore Memory を活用してセッション状態を管理

### CDK との連携

- エージェントが使用する AWS リソース（S3、DynamoDB 等）は CDK で定義
- 環境変数経由でリソース ARN やエンドポイントを渡す
- AgentCore CLI でエージェントをデプロイ

## テスト

- CDK スナップショットテストを実装（TypeScript）
- エージェントのユニットテストは pytest で実装（Python）
- プロパティベーステストは Hypothesis で実装（Python）
