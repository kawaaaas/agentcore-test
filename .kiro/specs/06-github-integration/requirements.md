# GitHub 連携機能 要件定義

## 概要

承認済みタスクを GitHub Issues に自動登録する機能。AgentCore Gateway 経由で GitHub API に接続し、タスクを Issue として作成する。Slack での最終確認フローを経て、ラベル・担当者・マイルストーンを設定した Issue を登録する。

## 用語集（Glossary）

- **GitHub_Connector**: GitHub API への接続を担当するコンポーネント
- **Issue_Creator**: タスクから GitHub Issue を作成するコンポーネント
- **Issue**: GitHub に登録されるチケット
- **Label**: Issue に付与する分類タグ
- **Assignee**: Issue の担当者（GitHub ユーザー名）
- **Milestone**: Issue を紐付けるマイルストーン
- **Repository**: Issue を登録する対象リポジトリ
- **Task**: 入力となる承認済みタスク（05-task-extraction で抽出）
- **Task_List**: 承認済みタスクの集合
- **AgentCore_Gateway**: MCP プロトコル経由で GitHub API に接続するコンポーネント
- **GitHub_Token**: GitHub Personal Access Token（AgentCore Identity で管理）
- **Registration_Flow**: Slack を通じた Issue 登録の最終確認フロー
- **Issue_Template**: Issue 本文のテンプレート

## 要件

### 要件 1: GitHub API 接続

**ユーザーストーリー:** 開発者として、AgentCore Gateway 経由で GitHub API に安全に接続したい。これにより、認証情報を安全に管理しながら Issue を操作できる。

#### 受け入れ条件

1. THE GitHub_Connector SHALL AgentCore Gateway の OpenAPI Schema Target として GitHub API を登録する
2. WHEN Gateway Target を作成する場合、THE Gateway SHALL GitHub REST API の OpenAPI スキーマを使用する
3. THE Gateway SHALL Personal Access Token 認証を使用して GitHub API に接続する
4. THE GitHub_Token SHALL AgentCore Identity で管理される
5. WHEN GitHub API を呼び出す場合、THE GitHub_Connector SHALL AgentCore Identity からトークンを取得する
6. THE GitHub_Token SHALL コードやログに平文で出力されない
7. IF トークンが無効な場合、THEN THE GitHub_Connector SHALL エラーを通知し処理を中断する

### 要件 2: Issue の作成

**ユーザーストーリー:** ユーザーとして、承認済みタスクを GitHub Issue として自動登録したい。これにより、手動での Issue 作成の手間が省ける。

#### 受け入れ条件

1. WHEN タスクが承認された場合、THE Issue_Creator SHALL 指定された Repository に Issue を作成する
2. THE Issue SHALL タスクのタイトルを Issue タイトルとして設定する
3. THE Issue SHALL タスクの説明を Issue 本文として設定する
4. THE Issue SHALL Issue_Template に従って本文をフォーマットする
5. WHEN Issue を作成する場合、THE Issue_Creator SHALL 作成された Issue の URL を返す
6. FOR ALL 有効な Task、Issue を作成した場合、THE Issue_Creator SHALL 成功または失敗のステータスを返す

### 要件 3: ラベルの設定

**ユーザーストーリー:** ユーザーとして、タスクの優先度に応じたラベルを Issue に自動設定したい。これにより、Issue の分類が容易になる。

#### 受け入れ条件

1. WHEN Issue を作成する場合、THE Issue_Creator SHALL タスクの優先度に応じたラベルを設定する
2. THE Issue_Creator SHALL 優先度 high を `priority: high` ラベルにマッピングする
3. THE Issue_Creator SHALL 優先度 medium を `priority: medium` ラベルにマッピングする
4. THE Issue_Creator SHALL 優先度 low を `priority: low` ラベルにマッピングする
5. IF 指定されたラベルがリポジトリに存在しない場合、THEN THE Issue_Creator SHALL ラベルを自動作成する
6. THE Issue_Creator SHALL 追加のカスタムラベルを設定できる

### 要件 4: 担当者の設定

**ユーザーストーリー:** ユーザーとして、タスクの担当者を Issue の Assignee として自動設定したい。これにより、担当者への通知が自動化される。

#### 受け入れ条件

1. WHEN Issue を作成する場合、THE Issue_Creator SHALL タスクの担当者を Assignee として設定する
2. THE Issue_Creator SHALL 担当者名を GitHub ユーザー名にマッピングする
3. IF 担当者名が GitHub ユーザー名にマッピングできない場合、THEN THE Issue_Creator SHALL Assignee を設定せずに Issue を作成する
4. IF 担当者が「未定」の場合、THEN THE Issue_Creator SHALL Assignee を設定せずに Issue を作成する
5. THE Issue_Creator SHALL 担当者マッピングテーブルを設定ファイルで管理する

### 要件 5: マイルストーンの設定

**ユーザーストーリー:** ユーザーとして、タスクの期限に応じたマイルストーンを Issue に設定したい。これにより、スケジュール管理が容易になる。

