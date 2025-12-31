# Slack 連携機能 実装タスク

## 概要

AgentCore Gateway 経由で Slack Web API に接続し、Block Kit を使用したインタラクティブな承認フローを実装する。

## タスク

- [ ] 1. Block Kit Builder の実装

  - [ ] 1.1 Block Kit Builder の基本構造を作成

    - `agents/tools/block_kit_builder.py` を作成
    - Pydantic モデルで Block Kit の型定義を実装
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]\* 1.2 Property 3: 承認メッセージ構造のプロパティテスト

    - **Property 3: 承認メッセージの構造**
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [ ] 1.3 承認メッセージ生成メソッドを実装

    - `create_approval_message()` メソッドを実装
    - 議事録/タスクのプレビュー表示
    - 承認/修正/キャンセルボタンの追加
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]\* 1.4 Property 1: Block Kit ラウンドトリップのプロパティテスト

    - **Property 1: Block Kit ラウンドトリップ**
    - **Validates: Requirements 2.6**

  - [ ] 1.5 文字数制限処理を実装

    - 4000 文字超過時の要約処理
    - テキスト切り詰め機能
    - _Requirements: 2.5_

  - [ ]\* 1.6 Property 2: 文字数制限のプロパティテスト

    - **Property 2: 文字数制限の遵守**
    - **Validates: Requirements 2.5**

  - [ ] 1.7 ステータス更新メッセージを実装

    - `create_status_message()` メソッドを実装
    - 承認済み/修正中/エラーステータス表示
    - タイムスタンプ表示
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]\* 1.8 Property 8: ステータス更新メッセージ構造のプロパティテスト

    - **Property 8: ステータス更新メッセージの構造**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

  - [ ] 1.9 リマインダーメッセージを実装

    - `create_reminder_message()` メソッドを実装
    - 元メッセージへのリンク含む
    - _Requirements: 6.4_

  - [ ]\* 1.10 Property 9: リマインダーメッセージ構造のプロパティテスト

    - **Property 9: リマインダーメッセージの構造**
    - **Validates: Requirements 6.4**

  - [ ] 1.11 フィードバックモーダルを実装

    - `create_feedback_modal()` メソッドを実装
    - テキスト入力フィールド、送信/キャンセルボタン
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]\* 1.12 Property 10: モーダル構造のプロパティテスト
    - **Property 10: モーダルの構造**
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 2. チェックポイント - Block Kit Builder

  - すべてのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 3. Slack Handler の実装

  - [ ] 3.1 Slack Handler の基本構造を作成

    - `agents/tools/slack_handler.py` を作成
    - ActionType enum の定義
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 3.2 署名検証機能を実装

    - `verify_signature()` メソッドを実装
    - HMAC-SHA256 による署名検証
    - タイムスタンプ検証（5 分以内）
    - _Requirements: 9.2, 9.3_

  - [ ]\* 3.3 Property 4: 署名検証のプロパティテスト

    - **Property 4: 署名検証の正確性**
    - **Validates: Requirements 9.2, 9.3**

  - [ ]\* 3.4 Property 5: タイムスタンプ検証のプロパティテスト

    - **Property 5: タイムスタンプ検証**
    - **Validates: Requirements 9.2**

  - [ ] 3.5 インタラクションパース機能を実装

    - `parse_interaction()` メソッドを実装
    - ペイロードの JSON パース
    - _Requirements: 3.4_

  - [ ] 3.6 ブロックアクション処理を実装

    - `handle_block_action()` メソッドを実装
    - 承認/修正/キャンセルの分岐処理
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]\* 3.7 Property 6: アクション処理のプロパティテスト

    - **Property 6: アクション処理の状態遷移**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ] 3.8 ビュー送信処理を実装

    - `handle_view_submission()` メソッドを実装
    - 修正内容の抽出と検証
    - 空入力のエラーハンドリング
    - _Requirements: 4.4, 4.5, 4.6_

  - [ ]\* 3.9 Property 7: 空の修正内容拒否のプロパティテスト
    - **Property 7: 空の修正内容の拒否**
    - **Validates: Requirements 4.5**

- [ ] 4. チェックポイント - Slack Handler

  - すべてのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 5. Slack Notifier の実装

  - [ ] 5.1 Slack Notifier の基本構造を作成

    - `agents/tools/slack_notifier.py` を作成
    - `@tool` デコレータでツール定義
    - _Requirements: 1.1, 1.2_

  - [ ] 5.2 メッセージ送信機能を実装

    - `send_message()` メソッドを実装
    - Block Kit メッセージの送信
    - リトライ機能（最大 3 回）
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 5.3 メッセージ更新機能を実装

    - `update_message()` メソッドを実装
    - ステータス更新処理
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 5.4 モーダル表示機能を実装

    - `open_modal()` メソッドを実装
    - trigger_id を使用したモーダル表示
    - _Requirements: 3.2_

  - [ ] 5.5 リマインダー送信機能を実装
    - `send_reminder()` メソッドを実装
    - リマインダー回数管理
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 6. チェックポイント - Slack Notifier

  - すべてのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 7. Webhook Lambda の実装

  - [ ] 7.1 Lambda 関数の基本構造を作成

    - `lambda/slack-webhook/handler.ts` を作成
    - イベントハンドラの定義
    - _Requirements: 9.4_

  - [ ] 7.2 URL 検証処理を実装

    - チャレンジレスポンスの返却
    - _Requirements: 9.5_

  - [ ] 7.3 署名検証処理を実装

    - Slack Signing Secret による検証
    - 不正リクエストの拒否
    - _Requirements: 9.2, 9.3_

  - [ ] 7.4 インタラクションイベント処理を実装

    - ペイロードのパース
    - AgentCore Runtime への通知
    - _Requirements: 9.6_

  - [ ] 7.5 3 秒以内応答の実装
    - 即時 200 応答
    - 非同期処理への委譲
    - _Requirements: 3.4_

- [ ] 8. チェックポイント - Webhook Lambda

  - すべてのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 9. CDK Construct の実装

  - [ ] 9.1 Slack Construct の基本構造を作成

    - `lib/constructs/notification/slack-construct.ts` を作成
    - Props インターフェースの定義
    - _Requirements: 9.1, 9.4_

  - [ ] 9.2 API Gateway の設定

    - REST API の作成
    - HTTPS エンドポイントの設定
    - _Requirements: 9.1_

  - [ ] 9.3 Lambda 関数の設定

    - Webhook Lambda のデプロイ
    - 環境変数の設定
    - _Requirements: 9.4_

  - [ ] 9.4 DynamoDB テーブルの設定

    - SlackMessageRecord テーブルの作成
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 9.5 Secrets Manager の設定
    - Slack Signing Secret の管理
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 10. チェックポイント - CDK Construct

  - CDK スナップショットテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 11. 統合とワイヤリング

  - [ ] 11.1 メインスタックへの統合

    - `lib/stacks/main-stack.ts` に Slack Construct を追加
    - 他の Construct との連携設定

  - [ ] 11.2 エージェントへのツール登録
    - `agents/meeting_agent.py` に Slack ツールを追加
    - ツールのインポートと登録

- [ ] 12. 最終チェックポイント
  - すべてのテストが通ることを確認
  - 不明点があればユーザーに確認

## 備考

- `*` マークのタスクはオプション（プロパティテスト）
- 各タスクは要件への参照を含む
- チェックポイントで段階的に検証
- プロパティテストは Hypothesis（Python）を使用
