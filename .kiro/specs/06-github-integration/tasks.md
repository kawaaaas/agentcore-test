# GitHub 連携機能 実装タスク

## 概要

承認済みタスクを GitHub Issues に自動登録する機能の実装。AgentCore Gateway 経由で GitHub API に接続し、Strands Agents SDK でツールを実装する。

## タスク一覧

- [ ] 1. データモデルとユーティリティの実装

  - [ ] 1.1 Task、IssueRequest、IssueResult の Pydantic モデルを作成
    - `agents/models/github_models.py` に定義
    - Priority enum を含む
    - _Requirements: 2.1, 2.2, 2.3_
  - [ ]\* 1.2 Property 3: 優先度からラベルへのマッピングのプロパティテスト
    - **Property 3: 優先度からラベルへのマッピング**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [ ] 2. Issue Formatter の実装

  - [ ] 2.1 Issue_Formatter クラスを実装
    - `agents/tools/issue_formatter.py` に作成
    - `format_issue_body()`: タスクから Issue 本文を生成
    - `parse_issue_body()`: Issue 本文からタスク情報を復元
    - `create_preview()`: Slack 用プレビューテキスト生成
    - _Requirements: 2.4, 9.1, 9.2, 9.3_
  - [ ]\* 2.2 Property 2: Issue 本文ラウンドトリップのプロパティテスト
    - **Property 2: Issue 本文ラウンドトリップ**
    - **Validates: Requirements 2.2, 2.3, 2.4, 9.1, 9.2, 9.3, 9.4**

- [ ] 3. Assignee Mapper の実装

  - [ ] 3.1 Assignee_Mapper クラスを実装
    - `agents/tools/assignee_mapper.py` に作成
    - DynamoDB から担当者マッピングを取得
    - マッピングが存在しない場合は None を返す
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]\* 3.2 Property 4: 担当者マッピングのプロパティテスト
    - **Property 4: 担当者マッピング**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 4. Milestone Selector の実装

  - [ ] 4.1 Milestone_Selector クラスを実装
    - `agents/tools/milestone_selector.py` に作成
    - 期限に最も近いマイルストーンを選択
    - 期限が「未定」の場合は None を返す
    - _Requirements: 5.1, 5.2, 5.3_
  - [ ]\* 4.2 Property 5: マイルストーン選択のプロパティテスト
    - **Property 5: マイルストーン選択**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ] 5. Duplicate Detector の実装

  - [ ] 5.1 Duplicate_Detector クラスを実装
    - `agents/tools/duplicate_detector.py` に作成
    - `calculate_similarity()`: タイトル類似度の計算（Levenshtein 距離ベース）
    - `find_duplicates()`: 重複 Issue の検索
    - `is_duplicate()`: 80%以上で重複判定
    - _Requirements: 10.1, 10.2, 10.3_
  - [ ]\* 5.2 Property 12: タイトル類似度計算のプロパティテスト
    - **Property 12: タイトル類似度計算**
    - **Validates: Requirements 10.2**

- [ ] 6. チェックポイント - 基本コンポーネントの確認

  - 全てのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 7. Issue Creator の実装

  - [ ] 7.1 Issue_Creator クラスの基本実装
    - `agents/tools/github_issue.py` に作成
    - `create_issue()`: 単一 Issue の作成
    - `get_issue_url()`: 作成された Issue の URL 取得
    - リトライロジック（最大 3 回、指数バックオフ）
    - _Requirements: 2.1, 2.5, 2.6, 8.1_
  - [ ]\* 7.2 Property 10: リトライ動作のプロパティテスト
    - **Property 10: リトライ動作**
    - **Validates: Requirements 8.1**
  - [ ] 7.3 一括作成機能の実装
    - `create_issues_batch()`: 複数 Issue の一括作成
    - 各 Issue の結果を個別に追跡
    - _Requirements: 7.1, 7.2, 7.3_
  - [ ]\* 7.4 Property 8: 一括作成の完全性のプロパティテスト
    - **Property 8: 一括作成の完全性**
    - **Validates: Requirements 7.1, 7.2**

