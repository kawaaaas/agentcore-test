# 議事録生成機能 要件定義

## 概要

会議の書き起こしテキストから議事録を自動生成する機能。Amazon Bedrock（Nova 2 Lite）を使用して要約・構造化を行い、Slack での確認・修正フローを経て最終版を保存する。

## 用語集（Glossary）

- **Transcript**: 会議の書き起こしテキスト（S3 に保存される入力データ）
- **Minutes**: 生成された議事録（構造化されたドキュメント）
- **Minutes_Generator**: 書き起こしテキストから議事録を生成するコンポーネント
- **Minutes_Formatter**: 議事録を指定フォーマットに整形するコンポーネント
- **Approval_Flow**: Slack を通じた議事録の確認・修正フロー
- **Nova_2_Lite**: Amazon Bedrock で使用する AI モデル
- **Transcript_Bucket**: 書き起こしテキストを保存する S3 バケット
- **Minutes_Bucket**: 生成された議事録を保存する S3 バケット

## 要件

### 要件 1: 書き起こしテキストの読み込み

**ユーザーストーリー:** ユーザーとして、S3 にアップロードした書き起こしテキストを自動的に処理したい。これにより、手動操作なしで議事録生成が開始される。

#### 受け入れ条件

1. WHEN 書き起こしテキストが Transcript_Bucket にアップロードされた場合、THE Minutes_Generator SHALL 自動的に処理を開始する
2. WHEN テキストファイルを読み込む場合、THE Minutes_Generator SHALL UTF-8 エンコーディングをサポートする
3. IF 書き起こしテキストが空の場合、THEN THE Minutes_Generator SHALL エラーを返し処理を中断する
4. WHEN テキストを読み込む場合、THE Minutes_Generator SHALL ファイルサイズが 1MB 以下であることを検証する
5. IF ファイルサイズが 1MB を超える場合、THEN THE Minutes_Generator SHALL エラーを返し処理を中断する

### 要件 2: 議事録の生成

**ユーザーストーリー:** ユーザーとして、書き起こしテキストから構造化された議事録を生成したい。これにより、会議内容を効率的に把握できる。

#### 受け入れ条件

1. WHEN 書き起こしテキストが入力された場合、THE Minutes_Generator SHALL Nova_2_Lite を使用して議事録を生成する
2. THE Minutes SHALL 以下のセクションを含む: 会議タイトル、日時、参加者、議題、議論内容、決定事項、アクションアイテム
3. WHEN 議事録を生成する場合、THE Minutes_Generator SHALL 元のテキストの重要なポイントを抽出する
4. WHEN 議事録を生成する場合、THE Minutes_Generator SHALL 冗長な表現を簡潔にまとめる
5. IF 書き起こしテキストに参加者情報が含まれない場合、THEN THE Minutes_Generator SHALL 参加者セクションを「不明」として生成する

### 要件 3: 議事録のフォーマット

**ユーザーストーリー:** ユーザーとして、一貫したフォーマットの議事録を取得したい。これにより、過去の議事録との比較や検索が容易になる。

#### 受け入れ条件

1. THE Minutes_Formatter SHALL Markdown 形式で議事録を出力する
2. WHEN 議事録をフォーマットする場合、THE Minutes_Formatter SHALL 見出しレベルを適切に設定する
3. WHEN アクションアイテムをフォーマットする場合、THE Minutes_Formatter SHALL チェックボックス形式（`- [ ]`）で出力する
4. FOR ALL 生成された議事録、フォーマットしてから再度パースした場合、THE Minutes_Formatter SHALL 同等の構造を復元できる（ラウンドトリップ特性）

### 要件 4: Slack 承認フロー

**ユーザーストーリー:** ユーザーとして、生成された議事録を Slack で確認・修正したい。これにより、AI の出力を人間がレビューできる。

#### 受け入れ条件

1. WHEN 議事録が生成された場合、THE Approval_Flow SHALL Slack に確認メッセージを送信する
2. THE Approval_Flow SHALL Block Kit を使用して承認/修正ボタンを表示する
3. WHEN ユーザーが承認ボタンをクリックした場合、THE Approval_Flow SHALL 議事録を確定する
4. WHEN ユーザーが修正ボタンをクリックした場合、THE Approval_Flow SHALL 修正入力フォームを表示する
5. WHEN 修正内容が入力された場合、THE Minutes_Generator SHALL 修正を反映した議事録を再生成する
6. IF 24 時間以内に応答がない場合、THEN THE Approval_Flow SHALL リマインダーを送信する

### 要件 5: 議事録の保存

**ユーザーストーリー:** ユーザーとして、確定した議事録を永続的に保存したい。これにより、後から参照できる。

#### 受け入れ条件

1. WHEN 議事録が承認された場合、THE Minutes_Generator SHALL Minutes_Bucket に保存する
2. THE Minutes_Generator SHALL ファイル名に日時とタイトルを含める
3. WHEN 議事録を保存する場合、THE Minutes_Generator SHALL メタデータ（生成日時、元ファイル名、承認者）を付与する
4. FOR ALL 保存された議事録、S3 から読み込んでパースした場合、THE Minutes_Formatter SHALL 元の構造を復元できる

### 要件 6: エラーハンドリング

**ユーザーストーリー:** ユーザーとして、処理中にエラーが発生した場合に適切な通知を受けたい。これにより、問題を迅速に把握できる。

#### 受け入れ条件

1. IF Bedrock API 呼び出しが失敗した場合、THEN THE Minutes_Generator SHALL 最大 3 回リトライする
2. IF リトライ後も失敗した場合、THEN THE Minutes_Generator SHALL Slack にエラー通知を送信する
3. WHEN エラーが発生した場合、THE Minutes_Generator SHALL エラー内容をログに記録する
4. IF S3 への保存が失敗した場合、THEN THE Minutes_Generator SHALL 一時ストレージに保存しリトライする

### 要件 7: AgentCore Memory 連携

**ユーザーストーリー:** ユーザーとして、過去の修正パターンを学習した議事録を生成したい。これにより、毎回同じ修正を指示する手間が省ける。

#### 受け入れ条件

1. WHEN ユーザーが議事録を修正した場合、THE Minutes_Generator SHALL 修正内容を長期記憶（LTM）に保存する
2. WHEN 議事録を生成する場合、THE Minutes_Generator SHALL 過去の修正パターンを LTM から検索する
3. IF 類似の修正パターンが見つかった場合、THEN THE Minutes_Generator SHALL そのパターンを生成時に適用する
4. THE Minutes_Generator SHALL ユーザーごとの文体・フォーマット好みを記憶する
5. WHEN 承認フロー中の会話が発生した場合、THE Minutes_Generator SHALL 短期記憶（STM）に保存する

## 制約事項

- Amazon Bedrock Nova 2 Lite モデルを使用する
- Slack Free Plan の制限内で動作する
- 書き起こしテキストは日本語を想定する
- 議事録の最大長は Slack メッセージの制限（4000 文字）を考慮する
