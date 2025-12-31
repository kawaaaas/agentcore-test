# タスク抽出機能 実装タスク

## 概要

承認済み議事録からタスクを抽出し、Slack 確認フローを経て GitHub Issues 登録準備を行う機能の実装。

## タスク一覧

- [ ] 1. データモデルとバリデーションの実装

  - [ ] 1.1 Task, TaskList, Priority データモデルを実装する

    - `agents/tools/task_models.py` に Pydantic モデルを定義
    - Task: id, title, description, assignee, due_date, priority, source_quote, created_at
    - TaskList: session_id, minutes_id, tasks, status, created_at, updated_at
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [ ] 1.2 Task_Validator を実装する

    - `agents/tools/task_validator.py` に検証ロジックを実装
    - タイトル空チェック、100 文字制限、優先度検証、日付形式検証
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]\* 1.3 Property 2: タスク検証のプロパティテストを実装する
    - **Property 2: タスク検証**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [ ] 2. Markdown フォーマッターの実装

  - [ ] 2.1 Task_Formatter の to_markdown を実装する

    - `agents/tools/task_formatter.py` に実装
    - 優先度ソート、チェックボックス形式、担当者・期限表示
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 2.2 Task_Formatter の from_markdown を実装する

    - Markdown パース、TaskList 復元
    - _Requirements: 4.5_

  - [ ]\* 2.3 Property 3: Markdown 出力形式のプロパティテストを実装する

    - **Property 3: Markdown 出力形式**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [ ]\* 2.4 Property 4: Markdown ラウンドトリップのプロパティテストを実装する
    - **Property 4: Markdown ラウンドトリップ**
    - **Validates: Requirements 4.5**

- [ ] 3. チェックポイント - データモデルとフォーマッターの検証

  - すべてのテストが通ることを確認、問題があればユーザーに確認

- [ ] 4. 重複検出の実装

  - [ ] 4.1 Duplicate_Detector を実装する

    - `agents/tools/duplicate_detector.py` に実装
    - calculate_similarity: Levenshtein 距離ベースの類似度計算
    - detect_duplicates: 類似度 80%以上で重複検出
    - merge_duplicates: 詳細な説明を持つタスクを優先して統合
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]\* 4.2 Property 8: 類似度閾値のプロパティテストを実装する

    - **Property 8: 類似度閾値**
    - **Validates: Requirements 6.3**

  - [ ]\* 4.3 Property 9: 重複統合のプロパティテストを実装する
    - **Property 9: 重複統合**
    - **Validates: Requirements 6.1, 6.2, 6.4**

- [ ] 5. タスク抽出の実装

  - [ ] 5.1 Task_Extractor を実装する

    - `agents/tools/extract_tasks.py` に @tool デコレータで実装
    - Nova 2 Lite を使用した議事録解析
    - アクションアイテムセクション優先、暗黙的タスク抽出
    - 優先度推定ロジック（high/medium/low）
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6_

  - [ ]\* 5.2 Property 1: タスク構造の完全性のプロパティテストを実装する
    - **Property 1: タスク構造の完全性**
    - **Validates: Requirements 2.1, 2.3**

- [ ] 6. 承認フローの実装

  - [ ] 6.1 Block Kit メッセージ生成を実装する

    - `agents/tools/task_approval_flow.py` に実装
    - タスク一覧プレビュー、承認/修正/キャンセルボタン、個別削除ボタン
    - _Requirements: 5.2_

  - [ ] 6.2 承認フロー状態遷移を実装する

    - approve → APPROVED, request_revision → REVISION_REQUESTED, cancel → CANCELLED
    - タスク追加・削除操作
    - _Requirements: 5.3, 5.4, 5.5, 5.6_

  - [ ]\* 6.3 Property 5: Block Kit 構造の妥当性のプロパティテストを実装する

    - **Property 5: Block Kit 構造の妥当性**
    - **Validates: Requirements 5.2**

  - [ ]\* 6.4 Property 6: 承認フロー状態遷移のプロパティテストを実装する

    - **Property 6: 承認フロー状態遷移**
    - **Validates: Requirements 5.3, 5.4**

  - [ ]\* 6.5 Property 7: TaskList 操作のプロパティテストを実装する
    - **Property 7: TaskList 操作**
    - **Validates: Requirements 5.5, 5.6**

- [ ] 7. チェックポイント - 抽出と承認フローの検証

  - すべてのテストが通ることを確認、問題があればユーザーに確認

- [ ] 8. 永続化の実装

  - [ ] 8.1 Task_Persistence を実装する

    - `agents/tools/task_persistence.py` に実装
    - save_pending_tasks: Memory STM + DynamoDB Session_Table
    - load_pending_tasks: session_id をキーに復元
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [ ]\* 8.2 Property 11: 承認待ち TaskList の永続化ラウンドトリップのプロパティテストを実装する
    - **Property 11: 承認待ち TaskList の永続化ラウンドトリップ**
    - **Validates: Requirements 8.4**

- [ ] 9. エラーハンドリングとリトライの実装

  - [ ] 9.1 リトライロジックを実装する

    - 最大 3 回リトライ、指数バックオフ
    - Bedrock API、Memory、DynamoDB、Slack API のエラー対応
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]\* 9.2 Property 10: リトライ動作のプロパティテストを実装する
    - **Property 10: リトライ動作**
    - **Validates: Requirements 7.1**

- [ ] 10. AgentCore Memory 連携の実装

  - [ ] 10.1 修正パターン学習を実装する

    - 修正内容を LTM に保存
    - 過去の修正パターンを LTM から検索
    - 類似パターンの適用
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 10.2 短期記憶（STM）連携を実装する
    - 確認フロー中の会話を STM に保存
    - _Requirements: 9.5_

- [ ] 11. 最終チェックポイント - 全機能の検証
  - すべてのテストが通ることを確認、問題があればユーザーに確認

## 備考

- タスクに `*` が付いているものはオプション（プロパティテスト）
- 各タスクは前のタスクに依存するため、順番に実装する
- プロパティテストは Hypothesis（Python）を使用、最小 100 回実行
