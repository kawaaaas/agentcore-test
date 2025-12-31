# Slack 連携機能 要件定義

## 概要

議事録・タスク管理自動化 AI エージェントと Slack を連携し、Human-in-the-Loop（HITL）による承認フローを実現する。Block Kit を使用したインタラクティブな UI で、議事録の確認・修正、タスクの確認・登録を行う。

## 用語集（Glossary）

- **Slack_Notifier**: Slack へのメッセージ送信を担当するコンポーネント
- **Slack_Handler**: Slack からのインタラクション（ボタンクリック等）を処理するコンポーネント
- **Block_Kit**: Slack のリッチメッセージ UI フレームワーク
- **Approval_Message**: 承認/修正ボタンを含む確認メッセージ
- **Feedback_Modal**: 修正内容を入力するためのモーダルダイアログ
- **Webhook_Endpoint**: Slack からのインタラクションイベントを受信する Lambda 関数
- **Slack_Token**: Slack Bot Token（AgentCore Identity で管理）
- **Channel_ID**: メッセージを送信する Slack チャンネルの識別子
- **AgentCore_Gateway**: MCP プロトコル経由で外部 API に接続するコンポーネント
- **OpenAPI_Target**: AgentCore Gateway に登録される Slack API の接続設定

## 要件

### 要件 1: Slack 通知の送信

**ユーザーストーリー:** ユーザーとして、議事録やタスクの確認依頼を Slack で受け取りたい。これにより、普段使用しているツールで通知を確認できる。

#### 受け入れ条件

1. WHEN 議事録が生成された場合、THE Slack_Notifier SHALL 指定された Channel_ID にメッセージを送信する
2. WHEN タスクが抽出された場合、THE Slack_Notifier SHALL 指定された Channel_ID にメッセージを送信する
3. THE Slack_Notifier SHALL Block_Kit を使用してリッチなメッセージを構築する
4. IF メッセージ送信が失敗した場合、THEN THE Slack_Notifier SHALL 最大 3 回リトライする
5. IF リトライ後も失敗した場合、THEN THE Slack_Notifier SHALL エラーをログに記録する

### 要件 2: 承認メッセージの構築

**ユーザーストーリー:** ユーザーとして、議事録やタスクの内容を確認し、承認または修正を選択したい。これにより、AI の出力を人間がレビューできる。

#### 受け入れ条件

1. THE Approval_Message SHALL 議事録またはタスクの内容をプレビュー表示する
2. THE Approval_Message SHALL 「承認」ボタンを含む
3. THE Approval_Message SHALL 「修正」ボタンを含む
4. THE Approval_Message SHALL 「キャンセル」ボタンを含む
5. WHEN メッセージが 4000 文字を超える場合、THE Slack_Notifier SHALL 内容を要約して表示する
6. FOR ALL 承認メッセージ、Block_Kit JSON を生成してからパースした場合、THE Slack_Notifier SHALL 同等の構造を復元できる

### 要件 3: インタラクションの処理

**ユーザーストーリー:** ユーザーとして、Slack 上でボタンをクリックして承認や修正を行いたい。これにより、シームレスなワークフローを実現できる。

#### 受け入れ条件

1. WHEN ユーザーが「承認」ボタンをクリックした場合、THE Slack_Handler SHALL 承認イベントを AgentCore Runtime に通知する
2. WHEN ユーザーが「修正」ボタンをクリックした場合、THE Slack_Handler SHALL Feedback_Modal を表示する
3. WHEN ユーザーが「キャンセル」ボタンをクリックした場合、THE Slack_Handler SHALL 処理を中断し元のメッセージを更新する
4. WHEN インタラクションを受信した場合、THE Slack_Handler SHALL 3 秒以内に応答する
5. THE Slack_Handler SHALL インタラクションの送信者を検証する

### 要件 4: 修正フィードバックの収集

**ユーザーストーリー:** ユーザーとして、修正内容をモーダルダイアログで入力したい。これにより、詳細なフィードバックを提供できる。

#### 受け入れ条件

