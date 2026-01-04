# Utility Functions

このディレクトリには、議事録生成エージェントで使用するユーティリティ関数が含まれています。

## モジュール

### retry.py

失敗した操作を自動的にリトライするデコレータを提供します。

**主な機能:**

- 指数バックオフによる自動リトライ（最大 3 回）
- エラーログの自動記録
- リトライ失敗時のコールバック機能

**使用例:**

```python
from agents.utils.retry import with_retry

# 基本的な使用方法
@with_retry(max_retries=3, base_delay=1.0)
def call_api():
    # API呼び出し
    pass

# エラー通知付き
def error_handler(exception, func_name, context):
    print(f"エラー: {func_name} が失敗しました")

@with_retry(max_retries=3, on_final_failure=error_handler)
def call_bedrock():
    # Bedrock API呼び出し
    pass
```

**Requirements:** 6.1, 6.2, 6.3

---

### error.py

エラー発生時に Slack へ通知するための機能を提供します。

**主な機能:**

- Block Kit 形式のエラー通知メッセージ生成
- Slack へのエラー通知送信
- コンテキスト情報の付与

**使用例:**

```python
from agents.utils.error import create_error_notification, send_error_notification
from slack_sdk import WebClient

# エラー通知メッセージの生成
notification = create_error_notification(
    error_type="Bedrock API Error",
    error_message="API呼び出しが3回失敗しました",
    context={"transcript_file": "meeting_20250104.txt"},
    session_id="session-123"
)

# Slackへの送信
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
response = send_error_notification(
    slack_client=slack_client,
    channel_id="C1234567890",
    error_type="Bedrock API Error",
    error_message="API呼び出しが3回失敗しました",
    context={"transcript_file": "meeting_20250104.txt"},
    session_id="session-123"
)
```

**Requirements:** 6.2

---

## 統合使用例

リトライ機能とエラー通知を組み合わせて使用する例:

```python
import os
from slack_sdk import WebClient
from agents.utils.retry import with_retry
from agents.utils.error import send_error_notification

# Slackクライアントを初期化
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
channel_id = os.environ["SLACK_CHANNEL_ID"]
session_id = "session-123"

# エラーハンドラを作成
def create_error_handler(slack_client, channel_id, session_id):
    def error_callback(exception, func_name, context):
        error_type = f"{context.get('error_type', 'Unknown Error')} in {func_name}"
        error_message = (
            f"関数 '{func_name}' が{context.get('max_retries', 3)}回のリトライ後に失敗しました。\n"
            f"エラー: {str(exception)}"
        )

        send_error_notification(
            slack_client=slack_client,
            channel_id=channel_id,
            error_type=error_type,
            error_message=error_message,
            context={"function": func_name, "retries": context.get("max_retries", 3)},
            session_id=session_id,
        )

    return error_callback

# エラーハンドラを設定
error_handler = create_error_handler(slack_client, channel_id, session_id)

# リトライ付きでBedrock APIを呼び出す
@with_retry(max_retries=3, base_delay=1.0, on_final_failure=error_handler)
def call_bedrock_api(prompt: str):
    # Bedrock API呼び出しのコード
    # エラーが発生した場合、3回リトライされ、
    # 最終的に失敗した場合はSlackに通知される
    pass

# 関数を実行
try:
    call_bedrock_api("議事録を生成してください")
except Exception as e:
    # エラーは既にSlackに通知されている
    print(f"処理が失敗しました: {e}")
```

詳細な使用例は `error_example.py` を参照してください。

## テスト

各モジュールのテストは `tests/unit/` ディレクトリにあります:

- `test_error_notification.py`: エラー通知機能のテスト
- `test_validator.py`: バリデーション機能のテスト

テストの実行:

```bash
python -m pytest tests/unit/ -v
```
