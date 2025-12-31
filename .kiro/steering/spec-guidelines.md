# Spec 作成ガイドライン

## 基本ルール

- **言語**: 日本語で記述
- **分割**: 肥大化を防ぐため、機能単位で適宜分割する

## 推奨する Spec 分割構成

```
.kiro/specs/
├── 01-infrastructure/        # インフラ基盤
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── 02-agent-core/            # AgentCore設定
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── 03-meeting-minutes/       # 議事録生成機能
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── 04-slack-integration/     # Slack連携
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── 05-task-extraction/       # タスク抽出機能
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── 06-github-integration/    # GitHub連携
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

## Spec 記述テンプレート

### requirements.md

```markdown
# [機能名] 要件定義

## 概要

[機能の目的と概要]

## 機能要件

- [ ] 要件 1
- [ ] 要件 2

## 非機能要件

- [ ] パフォーマンス要件
- [ ] セキュリティ要件

## 制約事項

- 制約 1
- 制約 2
```

### design.md

```markdown
# [機能名] 設計

## アーキテクチャ

[構成図や説明]

## コンポーネント

### コンポーネント 1

- 責務
- インターフェース

## データフロー

[処理の流れ]

## 外部参照

#[[file:path/to/related-file]]
```

### tasks.md

```markdown
# [機能名] 実装タスク

## タスク一覧

- [ ] タスク 1
  - 詳細説明
  - 完了条件
- [ ] タスク 2
```

## 外部ファイル参照

OpenAPI spec や GraphQL schema など、外部定義ファイルを参照する場合:

```markdown
#[[file:api/openapi.yaml]] #[[file:schema/schema.graphql]]
```
