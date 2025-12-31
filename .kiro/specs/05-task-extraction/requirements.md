# タスク抽出機能 要件定義

## 概要

承認済み議事録からアクションアイテム（タスク）を抽出し、構造化されたタスクデータとして出力する機能。Amazon Bedrock（Nova 2 Lite）を使用してタスクを識別・分類し、Slack での確認フローを経て GitHub Issues への登録準備を行う。

## 用語集（Glossary）

- **Task_Extractor**: 議事録からタスクを抽出するコンポーネント
- **Task**: 抽出された個別のタスク（担当者、期限、優先度を含む）
- **Task_List**: 抽出されたタスクの集合
- **Task_Validator**: 抽出されたタスクの妥当性を検証するコンポーネント
- **Task_Formatter**: タスクを指定フォーマットに整形するコンポーネント
- **Priority**: タスクの優先度（high, medium, low）
- **Assignee**: タスクの担当者
- **Due_Date**: タスクの期限
- **Minutes**: 入力となる承認済み議事録
- **Action_Item**: 議事録内のアクションアイテムセクション
- **Nova_2_Lite**: Amazon Bedrock で使用する AI モデル
- **Approval_Flow**: Slack を通じたタスクの確認・修正フロー

## 要件

### 要件 1: 議事録からのタスク抽出

**ユーザーストーリー:** ユーザーとして、承認済み議事録から自動的にタスクを抽出したい。これにより、手動でタスクを洗い出す手間が省ける。

#### 受け入れ条件

1. WHEN 議事録が承認された場合、THE Task_Extractor SHALL 自動的にタスク抽出処理を開始する
2. WHEN タスクを抽出する場合、THE Task_Extractor SHALL Nova_2_Lite を使用して議事録を解析する
3. THE Task_Extractor SHALL 議事録のアクションアイテムセクションを優先的に解析する
4. THE Task_Extractor SHALL 議事録の議論内容・決定事項からも暗黙的なタスクを抽出する
5. IF 議事録にタスクが含まれない場合、THEN THE Task_Extractor SHALL 空の Task_List を返す

### 要件 2: タスクの構造化

**ユーザーストーリー:** ユーザーとして、抽出されたタスクを構造化されたデータとして取得したい。これにより、タスク管理ツールへの登録が容易になる。

#### 受け入れ条件

1. THE Task SHALL 以下のフィールドを含む: タイトル、説明、担当者、期限、優先度
2. WHEN タスクを構造化する場合、THE Task_Extractor SHALL タイトルを 100 文字以内に要約する
3. WHEN タスクを構造化する場合、THE Task_Extractor SHALL 説明に元の議事録の該当箇所を引用する
4. IF 担当者が明示されていない場合、THEN THE Task_Extractor SHALL 担当者を「未定」として設定する
5. IF 期限が明示されていない場合、THEN THE Task_Extractor SHALL 期限を「未定」として設定する
6. WHEN 優先度を判定する場合、THE Task_Extractor SHALL 文脈から high/medium/low を推定する

### 要件 3: タスクの検証

**ユーザーストーリー:** ユーザーとして、抽出されたタスクが妥当であることを確認したい。これにより、不完全なタスクの登録を防げる。

#### 受け入れ条件

1. THE Task_Validator SHALL タイトルが空でないことを検証する
2. THE Task_Validator SHALL タイトルが 100 文字以内であることを検証する
3. THE Task_Validator SHALL 優先度が有効な値（high, medium, low）であることを検証する
4. IF 期限が設定されている場合、THEN THE Task_Validator SHALL 日付形式が有効であることを検証する
5. FOR ALL 抽出されたタスク、検証に合格したタスクのみが Task_List に含まれる

### 要件 4: タスクのフォーマット

**ユーザーストーリー:** ユーザーとして、タスクを一貫したフォーマットで確認したい。これにより、レビューが容易になる。

#### 受け入れ条件

1. THE Task_Formatter SHALL Markdown 形式でタスク一覧を出力する
2. WHEN タスクをフォーマットする場合、THE Task_Formatter SHALL 優先度でソートする
3. THE Task_Formatter SHALL 各タスクにチェックボックス形式（`- [ ]`）を付与する
4. THE Task_Formatter SHALL 担当者と期限をタスクの下に表示する
5. FOR ALL 有効な Task_List、フォーマットしてから再度パースした場合、THE Task_Formatter SHALL 同等の構造を復元できる（ラウンドトリップ特性）

### 要件 5: Slack 確認フロー

