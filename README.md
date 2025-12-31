# 議事録・タスク管理自動化 AI エージェント

議事録の生成からタスクの抽出、管理ツールへの登録までを自律的に行う AI エージェントを構築するプロジェクト。

## 概要

会議の書き起こしテキストから議事録を自動生成し、タスクを抽出して GitHub Issues に登録するワークフローを実現します。

### ワークフロー

1. 会議の書き起こしテキストを S3 へアップロード
2. Nova 2 Lite が要約・議事録を生成
3. Slack で議事録の承認/修正フロー
4. 議事録から Action Items を抽出
5. Slack でタスク登録の確認フロー
6. GitHub Issues にチケット作成

## テクノロジースタック

| カテゴリ      | 選定ツール                   |
| ------------- | ---------------------------- |
| Agent SDK     | Strands Agents (Python)      |
| インフラ      | AWS CDK (TypeScript)         |
| 実行基盤      | AWS AgentCore                |
| AI モデル     | Amazon Bedrock (Nova 2 Lite) |
| 通知・確認 UI | Slack                        |
| タスク管理    | GitHub Issues                |
| プロトコル    | MCP                          |

## プロジェクト構成

```
.
├── lib/
│   ├── stacks/
│   │   └── main-stack.ts        # メインスタック
│   └── constructs/
│       └── storage-construct.ts # ストレージリソース
├── agents/                      # エージェントコード（Python）※今後追加
├── test/                        # テストコード
└── .kiro/
    ├── specs/                   # 機能仕様
    └── steering/                # コーディング規約
```

## セットアップ

### 前提条件

- Node.js 18+
- AWS CLI（認証情報設定済み）
- AWS CDK CLI

### インストール

```bash
npm install
```

### ビルド

```bash
npm run build
```

## 開発コマンド

| コマンド         | 説明                               |
| ---------------- | ---------------------------------- |
| `npm run build`  | TypeScript をコンパイル            |
| `npm run watch`  | 変更を監視してコンパイル           |
| `npm run test`   | Jest ユニットテストを実行          |
| `npm run lint`   | Biome で静的解析                   |
| `npm run format` | Biome でフォーマット               |
| `npx cdk synth`  | CloudFormation テンプレートを生成  |
| `npx cdk diff`   | デプロイ済みスタックとの差分を表示 |
| `npx cdk deploy` | スタックをデプロイ                 |

## 注意事項

- 検証環境向けの設定（`removalPolicy: DESTROY`）が有効になっています
- 本番環境では適切な削除保護を設定してください