- [ ] 8. ラベル・担当者・マイルストーン設定の統合

  - [ ] 8.1 Issue_Creator にラベル設定を統合
    - 優先度からラベルへのマッピング
    - カスタムラベルの追加
    - ラベル自動作成機能
    - _Requirements: 3.1, 3.5, 3.6_
  - [ ] 8.2 Issue_Creator に担当者設定を統合
    - Assignee_Mapper を使用
    - マッピング失敗時は Assignee なしで作成
    - _Requirements: 4.1, 4.3, 4.4_
  - [ ] 8.3 Issue_Creator にマイルストーン設定を統合
    - Milestone_Selector を使用
    - 適切なマイルストーンがない場合はなしで作成
    - _Requirements: 5.1, 5.3_

- [ ] 9. Block Kit メッセージの実装

  - [ ] 9.1 Issue 登録確認メッセージの実装
    - `agents/tools/github_block_kit.py` に作成
    - Issue プレビュー表示
    - 登録/キャンセルボタン
    - _Requirements: 6.2_
  - [ ]\* 9.2 Property 6: Issue 登録確認メッセージ構造のプロパティテスト
    - **Property 6: Issue 登録確認メッセージ構造**
    - **Validates: Requirements 6.2**
  - [ ] 9.3 完了メッセージの実装
    - Issue URL を含む完了メッセージ
    - _Requirements: 6.5_
  - [ ]\* 9.4 Property 7: 完了メッセージの Issue URL 含有のプロパティテスト
    - **Property 7: 完了メッセージの Issue URL 含有**
    - **Validates: Requirements 6.5**
  - [ ] 9.5 登録結果サマリーメッセージの実装
    - 成功数、失敗数、各 Issue の詳細
    - _Requirements: 7.5_
  - [ ]\* 9.6 Property 9: 登録結果サマリー構造のプロパティテスト
    - **Property 9: 登録結果サマリー構造**
    - **Validates: Requirements 7.5**
  - [ ] 9.7 重複警告メッセージの実装
    - 既存 Issue へのリンク
    - 「それでも登録」「スキップ」ボタン
    - _Requirements: 10.3, 10.4_
  - [ ]\* 9.8 Property 13: 重複警告メッセージ構造のプロパティテスト
    - **Property 13: 重複警告メッセージ構造**
    - **Validates: Requirements 10.3, 10.4**

- [ ] 10. チェックポイント - Issue 作成機能の確認

  - 全てのテストが通ることを確認
  - 不明点があればユーザーに確認

- [ ] 11. エラーハンドリングとログ

  - [ ] 11.1 エラーハンドリングの実装
    - InvalidTokenError、PermissionError、RateLimitError の処理
    - Slack へのエラー通知
    - _Requirements: 1.7, 8.2, 8.4, 8.5_
  - [ ] 11.2 ログ記録の実装
    - エラー内容のログ記録
    - トークンがログに含まれないことを保証
    - _Requirements: 8.3, 1.6_
  - [ ]\* 11.3 Property 1, 11: トークン保護とエラーログのプロパティテスト
    - **Property 1: トークンのログ出力防止**
    - **Property 11: エラーログ記録**
    - **Validates: Requirements 1.6, 8.3**

- [ ] 12. CDK Construct の実装

  - [ ] 12.1 GitHub_Construct の作成
    - `lib/constructs/integration/github-construct.ts` に作成
    - DynamoDB テーブル（AssigneeMapping）の定義
    - _Requirements: 4.5_
  - [ ] 12.2 AgentCore Gateway Target の設定
    - GitHub REST API の OpenAPI スキーマ定義
    - Personal Access Token の Identity 設定
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 13. Strands Agent ツールの統合

  - [ ] 13.1 @tool デコレータでツールを定義
    - `create_github_issue`: 単一 Issue 作成
    - `create_github_issues_batch`: 一括 Issue 作成
    - `check_duplicate_issue`: 重複チェック
    - _Requirements: 2.1, 7.1, 10.1_
  - [ ] 13.2 Meeting Agent への統合
    - `agents/meeting_agent.py` にツールを追加
    - タスク承認後の Issue 登録フローを実装
    - _Requirements: 2.1, 6.1, 6.3, 6.4_

- [ ] 14. 最終チェックポイント
  - 全てのテストが通ることを確認
  - 不明点があればユーザーに確認

## 備考

- タスクに `*` が付いているものはオプション（プロパティテスト）
- 各タスクは Requirements への参照を含む
- チェックポイントで進捗を確認
