# プロジェクト概要: 議事録・タスク管理自動化 AI エージェント

## 目的

議事録の生成からタスクの抽出、管理ツールへの登録までを自律的に行う AI エージェントを構築する。
「安価・簡素・高機能」な構成を目指す個人検証プロジェクト。

## テクノロジースタック

| カテゴリ      | 選定ツール                               | 備考                                               |
| ------------- | ---------------------------------------- | -------------------------------------------------- |
| Agent SDK     | Strands Agents (Python)                  | AgentCore Memory/Identity 統合、Pydantic スキーマ  |
| インフラ      | AWS CDK (TypeScript)                     | 型安全なインフラ定義                               |
| 実行基盤      | AWS AgentCore (Runtime/Identity/Gateway) | エージェントの実行、セッション維持、認証情報の保護 |
| AI モデル     | Amazon Bedrock (Nova 2 Lite)             | コストパフォーマンス重視                           |
| 通知・確認 UI | Slack (Free Plan)                        | Block Kit による承認フロー                         |
| タスク管理    | GitHub Issues                            | API 操作が容易                                     |
| プロトコル    | MCP (Model Context Protocol)             | ツール接続の標準化                                 |

## ワークフロー

1. **入力**: 会議の書き起こしテキストを S3 へ保存
2. **議事録生成**: Nova 2 Lite が要約・議事録を生成
3. **議事録確認**: Slack で承認/修正フロー
4. **タスク抽出**: 議事録から Action Items を抽出
5. **タスク確認**: Slack で登録実行/修正フロー
6. **タスク登録**: GitHub Issues にチケット作成

## AgentCore ネイティブ機能

- **Runtime**: 非同期実行（最大 8 時間）、ステートフル・セッション、HITL（Human-in-the-Loop）の承認待ち機能
- **Gateway**: MCP 統合、Lambda レス・ツール接続（GitHub、Slack 等の外部 API）
- **Identity**: マネージド・トークン・インジェクション（API キーの安全な管理）
- **Memory**: 永続的な知識ストレージ
  - **Short-term Memory (STM)**: 会話イベントの保持（自動期限切れ、デフォルト 90 日）
  - **Long-term Memory (LTM)**: セマンティックメモリ（ベクター検索による事実・知識の保存）
  - 活用例: 過去の修正指示パターンの学習、ユーザーの好みや文体の記憶
