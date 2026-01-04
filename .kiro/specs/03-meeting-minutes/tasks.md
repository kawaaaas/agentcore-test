# 議事録生成機能 実装タスク

## 概要

議事録生成機能の実装タスク一覧。Strands Agents SDK（Python）を使用してエージェントを実装し、AgentCore Memory との連携、Slack 承認フロー、S3 保存を実現する。

## タスク

- [x] 1. プロジェクト構造とデータモデルのセットアップ

  - [x] 1.1 Python プロジェクト構造の作成

    - `agents/` ディレクトリ構造を作成
    - `pyproject.toml` または `requirements.txt` で依存関係を定義
    - Hypothesis、pytest、pydantic、strands-agents を含める
    - _Requirements: 1.1, 2.1_

  - [x] 1.2 データモデルの実装

    - `agents/models/minutes.py` に `ActionItem`, `Minutes`, `MinutesMetadata` を実装
    - `agents/models/approval.py` に `ApprovalStatus`, `PendingMinutesRecord`, `PendingMinutesBlob` を実装
    - Pydantic BaseModel を使用して型安全に定義
    - _Requirements: 2.2, 4.3, 4.4_

  - [ ]\* 1.3 データモデルのプロパティテスト
    - **Property 3: 議事録構造の完全性**
    - **Validates: Requirements 2.2, 2.5**

- [-] 2. 書き起こしテキストの検証機能

  - [x] 2.1 validate_transcript 関数の実装

    - `agents/tools/validate.py` に実装
    - UTF-8 エンコーディングのサポート
    - 空ファイルチェック
    - ファイルサイズ検証（1MB 上限）
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

  - [ ]\* 2.2 ファイルサイズ検証のプロパティテスト

    - **Property 2: ファイルサイズ検証**
    - **Validates: Requirements 1.4, 1.5**

  - [ ]\* 2.3 UTF-8 エンコーディングのプロパティテスト
    - **Property 1: UTF-8 エンコーディングの保持**
    - **Validates: Requirements 1.2**

- [x] 3. チェックポイント - 検証機能の確認

  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する

- [x] 4. Minutes Formatter の実装

  - [x] 4.1 to_markdown 関数の実装

    - `agents/tools/formatter.py` に `MinutesFormatter` クラスを実装
    - H1 見出しでタイトル、H2 見出しで各セクション
    - アクションアイテムはチェックボックス形式（`- [ ]`）
    - 参加者が空の場合は「不明」を出力
    - _Requirements: 3.1, 3.2, 3.3, 2.5_

  - [x] 4.2 from_markdown 関数の実装

    - Markdown 文字列から Minutes オブジェクトを復元
    - 正規表現でセクションをパース
    - _Requirements: 3.4, 5.4_

  - [x] 4.3 generate_filename 関数の実装

    - `{YYYY-MM-DD}_{title-slug}.md` 形式でファイル名を生成
    - タイトルから特殊文字を除去してスラッグ化
    - _Requirements: 5.2_

  - [ ]\* 4.4 Markdown ラウンドトリップのプロパティテスト

    - **Property 4: Markdown ラウンドトリップ**
    - **Validates: Requirements 3.4, 5.4**

  - [ ]\* 4.5 Markdown 見出し構造のプロパティテスト

    - **Property 5: Markdown 見出し構造**
    - **Validates: Requirements 3.1, 3.2**

  - [ ]\* 4.6 アクションアイテム形式のプロパティテスト

    - **Property 6: アクションアイテムのチェックボックス形式**
    - **Validates: Requirements 3.3**

  - [ ]\* 4.7 ファイル名形式のプロパティテスト
    - **Property 9: ファイル名形式**
    - **Validates: Requirements 5.2**

- [x] 5. チェックポイント - Formatter の確認

  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する

- [x] 6. リトライハンドラの実装

  - [x] 6.1 with_retry デコレータの実装

    - `agents/utils/retry.py` に実装
    - 最大 3 回のリトライ
    - 指数バックオフ（base_delay \* 2^attempt）
    - ログ出力
    - _Requirements: 6.1, 6.3_

  - [ ]\* 6.2 リトライ動作のプロパティテスト

    - **Property 11: リトライ動作**
    - **Validates: Requirements 6.1**

  - [ ]\* 6.3 エラーログ記録のプロパティテスト
    - **Property 12: エラーログ記録**
    - **Validates: Requirements 6.3**