#### 受け入れ条件

1. WHEN Issue を作成する場合、THE Issue_Creator SHALL タスクの期限に最も近いマイルストーンを設定する
2. IF タスクの期限が「未定」の場合、THEN THE Issue_Creator SHALL マイルストーンを設定しない
3. IF 適切なマイルストーンが存在しない場合、THEN THE Issue_Creator SHALL マイルストーンを設定せずに Issue を作成する
4. THE Issue_Creator SHALL リポジトリの既存マイルストーン一覧を取得して比較する

### 要件 6: Slack 最終確認フロー

**ユーザーストーリー:** ユーザーとして、Issue 登録前に最終確認を Slack で行いたい。これにより、誤った Issue の登録を防げる。

#### 受け入れ条件

1. WHEN タスクが承認された場合、THE Registration_Flow SHALL Slack に Issue 登録確認メッセージを送信する
2. THE Registration_Flow SHALL Block Kit を使用して Issue プレビューと登録/キャンセルボタンを表示する
3. WHEN ユーザーが登録ボタンをクリックした場合、THE Registration_Flow SHALL Issue を GitHub に登録する
4. WHEN ユーザーがキャンセルボタンをクリックした場合、THE Registration_Flow SHALL 登録をスキップする
5. WHEN Issue 登録が完了した場合、THE Registration_Flow SHALL Issue URL を含む完了メッセージを送信する
6. IF 24 時間以内に応答がない場合、THEN THE Registration_Flow SHALL リマインダーを送信する

### 要件 7: 一括登録

**ユーザーストーリー:** ユーザーとして、複数のタスクを一括で Issue 登録したい。これにより、効率的にタスクを管理できる。

#### 受け入れ条件

1. WHEN 複数のタスクが承認された場合、THE Issue_Creator SHALL 一括で Issue を作成する
2. THE Issue_Creator SHALL 各 Issue の作成結果（成功/失敗）を個別に追跡する
3. IF 一部の Issue 作成が失敗した場合、THEN THE Issue_Creator SHALL 成功した Issue のみを登録し、失敗した Issue をレポートする
4. THE Issue_Creator SHALL 一括登録の進捗状況を Slack に通知する
5. WHEN 一括登録が完了した場合、THE Issue_Creator SHALL 登録結果サマリーを Slack に送信する

### 要件 8: エラーハンドリング

**ユーザーストーリー:** ユーザーとして、Issue 登録中にエラーが発生した場合に適切な通知を受けたい。これにより、問題を迅速に把握できる。

#### 受け入れ条件

1. IF GitHub API 呼び出しが失敗した場合、THEN THE Issue_Creator SHALL 最大 3 回リトライする
2. IF リトライ後も失敗した場合、THEN THE Issue_Creator SHALL Slack にエラー通知を送信する
3. WHEN エラーが発生した場合、THE Issue_Creator SHALL エラー内容をログに記録する
4. IF レート制限に達した場合、THEN THE Issue_Creator SHALL 指数バックオフでリトライする
5. IF リポジトリへのアクセス権限がない場合、THEN THE Issue_Creator SHALL 権限エラーを通知する

### 要件 9: Issue テンプレート

**ユーザーストーリー:** ユーザーとして、一貫したフォーマットの Issue を作成したい。これにより、Issue の可読性が向上する。

#### 受け入れ条件

1. THE Issue_Template SHALL 以下のセクションを含む: 概要、詳細、関連議事録、期限、優先度
2. THE Issue_Creator SHALL Issue_Template に従って Issue 本文を生成する
3. THE Issue_Creator SHALL 元の議事録へのリンクを Issue 本文に含める
4. FOR ALL 有効な Task、Issue 本文を生成してからパースした場合、THE Issue_Creator SHALL 元のタスク情報を復元できる
5. THE Issue_Template SHALL Markdown 形式で記述される

### 要件 10: 重複 Issue の検出

**ユーザーストーリー:** ユーザーとして、既存の Issue と重複する Issue の作成を防ぎたい。これにより、Issue の重複を避けられる。

#### 受け入れ条件

1. WHEN Issue を作成する前に、THE Issue_Creator SHALL リポジトリ内の既存 Issue を検索する
2. THE Issue_Creator SHALL タイトルの類似度 80%以上を重複とみなす
3. IF 重複 Issue が検出された場合、THEN THE Issue_Creator SHALL Slack で重複警告を表示する
4. WHEN 重複警告が表示された場合、THE Registration_Flow SHALL 「それでも登録」「スキップ」の選択肢を提供する
5. IF ユーザーが「スキップ」を選択した場合、THEN THE Issue_Creator SHALL 既存 Issue へのリンクを返す

## 制約事項

- GitHub REST API v3 を使用する
- GitHub API のレート制限（認証済み: 5000 リクエスト/時間）を考慮する
- Personal Access Token には `repo` スコープが必要
- Issue タイトルは 256 文字以内とする
- Issue 本文は 65536 文字以内とする
- 日本語の Issue タイトル・本文をサポートする
