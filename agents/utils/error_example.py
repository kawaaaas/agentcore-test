"""エラー通知機能の使用例。

このファイルは、エラー通知機能とリトライハンドラの統合方法を示します。
"""

import os
from typing import Any

from agents.utils.error import send_error_notification
from agents.utils.retry import with_retry


def create_error_handler(slack_client: Any, channel_id: str, session_id: str = None):
    """エラーハンドラを作成する。
    
    リトライ失敗時にSlackに通知するコールバック関数を返します。
    
    Args:
        slack_client: Slack APIクライアント
        channel_id: 通知先のSlackチャンネルID
        session_id: AgentCoreセッションID（オプション）
    
    Returns:
        エラーコールバック関数
    
    Example:
        >>> slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        >>> error_handler = create_error_handler(
        ...     slack_client=slack_client,
        ...     channel_id="C1234567890",
        ...     session_id="session-123"
        ... )
        >>> 
        >>> @with_retry(max_retries=3, on_final_failure=error_handler)
        >>> def call_bedrock_api():
        ...     # Bedrock API呼び出し
        ...     pass
    """
    def error_callback(exception: Exception, func_name: str, context: dict):
        """リトライ失敗時のコールバック関数。
        
        Args:
            exception: 発生した例外
            func_name: 失敗した関数名
            context: コンテキスト情報
        """
        # エラー種別を決定
        error_type = f"{context.get('error_type', 'Unknown Error')} in {func_name}"
        
        # エラーメッセージを構築
        error_message = (
            f"関数 '{func_name}' が{context.get('max_retries', 3)}回のリトライ後に失敗しました。\n"
            f"エラー: {str(exception)}"
        )
        
        # 追加のコンテキスト情報
        additional_context = {
            "function": func_name,
            "retries": context.get("max_retries", 3),
            "exception_type": context.get("error_type", "Unknown"),
        }
        
        # Slackに通知
        try:
            send_error_notification(
                slack_client=slack_client,
                channel_id=channel_id,
                error_type=error_type,
                error_message=error_message,
                context=additional_context,
                session_id=session_id,
            )
        except Exception as e:
            # Slack通知自体が失敗した場合はログに記録（既にerror.pyで処理済み）
            pass
    
    return error_callback


# 使用例
if __name__ == "__main__":
    """
    使用例:
    
    from slack_sdk import WebClient
    from agents.utils.error_example import create_error_handler
    from agents.utils.retry import with_retry
    
    # Slackクライアントを初期化
    slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    
    # エラーハンドラを作成
    error_handler = create_error_handler(
        slack_client=slack_client,
        channel_id=os.environ["SLACK_CHANNEL_ID"],
        session_id="session-123"
    )
    
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
    """
    print("このファイルは使用例を示すためのものです。")
    print("詳細はソースコードのコメントを参照してください。")
