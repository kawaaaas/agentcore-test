"""エラー通知機能の実装。

このモジュールは、エラー発生時にSlackへ通知するための機能を提供します。
Block Kit形式でエラー内容を表示します。

Requirements: 6.2
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

# ロガーの設定
logger = logging.getLogger(__name__)


def create_error_notification(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """エラー通知メッセージを生成する。
    
    Slack Block Kit形式でエラー内容を表示するメッセージを生成します。
    
    Requirements: 6.2
    
    Args:
        error_type: エラーの種類（例: "Bedrock API Error", "S3 Save Error"）
        error_message: エラーメッセージ
        context: 追加のコンテキスト情報（オプション）
        session_id: AgentCoreセッションID（オプション）
    
    Returns:
        Slack Block Kit形式のメッセージ辞書
    
    Example:
        >>> notification = create_error_notification(
        ...     error_type="Bedrock API Error",
        ...     error_message="API呼び出しが3回失敗しました",
        ...     context={"transcript_file": "meeting_20250104.txt"},
        ...     session_id="session-123"
        ... )
    """
    # 現在時刻を取得
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    # Block Kitメッセージを構築
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚠️ エラーが発生しました",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*エラー種別:*\n{error_type}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*発生時刻:*\n{timestamp}",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*エラー内容:*\n```{error_message}```",
            },
        },
    ]
    
    # セッションIDがある場合は追加
    if session_id:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*セッションID:*\n`{session_id}`",
            },
        })
    
    # コンテキスト情報がある場合は追加
    if context:
        context_text = "\n".join([f"• *{key}:* {value}" for key, value in context.items()])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*追加情報:*\n{context_text}",
            },
        })
    
    # 区切り線とフッター
    blocks.extend([
        {
            "type": "divider",
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 このエラーは自動的に記録されました。必要に応じて管理者に連絡してください。",
                },
            ],
        },
    ])
    
    return {
        "blocks": blocks,
        "text": f"エラーが発生しました: {error_type}",
    }


def send_error_notification(
    slack_client: Any,
    channel_id: str,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Slackにエラー通知を送信する。
    
    create_error_notification()で生成したメッセージをSlackに送信します。
    
    Requirements: 6.2
    
    Args:
        slack_client: Slack APIクライアント
        channel_id: 送信先のSlackチャンネルID
        error_type: エラーの種類
        error_message: エラーメッセージ
        context: 追加のコンテキスト情報（オプション）
        session_id: AgentCoreセッションID（オプション）
    
    Returns:
        Slack APIのレスポンス
    
    Raises:
        Exception: Slack送信に失敗した場合
    
    Example:
        >>> response = send_error_notification(
        ...     slack_client=slack_client,
        ...     channel_id="C1234567890",
        ...     error_type="Bedrock API Error",
        ...     error_message="API呼び出しが3回失敗しました",
        ... )
    """
    try:
        # エラー通知メッセージを生成
        notification = create_error_notification(
            error_type=error_type,
            error_message=error_message,
            context=context,
            session_id=session_id,
        )
        
        # Slackに送信
        logger.info(f"Slackにエラー通知を送信: {error_type}")
        response = slack_client.chat_postMessage(
            channel=channel_id,
            blocks=notification["blocks"],
            text=notification["text"],
        )
        
        logger.info(f"エラー通知の送信に成功: ts={response.get('ts')}")
        return response
        
    except Exception as e:
        # Slack送信自体が失敗した場合はログに記録
        logger.error(f"Slackへのエラー通知送信に失敗: {str(e)}")
        raise Exception(f"Failed to send error notification to Slack: {str(e)}") from e
