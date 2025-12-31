# Implementation Plan: AgentCore 設定

## Overview

AWS AgentCore を活用した AI エージェント実行基盤の実装。CDK（TypeScript）の L1 リソース（CfnXxx）でインフラを定義し、Strands Agents（Python）でエージェントを実装する。

## Tasks

- [x] 1. プロジェクト構造のセットアップ

  - [x] 1.1 Python エージェント用ディレクトリ構造を作成
    - `agents/` ディレクトリを作成
    - `agents/tools/` サブディレクトリを作成
    - `agents/__init__.py` を作成
    - `agents/tools/__init__.py` を作成
    - _Requirements: 5.1, 6.1_
  - [x] 1.2 Python 依存関係ファイルを作成
    - `agents/requirements.txt` を作成
    - strands-agents、strands-agents-tools を追加
    - _Requirements: 5.1, 5.2_

- [x] 2. AgentCore Memory Construct を実装

  - [x] 2.1 AgentMemoryConstruct を作成
    - `lib/constructs/agent/agent-memory-construct.ts` を作成
    - CfnMemory（L1）を使用して AWS::BedrockAgentCore::Memory を作成
    - Name、EventExpiryDuration（7-365）を設定
    - MemoryStrategies（オプション）を設定
    - EncryptionKeyArn（オプション）を設定
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [ ]\* 2.2 AgentMemoryConstruct のスナップショットテストを作成
    - Memory 設定が正しく生成されることを検証
    - _Requirements: 3.2_

- [x] 3. AgentCore Identity Construct を実装

  - [x] 3.1 AgentIdentityConstruct を作成
    - `lib/constructs/agent/agent-identity-construct.ts` を作成
    - CfnWorkloadIdentity（L1）を使用して AWS::BedrockAgentCore::WorkloadIdentity を作成
    - Name を設定
    - AllowedResourceOauth2ReturnUrls（オプション）を設定
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ]\* 3.2 AgentIdentityConstruct のスナップショットテストを作成
    - Identity 設定が正しく生成されることを検証
    - _Requirements: 4.2_

- [x] 4. AgentCore Gateway Construct を実装

  - [x] 4.1 AgentGatewayConstruct を作成
    - `lib/constructs/agent/agent-gateway-construct.ts` を作成
    - CfnGateway（L1）を使用して AWS::BedrockAgentCore::Gateway を作成
    - Name、AuthorizerType（CUSTOM_JWT | AWS_IAM | NONE）を設定
    - ProtocolType（MCP）を設定
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 4.2 GatewayTarget 追加メソッドを実装
    - CfnGatewayTarget（L1）を使用して AWS::BedrockAgentCore::GatewayTarget を作成
    - TargetConfiguration、CredentialProviderConfigurations を設定
    - _Requirements: 2.4, 2.5_
  - [ ]\* 4.3 AgentGatewayConstruct のスナップショットテストを作成
    - Gateway 設定が正しく生成されることを検証
    - _Requirements: 2.3_

- [x] 5. AgentCore Runtime Construct を実装

  - [x] 5.1 AgentRuntimeConstruct を作成
    - `lib/constructs/agent/agent-runtime-construct.ts` を作成
    - CfnRuntime（L1）を使用して AWS::BedrockAgentCore::Runtime を作成
    - AgentRuntimeName、AgentRuntimeArtifact を設定
    - NetworkConfiguration（PUBLIC または VPC）を設定
    - LifecycleConfiguration（オプション）を設定
    - ProtocolConfiguration（MCP | HTTP | A2A）を設定
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 5.2 IAM 実行ロールを作成
    - bedrock-agentcore.amazonaws.com を信頼するロールを作成
    - Bedrock モデル呼び出し権限を付与
    - CloudWatch Logs 権限を付与
    - _Requirements: 6.3_
  - [x] 5.3 RuntimeEndpoint を作成
    - CfnRuntimeEndpoint（L1）を使用して AWS::BedrockAgentCore::RuntimeEndpoint を作成
    - AgentRuntimeId、Name を設定
    - _Requirements: 1.5_
  - [ ]\* 5.4 AgentRuntimeConstruct のスナップショットテストを作成
    - Runtime 設定が正しく生成されることを検証
    - IAM ロールの権限が正しく設定されていることを検証
    - _Requirements: 1.2, 6.3_

- [x] 6. Checkpoint - インフラ Construct の確認

  - すべての CDK Construct が正しく実装されていることを確認
  - テストが通ることを確認
  - ユーザーに質問があれば確認

- [x] 7. Meeting Agent の基本実装

  - [x] 7.1 エージェントエントリポイントを実装
    - `agents/meeting_agent.py` を作成
    - Strands Agents SDK をインポートして初期化
    - Nova 2 Lite モデルを設定
    - システムプロンプトを定義
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 7.2 エージェントツールを実装
    - `agents/tools/summarize.py` を作成（議事録要約ツール）
    - `agents/tools/extract_tasks.py` を作成（タスク抽出ツール）
    - @tool デコレータと Pydantic スキーマでツールを定義
    - _Requirements: 5.1_

- [x] 8. 共通型定義を作成（スキップ）

  - [x] 8.1 lib/shared/types.ts を作成（スキップ：各 Construct に既に詳細な型定義が存在するため不要）
    - RuntimeConfig 型を追加
    - GatewayConfig 型を追加
    - MemoryConfig 型を追加
    - IdentityConfig 型を追加
    - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 9. メインスタックに AgentCore Construct を統合

  - [x] 9.1 MainStack を更新
    - AgentMemoryConstruct をインスタンス化
    - AgentIdentityConstruct をインスタンス化
    - AgentGatewayConstruct をインスタンス化
    - AgentRuntimeConstruct をインスタンス化
    - 出力値を追加（Runtime ARN、Gateway ARN、Memory ID、Identity ARN）
    - _Requirements: 6.1, 6.2_

- [x] 10. Final Checkpoint - 全体確認
  - すべてのテストが通ることを確認
  - CDK synth が成功することを確認
  - ユーザーに質問があれば確認

## Notes

- タスクに `*` マークがあるものはオプションで、MVP では省略可能
- 各タスクは特定の要件を参照しており、トレーサビリティを確保
- チェックポイントで段階的に検証を行う
- AgentCore は L2 コンストラクトが存在しないため、L1（CfnXxx）を使用
- CloudFormation リソース参照: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/AWS_BedrockAgentCore.html