**ユーザーストーリー:** ユーザーとして、抽出されたタスクを Slack で確認・修正したい。これにより、AI の出力を人間がレビューできる。

#### 受け入れ条件

1. WHEN タスクが抽出された場合、THE Approval_Flow SHALL Slack に確認メッセージを送信する
2. THE Approval_Flow SHALL Block Kit を使用してタスク一覧と承認/修正ボタンを表示する
3. WHEN ユーザーが承認ボタンをクリックした場合、THE Approval_Flow SHALL タスクを確定する
4. WHEN ユーザーが修正ボタンをクリックした場合、THE Approval_Flow SHALL 修正入力フォームを表示する
5. WHEN ユーザーが個別タスクを削除した場合、THE Approval_Flow SHALL そのタスクを Task_List から除外する
6. WHEN ユーザーがタスクを追加した場合、THE Approval_Flow SHALL 新しいタスクを Task_List に追加する
7. IF 24 時間以内に応答がない場合、THEN THE Approval_Flow SHALL リマインダーを送信する

### 要件 6: 重複タスクの検出

**ユーザーストーリー:** ユーザーとして、重複するタスクを自動的に検出したい。これにより、同じタスクが複数登録されることを防げる。

#### 受け入れ条件

1. WHEN タスクを抽出する場合、THE Task_Extractor SHALL 同一議事録内の重複タスクを検出する
2. IF 重複タスクが検出された場合、THEN THE Task_Extractor SHALL 重複を統合して 1 つのタスクにする
3. THE Task_Extractor SHALL タイトルの類似度 80%以上を重複とみなす
4. WHEN 重複を統合する場合、THE Task_Extractor SHALL より詳細な説明を持つタスクを優先する

### 要件 7: エラーハンドリング

**ユーザーストーリー:** ユーザーとして、タスク抽出中にエラーが発生した場合に適切な通知を受けたい。これにより、問題を迅速に把握できる。

#### 受け入れ条件

1. IF Bedrock API 呼び出しが失敗した場合、THEN THE Task_Extractor SHALL 最大 3 回リトライする
2. IF リトライ後も失敗した場合、THEN THE Task_Extractor SHALL Slack にエラー通知を送信する
3. WHEN エラーが発生した場合、THE Task_Extractor SHALL エラー内容をログに記録する
4. IF タスク抽出が部分的に失敗した場合、THEN THE Task_Extractor SHALL 成功したタスクのみを返す

### 要件 8: 承認待ちデータの永続化

**ユーザーストーリー:** ユーザーとして、承認待ちのタスクリストが永続化され、セッション再開時に復元されることを期待する。これにより、承認フローの途中でシステムが再起動しても作業を継続できる。

#### 受け入れ条件

1. WHEN タスクが抽出された場合、THE Task_Extractor SHALL Task_List を AgentCore Memory STM に保存する
2. WHEN タスクが抽出された場合、THE Task_Extractor SHALL 承認状態・メタデータを DynamoDB Session_Table に保存する
3. WHEN セッションが再開された場合、THE Task_Extractor SHALL Memory と DynamoDB から承認待ちデータを復元する
4. FOR ALL 承認待ち Task_List、保存してから復元した場合、THE Task_Extractor SHALL 元の構造と同等のデータを取得できる
5. THE Task_Extractor SHALL session_id をキーとしてデータを管理する

### 要件 9: AgentCore Memory 連携

**ユーザーストーリー:** ユーザーとして、過去のタスク抽出パターンを学習したタスク抽出を行いたい。これにより、抽出精度が向上する。

#### 受け入れ条件

1. WHEN ユーザーがタスクを修正した場合、THE Task_Extractor SHALL 修正内容を長期記憶（LTM）に保存する
2. WHEN タスクを抽出する場合、THE Task_Extractor SHALL 過去の修正パターンを LTM から検索する
3. IF 類似の修正パターンが見つかった場合、THEN THE Task_Extractor SHALL そのパターンを抽出時に適用する
4. THE Task_Extractor SHALL ユーザーごとのタスク分類・優先度付けの傾向を記憶する
5. WHEN 確認フロー中の会話が発生した場合、THE Task_Extractor SHALL 短期記憶（STM）に保存する

## 制約事項

- Amazon Bedrock Nova 2 Lite モデルを使用する
- Slack Free Plan の制限内で動作する
- 議事録は日本語を想定する
- 1 回の抽出で最大 20 タスクまでを処理する
- タスクのタイトルは 100 文字以内とする
