# Requirements Document

## Introduction

AWS AgentCore を活用した AI エージェント実行基盤の構築。Strands Agents SDK と連携し、議事録生成・タスク抽出ワークフローを実行するエージェントの Runtime、Gateway、Identity、Memory 機能を提供する。

## Glossary

- **AgentCore**: AWS が提供するエージェント実行基盤サービス
- **Runtime**: エージェントの非同期実行とセッション管理を担当するコンポーネント
- **Gateway**: MCP 統合と外部 API 接続を担当するコンポーネント
- **Identity**: API キーやトークンの安全な管理を担当するコンポーネント
- **Memory**: 短期記憶（STM）と長期記憶（LTM）を管理するコンポーネント
- **Strands_Agents**: TypeScript ベースのエージェント SDK
- **MCP**: Model Context Protocol、ツール接続の標準プロトコル
- **HITL**: Human-in-the-Loop、人間による承認フロー

## Requirements

### Requirement 1: エージェント Runtime 設定

**User Story:** As a 開発者, I want to AgentCore Runtime を設定する, so that エージェントを非同期で実行しセッションを維持できる。

#### Acceptance Criteria

1. WHEN エージェントが起動される THEN THE Runtime SHALL 最大 8 時間の非同期実行をサポートする
2. WHEN セッションが開始される THEN THE Runtime SHALL ステートフルなセッション管理を提供する
3. WHEN HITL 承認が必要な場合 THEN THE Runtime SHALL 承認待ち状態で実行を一時停止する
4. WHEN 承認が完了した場合 THEN THE Runtime SHALL 中断した処理を再開する

### Requirement 2: Gateway 設定

**User Story:** As a 開発者, I want to AgentCore Gateway を設定する, so that MCP 経由で外部ツールに接続できる。

#### Acceptance Criteria

1. WHEN Gateway が設定される THEN THE Gateway SHALL MCP プロトコルをサポートする
2. WHEN 外部 API（Slack、GitHub）への接続が必要な場合 THEN THE Gateway SHALL Lambda を介さずに直接接続を提供する
3. WHEN ツール呼び出しが発生した場合 THEN THE Gateway SHALL 適切なエンドポイントにリクエストをルーティングする

### Requirement 3: Identity 設定

**User Story:** As a 開発者, I want to AgentCore Identity を設定する, so that API キーを安全に管理できる。

#### Acceptance Criteria

1. WHEN 外部サービスの認証情報が必要な場合 THEN THE Identity SHALL マネージド・トークン・インジェクションを提供する
2. WHEN API キーが設定される THEN THE Identity SHALL 暗号化されたストレージに保存する
3. WHEN エージェントがツールを実行する THEN THE Identity SHALL 必要な認証情報を自動的に注入する

### Requirement 4: Memory 設定

**User Story:** As a 開発者, I want to AgentCore Memory を設定する, so that エージェントが過去の情報を活用できる。

#### Acceptance Criteria

1. WHEN 会話イベントが発生した場合 THEN THE Memory SHALL 短期記憶（STM）に保存する
2. WHEN STM に保存されたデータが 90 日経過した場合 THEN THE Memory SHALL 自動的に期限切れとする
3. WHEN 重要な知識が抽出された場合 THEN THE Memory SHALL 長期記憶（LTM）にベクター形式で保存する
4. WHEN 過去の知識を検索する場合 THEN THE Memory SHALL セマンティック検索を提供する

### Requirement 5: Strands Agents 連携

**User Story:** As a 開発者, I want to Strands Agents SDK と AgentCore を連携する, so that 型安全なエージェントを実行できる。

#### Acceptance Criteria

1. WHEN エージェントが定義される THEN THE Strands_Agents SHALL Zod スキーマによる型安全なツール定義をサポートする
2. WHEN エージェントが AgentCore にデプロイされる THEN THE Runtime SHALL Strands Agents 形式のエージェントを実行する
3. WHEN Bedrock モデルが呼び出される THEN THE Strands_Agents SHALL Nova 2 Lite モデルを使用する

### Requirement 6: CDK 統合

**User Story:** As a 開発者, I want to AgentCore リソースを CDK で定義する, so that インフラをコードで管理できる。

#### Acceptance Criteria

1. WHEN AgentCore リソースが定義される THEN THE CDK SHALL L2 コンストラクトを優先して使用する
2. IF L2 コンストラクトが存在しない場合 THEN THE CDK SHALL L1（Cfn）リソースを使用する
3. WHEN 検証環境にデプロイされる THEN THE CDK SHALL リソースの一括削除を可能にする設定を適用する
