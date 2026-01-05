"""
Slack Notifier

AgentCore Gateway 経由で Slack Web API に接続し、
Block Kit を使用したメッセージ送信を行うツール。

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.2, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4
"""

import logging
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from strands import tool

from agents.tools.block_kit_builder import (
    BlockKitBuilder,
    ContentType,
    StatusType,
)

# ロギング設定
logger = logging.getLogger(__name__)


class SlackNotifierConfig(BaseModel):
    """Slack Notifier 設定"""
    bot_token: str = Field(..., description="Slack Bot Token")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: float = Field(default=1.0, description="リトライ間隔（秒）")


class SlackNotifier:
    """
    Slack 通知ツール
    
    AgentCore Gateway 経由で Slack Web API に接続し、
    Block Kit メッセージの送信、更新、モーダル表示を行う。
    
    Requirements: 1.1, 1.2
    """
    
    def __init__(self, config: SlackNotifierConfig):
        """
        初期化
        
        Args:
            config: Slack Notifier 設定
        """
        self.config = config
        self.builder = BlockKitBuilder()
        logger.info("Slack Notifier を初期化しました")
    
    def send_message(
        self,
        channel_id: str,
        blocks: List[Dict[str, Any]],
        text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Slack チャンネルにメッセージを送信する
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        
        Args:
            channel_id: 送信先チャンネルID
            blocks: Block Kit ブロックのリスト
            text: フォールバックテキスト（オプション）
            
        Returns:
            Slack API レスポンス（ts, channel 等を含む）
            
        Raises:
            Exception: メッセージ送信に失敗した場合
        """
        import requests
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.config.bot_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "channel": channel_id,
            "blocks": blocks,
        }
        
        if text:
            payload["text"] = text
        
        # リトライロジック (Requirements 1.3, 1.4)
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"メッセージ送信試行 {attempt + 1}/{self.config.max_retries}: "
                    f"channel={channel_id}"
                )
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Slack API エラー: {error_msg}")
                
                logger.info(
                    f"メッセージ送信成功: ts={result.get('ts')}, "
                    f"channel={result.get('channel')}"
                )
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"メッセージ送信失敗 (試行 {attempt + 1}/{self.config.max_retries}): {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    # 指数バックオフでリトライ
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"{delay}秒後にリトライします...")
                    time.sleep(delay)
        
        # 全てのリトライが失敗 (Requirement 1.5)
        error_msg = f"メッセージ送信に失敗しました（{self.config.max_retries}回試行）: {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def update_message(
        self,
        channel_id: str,
        message_ts: str,
        blocks: List[Dict[str, Any]],
        text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        既存のメッセージを更新する
        
        Requirements: 5.1, 5.2, 5.3
        
        Args:
            channel_id: チャンネルID
            message_ts: メッセージタイムスタンプ
            blocks: 更新後の Block Kit ブロック
            text: フォールバックテキスト（オプション）
            
        Returns:
            Slack API レスポンス
            
        Raises:
            Exception: メッセージ更新に失敗した場合
        """
        import requests
        
        url = "https://slack.com/api/chat.update"
        headers = {
            "Authorization": f"Bearer {self.config.bot_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "channel": channel_id,
            "ts": message_ts,
            "blocks": blocks,
        }
        
        if text:
            payload["text"] = text
        
        # リトライロジック
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"メッセージ更新試行 {attempt + 1}/{self.config.max_retries}: "
                    f"channel={channel_id}, ts={message_ts}"
                )
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Slack API エラー: {error_msg}")
                
                logger.info(
                    f"メッセージ更新成功: ts={result.get('ts')}, "
                    f"channel={result.get('channel')}"
                )
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"メッセージ更新失敗 (試行 {attempt + 1}/{self.config.max_retries}): {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"{delay}秒後にリトライします...")
                    time.sleep(delay)
        
        # 全てのリトライが失敗
        error_msg = f"メッセージ更新に失敗しました（{self.config.max_retries}回試行）: {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def open_modal(
        self,
        trigger_id: str,
        view: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        モーダルを表示する
        
        Requirements: 3.2
        
        Args:
            trigger_id: トリガーID（インタラクションから取得）
            view: モーダルビューの定義
            
        Returns:
            Slack API レスポンス
            
        Raises:
            Exception: モーダル表示に失敗した場合
        """
        import requests
        
        url = "https://slack.com/api/views.open"
        headers = {
            "Authorization": f"Bearer {self.config.bot_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "trigger_id": trigger_id,
            "view": view,
        }
        
        # リトライロジック
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"モーダル表示試行 {attempt + 1}/{self.config.max_retries}: "
                    f"trigger_id={trigger_id}"
                )
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Slack API エラー: {error_msg}")
                
                logger.info(f"モーダル表示成功: view_id={result.get('view', {}).get('id')}")
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"モーダル表示失敗 (試行 {attempt + 1}/{self.config.max_retries}): {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"{delay}秒後にリトライします...")
                    time.sleep(delay)
        
        # 全てのリトライが失敗
        error_msg = f"モーダル表示に失敗しました（{self.config.max_retries}回試行）: {last_exception}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def send_reminder(
        self,
        channel_id: str,
        session_id: str,
        content_type: ContentType,
        original_message_link: str,
        reminder_count: int,
    ) -> Dict[str, Any]:
        """
        リマインダーメッセージを送信する
        
        Requirements: 6.1, 6.2, 6.3, 6.4
        
        Args:
            channel_id: 送信先チャンネルID
            session_id: セッションID
            content_type: コンテンツタイプ
            original_message_link: 元のメッセージへのリンク
            reminder_count: リマインダー送信回数
            
        Returns:
            Slack API レスポンス
            
        Raises:
            Exception: リマインダー送信に失敗した場合
        """
        # リマインダー回数の検証 (Requirement 6.2)
        if reminder_count > 3:
            error_msg = f"リマインダー送信回数が上限（3回）を超えています: {reminder_count}"
            logger.warning(error_msg)
            raise ValueError(error_msg)
        
        # リマインダーメッセージを生成 (Requirement 6.4)
        blocks = self.builder.create_reminder_message(
            session_id=session_id,
            content_type=content_type,
            original_message_link=original_message_link,
            reminder_count=reminder_count,
        )
        
        # メッセージを送信
        logger.info(
            f"リマインダー送信: session={session_id}, count={reminder_count}/3"
        )
        
        return self.send_message(
            channel_id=channel_id,
            blocks=blocks,
            text=f"リマインダー: 確認をお願いします（{reminder_count}/3回目）",
        )


@tool
def send_slack_approval_message(
    channel_id: str,
    session_id: str,
    content_type: str,
    content: str,
    title: str,
    bot_token: str,
) -> str:
    """
    Slack に承認メッセージを送信する
    
    Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4
    
    Args:
        channel_id: 送信先チャンネルID
        session_id: セッションID
        content_type: コンテンツタイプ（minutes/tasks）
        content: 表示するコンテンツ
        title: タイトル
        bot_token: Slack Bot Token
        
    Returns:
        送信結果メッセージ
    """
    try:
        # ContentType に変換
        ct = ContentType(content_type)
        
        # Notifier を初期化
        config = SlackNotifierConfig(bot_token=bot_token)
        notifier = SlackNotifier(config)
        
        # 承認メッセージを生成
        blocks = notifier.builder.create_approval_message(
            session_id=session_id,
            content_type=ct,
            content=content,
            title=title,
        )
        
        # メッセージを送信
        response = notifier.send_message(
            channel_id=channel_id,
            blocks=blocks,
            text=f"{title} - 確認をお願いします",
        )
        
        return f"承認メッセージを送信しました: {response.get('ts', 'unknown')}"
        
    except Exception as e:
        logger.error(f"承認メッセージ送信エラー: {e}")
        return f"エラー: {str(e)}"