1. THE Feedback_Modal SHALL テキスト入力フィールドを含む
2. THE Feedback_Modal SHALL 「送信」ボタンを含む
3. THE Feedback_Modal SHALL 「キャンセル」ボタンを含む
4. WHEN 修正内容が送信された場合、THE Slack_Handler SHALL 内容を AgentCore Runtime に転送する
5. IF 修正内容が空の場合、THEN THE Feedback_Modal SHALL エラーメッセージを表示する
6. WHEN 修正内容が送信された場合、THE Slack_Handler SHALL 元のメッセージを「修正中」ステータスに更新する

### 要件 5: メッセージの更新

**ユーザーストーリー:** ユーザーとして、処理の進捗状況を元のメッセージで確認したい。これにより、チャンネルが新しいメッセージで埋まることを防げる。

#### 受け入れ条件

1. WHEN 承認が完了した場合、THE Slack_Notifier SHALL 元のメッセージを「承認済み」ステータスに更新する
2. WHEN 修正が完了した場合、THE Slack_Notifier SHALL 元のメッセージを更新して新しい内容を表示する
3. WHEN エラーが発生した場合、THE Slack_Notifier SHALL 元のメッセージを「エラー」ステータスに更新する
4. THE Slack_Notifier SHALL 更新時にタイムスタンプを表示する

### 要件 6: リマインダー機能

**ユーザーストーリー:** ユーザーとして、未対応の確認依頼についてリマインダーを受け取りたい。これにより、対応漏れを防げる。

#### 受け入れ条件

1. IF 承認メッセージに 24 時間以内に応答がない場合、THEN THE Slack_Notifier SHALL リマインダーメッセージを送信する
2. THE Slack_Notifier SHALL リマインダーを最大 3 回まで送信する
3. IF 3 回のリマインダー後も応答がない場合、THEN THE Slack_Notifier SHALL タイムアウトとして処理を終了する
4. WHEN リマインダーを送信する場合、THE Slack_Notifier SHALL 元のメッセージへのリンクを含める

### 要件 7: 認証情報の管理

**ユーザーストーリー:** 開発者として、Slack API トークンを安全に管理したい。これにより、セキュリティリスクを軽減できる。

#### 受け入れ条件

1. THE Slack_Token SHALL AgentCore Identity で管理される
2. WHEN Slack API を呼び出す場合、THE Slack_Notifier SHALL AgentCore Identity からトークンを取得する
3. THE Slack_Token SHALL コードやログに平文で出力されない
4. IF トークンが無効な場合、THEN THE Slack_Notifier SHALL エラーを通知し処理を中断する

### 要件 8: AgentCore Gateway 連携

**ユーザーストーリー:** 開発者として、AgentCore Gateway 経由で Slack API に接続したい。これにより、Lambda を介さずに直接 Slack と通信できる。

#### 受け入れ条件

1. THE Slack_Notifier SHALL AgentCore Gateway の OpenAPI Schema Target として Slack API を登録する
2. WHEN Gateway Target を作成する場合、THE Gateway SHALL Slack Web API の OpenAPI スキーマを使用する
3. THE Gateway SHALL API Key 認証（Bot Token）を使用して Slack API に接続する
4. WHEN エージェントが Slack ツールを呼び出す場合、THE Gateway SHALL MCP プロトコル経由でリクエストをルーティングする
5. THE Gateway SHALL Slack API のレート制限を考慮したリトライ機能を提供する

### 要件 9: Webhook エンドポイント

**ユーザーストーリー:** 開発者として、Slack からのインタラクションイベントを受信するエンドポイントを設定したい。これにより、ボタンクリック等のイベントを処理できる。

#### 受け入れ条件

1. THE Webhook_Endpoint SHALL HTTPS でアクセス可能である
2. WHEN Slack からリクエストを受信した場合、THE Webhook_Endpoint SHALL 署名を検証する
3. IF 署名検証が失敗した場合、THEN THE Webhook_Endpoint SHALL リクエストを拒否する
4. THE Webhook_Endpoint SHALL Lambda 関数として実装される
5. WHEN URL 検証リクエストを受信した場合、THE Webhook_Endpoint SHALL チャレンジレスポンスを返す
6. WHEN インタラクションイベントを受信した場合、THE Webhook_Endpoint SHALL AgentCore Runtime に通知する

## 制約事項

- Slack Free Plan の制限内で動作する
- メッセージは 4000 文字以内に収める
- Block Kit の制限（ブロック数、アクション数）を遵守する
- Slack API のレート制限を考慮する
- 日本語メッセージをサポートする
