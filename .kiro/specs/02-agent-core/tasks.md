# Implementation Plan: AgentCore 設定

## Overview

AWS AgentCore を活用した AI エージェント実行基盤の実装。CDK（TypeScript）でインフラを定義し、Strands Agents（Python）でエージェントを実装する。

## Tasks

- [ ] 1. プロジェクト構造のセットアップ

  - [ ] 1.1 Python エージェント用ディレクトリ構造を作成
    - `agents/` ディレクトリを作成
    - `agents/tools/` サブディレクトリを作成
    - `agents/__init__.py` を作成
    - `agents/tools/__init__.py` を作成
    - _Requirements: 5.1, 6.1_
  - [ ] 1.2 Python 依存関係ファイルを作成
    - `agents/requirements.txt` を作成
    - bedrock-agentcore、strands-agents、strands-agents-tools を追加
    - _Requirements: 5.1, 5.2_

- [ ] 2. AgentCore Runtime 用 IAM ロール Construct を実装

  - [ ] 2.1 AgentRuntimeConstruct を作成
    - `lib/constructs/agent/agent-runtime-construct.ts` を作成
    - AgentCore Runtime 用の IAM ロールを定義
    - Bedrock モデル呼び出し権限を付与
    - S3 読み取り権限を付与
    - _Requirements: 1.1, 1.2, 5.3_
  - [ ]\* 2.2 AgentRuntimeConstruct のスナップショットテストを作成
    - IAM ロールの権限が正しく設定されていることを検証
    - _Requirements: 6.3_

- [ ] 3. AgentCore Gateway Construct を実装

  - [ ] 3.1 AgentGatewayConstruct を作成
    - `lib/constructs/agent/agent-gateway-construct.ts` を作成
    - Gateway 設定用の型定義を追加
    - CLI コマンド生成ヘルパーを実装
    - _Requirements: 2.1, 2.2_
  - [ ]\* 3.2 AgentGatewayConstruct のスナップショットテストを作成
    - Gateway 設定が正しく生成されることを検証
    - _Requirements: 2.3_

- [ ] 4. AgentCore Memory Construct を実装

  - [ ] 4.1 AgentMemoryConstruct を作成
    - `lib/constructs/agent/agent-memory-construct.ts` を作成
    - Memory 設定用の型定義を追加
    - STM/LTM 戦略設定を実装
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ]\* 4.2 AgentMemoryConstruct のスナップショットテストを作成
    - Memory 設定が正しく生成されることを検証
    - _Requirements: 4.4_

- [ ] 5. Checkpoint - インフラ Construct の確認

  - すべての CDK Construct が正しく実装されていることを確認
  - テストが通ることを確認
  - ユーザーに質問があれば確認

- [ ] 6. Meeting Agent の基本実装

  - [ ] 6.1 BedrockAgentCoreApp ラッパーを実装
    - `agents/meeting_agent.py` を作成
    - BedrockAgentCoreApp をインポートして初期化
    - @app.entrypoint デコレータでエントリポイントを定義
    - _Requirements: 1.1, 5.2_
  - [ ] 6.2 AgentCore Memory 統合を実装
    - AgentCoreMemoryConfig を設定
    - AgentCoreMemorySessionManager を作成
    - セッション ID とアクター ID の管理を実装
    - _Requirements: 4.1, 4.3_
  - [ ] 6.3 Strands Agent を作成
    - Nova 2 Lite モデルを設定
    - システムプロンプトを定義
    - session_manager を Agent に渡す
    - _Requirements: 5.1, 5.3_

- [ ] 7. エージェントツールの実装

  - [ ] 7.1 summarize_transcript ツールを実装
    - `agents/tools/summarize.py` を作成
    - @tool デコレータでツールを定義
    - 入力スキーマを Pydantic で定義
    - _Requirements: 5.1_
  - [ ] 7.2 extract_tasks ツールを実装
    - `agents/tools/extract_tasks.py` を作成
    - @tool デコレータでツールを定義
    - 入力スキーマを Pydantic で定義
    - _Requirements: 5.1_
  - [ ]\* 7.3 ツール入力検証のプロパティテストを作成
    - **Property 3: ツール入力検証**
    - **Validates: Requirements 5.1**

- [ ] 8. AgentCore 設定ファイルを作成

  - [ ] 8.1 .bedrock_agentcore.yaml を作成
    - `agents/.bedrock_agentcore.yaml` を作成
    - エントリポイント、ランタイム、デプロイタイプを設定
    - Memory 設定を追加
    - 環境変数を設定
    - _Requirements: 1.1, 4.1, 4.2_

- [ ] 9. エラーハンドリングを実装

  - [ ] 9.1 エラーハンドリングロジックを追加
    - SessionNotFoundError の処理
    - ModelAccessDeniedError の処理
    - 一般的な例外の処理
    - ログ出力を追加
    - _Requirements: 1.3, 1.4_

- [ ] 10. Checkpoint - エージェント実装の確認

  - エージェントコードが正しく実装されていることを確認
  - 設定ファイルが正しいことを確認
  - ユーザーに質問があれば確認

- [ ] 11. 共通型定義を更新

  - [ ] 11.1 lib/shared/types.ts を更新
    - GatewayConfig 型を追加
    - MemoryConfig 型を追加
    - AgentRuntimeConfig 型を追加
    - _Requirements: 2.1, 4.1_

- [ ] 12. メインスタックに AgentCore Construct を統合

  - [ ] 12.1 MainStack を更新
    - AgentRuntimeConstruct をインスタンス化
    - AgentGatewayConstruct をインスタンス化
    - AgentMemoryConstruct をインスタンス化
    - 出力値を追加（Runtime ARN、Gateway URL、Memory ID）
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 13. Final Checkpoint - 全体確認
  - すべてのテストが通ることを確認
  - CDK synth が成功することを確認
  - ユーザーに質問があれば確認

## Notes

- タスクに `*` マークがあるものはオプションで、MVP では省略可能
- 各タスクは特定の要件を参照しており、トレーサビリティを確保
- チェックポイントで段階的に検証を行う
- プロパティテストは Hypothesis ライブラリを使用