- [x] 7. Slack 承認フローの実装

  - [x] 7.1 Block Kit メッセージ生成の実装

    - `agents/tools/approval.py` に `ApprovalFlow` クラスを実装
    - `create_approval_message()` で承認メッセージを生成
    - Slack メッセージ制限（4000 文字）を考慮した省略処理
    - _Requirements: 4.1, 4.2_

  - [x] 7.2 修正モーダル生成の実装

    - `create_revision_modal()` で修正入力フォームを生成
    - _Requirements: 4.4_

  - [x] 7.3 アクションハンドラの実装

    - `handle_action()` で承認/修正アクションを処理
    - 状態遷移ロジック（PENDING → APPROVED / REVISION_REQUESTED）
    - _Requirements: 4.3, 4.4, 4.5_

  - [ ]\* 7.4 Block Kit 構造のプロパティテスト

    - **Property 7: Block Kit 構造の妥当性**
    - **Validates: Requirements 4.2**

  - [ ]\* 7.5 承認フロー状態遷移のプロパティテスト
    - **Property 8: 承認フロー状態遷移**
    - **Validates: Requirements 4.3, 4.4**

- [x] 8. チェックポイント - 承認フローの確認

  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する

- [x] 9. 承認待ち議事録の永続化

  - [x] 9.1 save_pending_minutes の実装

    - `ApprovalFlow` クラスに永続化メソッドを追加
    - AgentCore Memory に `create_blob_event()` で議事録本体を保存
    - DynamoDB に `PendingMinutesRecord` を保存
    - _Requirements: 4.3, 7.5_

  - [x] 9.2 get_pending_minutes の実装

    - DynamoDB からメタデータを取得
    - AgentCore Memory から議事録本体を取得
    - _Requirements: 4.3, 4.4_

  - [ ]\* 9.3 承認待ち議事録永続化のプロパティテスト

    - **Property 14: 承認待ち議事録の永続化**
    - **Validates: Requirements 4.3, 4.4, 7.5**

  - [ ]\* 9.4 承認待ち議事録復元のプロパティテスト
    - **Property 15: 承認待ち議事録の復元**
    - **Validates: Requirements 4.3, 4.4**

- [x] 10. 議事録生成ツールの実装

  - [x] 10.1 generate_minutes ツールの実装

    - `agents/tools/generator.py` に実装
    - Strands `@tool` デコレータを使用
    - Bedrock Nova 2 Lite を呼び出して議事録を生成
    - 過去の修正パターンをプロンプトに含める
    - _Requirements: 2.1, 2.3, 2.4, 7.3_

  - [x] 10.2 AgentCore Memory からの修正パターン検索

    - LTM からセマンティック検索で類似パターンを取得
    - _Requirements: 7.2, 7.3_

  - [ ]\* 10.3 修正パターン適用のプロパティテスト
    - **Property 13: 修正パターンのプロンプト適用**
    - **Validates: Requirements 7.3**

- [x] 11. チェックポイント - 生成機能の確認

  - すべてのテストが通ることを確認し、不明点があればユーザーに質問する

- [x] 12. エージェント統合

  - [x] 12.1 Meeting Agent の定義

    - `agents/meeting_agent.py` にメインエージェントを実装
    - Strands Agent クラスを使用
    - システムプロンプトを設定
    - ツール（validate, generate, format）を登録
    - _Requirements: 2.1_

  - [x] 12.2 AgentCore Memory 連携の設定

    - `AgentCoreMemoryConfig` でメモリ設定
    - STM/LTM の使い分け
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [x] 12.3 S3 保存機能の実装

    - 承認された議事録を Minutes_Bucket に保存
    - メタデータを付与して保存
    - _Requirements: 5.1, 5.3_

  - [ ]\* 12.4 メタデータ完全性のプロパティテスト
    - **Property 10: メタデータの完全性**
    - **Validates: Requirements 5.3**

- [x] 13. エラー通知の実装

  - [x] 13.1 エラー通知メッセージの生成

    - `agents/utils/error.py` に `create_error_notification()` を実装
    - Block Kit 形式でエラー内容を表示
    - _Requirements: 6.2_

  - [x] 13.2 Slack へのエラー通知送信
    - リトライ失敗時に Slack に通知
    - _Requirements: 6.2_

- [x] 14. 最終チェックポイント
  - すべてのテストが通ることを確認
  - 統合テストを実行
  - 不明点があればユーザーに質問する

## 備考

- タスクに `*` が付いているものはオプション（プロパティテスト）
- 各プロパティテストは Hypothesis を使用して最低 100 回の反復を実行
- AgentCore Memory のモック実装が必要な場合は統合テストで対応
