"""
Slack Notifier のユニットテスト

SlackNotifier クラスの基本機能をテストする。
"""

from unittest.mock import Mock, patch, MagicMock
import pytest

from agents.tools.slack_notifier import (
    SlackNotifier,
    SlackNotifierConfig,
    send_slack_approval_message,
)
from agents.tools.block_kit_builder import ContentType, StatusType


class TestSlackNotifier:
    """SlackNotifier クラスのテスト"""
    
    @pytest.fixture
    def config(self) -> SlackNotifierConfig:
        """テスト用設定"""
        return SlackNotifierConfig(
            bot_token="xoxb-test-token",
            max_retries=3,
            retry_delay=0.1,  # テスト用に短縮
        )
    
    @pytest.fixture
    def notifier(self, config: SlackNotifierConfig) -> SlackNotifier:
        """SlackNotifier インスタンス"""
        return SlackNotifier(config)
    
    @patch("requests.post")
    def test_send_message_success(self, mock_post: Mock, notifier: SlackNotifier):
        """メッセージ送信成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # メッセージ送信
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Test"}}]
        result = notifier.send_message(
            channel_id="C123456",
            blocks=blocks,
            text="Test message",
        )
        
        # 検証
        assert result["ok"] is True
        assert result["ts"] == "1234567890.123456"
        assert result["channel"] == "C123456"
        
        # API呼び出しの検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://slack.com/api/chat.postMessage"
        assert call_args[1]["json"]["channel"] == "C123456"
        assert call_args[1]["json"]["blocks"] == blocks
    
    @patch("requests.post")
    def test_send_message_retry_on_failure(
        self, mock_post: Mock, notifier: SlackNotifier
    ):
        """メッセージ送信失敗時のリトライテスト"""
        # 最初の2回は失敗、3回目は成功
        mock_response_fail = Mock()
        mock_response_fail.json.return_value = {"ok": False, "error": "rate_limited"}
        mock_response_fail.raise_for_status = Mock()
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_response_success.raise_for_status = Mock()
        
        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]
        
        # メッセージ送信
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Test"}}]
        result = notifier.send_message(
            channel_id="C123456",
            blocks=blocks,
        )
        
        # 検証
        assert result["ok"] is True
        assert mock_post.call_count == 3
    
    @patch("requests.post")
    def test_send_message_all_retries_fail(
        self, mock_post: Mock, notifier: SlackNotifier
    ):
        """全てのリトライが失敗した場合のテスト"""
        # 全て失敗
        mock_response = Mock()
        mock_response.json.return_value = {"ok": False, "error": "rate_limited"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # メッセージ送信（例外が発生するはず）
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Test"}}]
        
        with pytest.raises(Exception) as exc_info:
            notifier.send_message(
                channel_id="C123456",
                blocks=blocks,
            )
        
        assert "メッセージ送信に失敗しました" in str(exc_info.value)
        assert mock_post.call_count == 3  # max_retries
    
    @patch("requests.post")
    def test_update_message_success(self, mock_post: Mock, notifier: SlackNotifier):
        """メッセージ更新成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # メッセージ更新
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Updated"}}]
        result = notifier.update_message(
            channel_id="C123456",
            message_ts="1234567890.123456",
            blocks=blocks,
        )
        
        # 検証
        assert result["ok"] is True
        
        # API呼び出しの検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://slack.com/api/chat.update"
        assert call_args[1]["json"]["channel"] == "C123456"
        assert call_args[1]["json"]["ts"] == "1234567890.123456"
        assert call_args[1]["json"]["blocks"] == blocks
    
    @patch("requests.post")
    def test_open_modal_success(self, mock_post: Mock, notifier: SlackNotifier):
        """モーダル表示成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "view": {"id": "V123456"},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # モーダル表示
        view = {"type": "modal", "title": {"type": "plain_text", "text": "Test"}}
        result = notifier.open_modal(
            trigger_id="12345.67890",
            view=view,
        )
        
        # 検証
        assert result["ok"] is True
        assert result["view"]["id"] == "V123456"
        
        # API呼び出しの検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://slack.com/api/views.open"
        assert call_args[1]["json"]["trigger_id"] == "12345.67890"
        assert call_args[1]["json"]["view"] == view
    
    @patch("requests.post")
    def test_send_reminder_success(self, mock_post: Mock, notifier: SlackNotifier):
        """リマインダー送信成功のテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # リマインダー送信
        result = notifier.send_reminder(
            channel_id="C123456",
            session_id="test-session",
            content_type=ContentType.MINUTES,
            original_message_link="https://example.slack.com/archives/C123/p1234567890",
            reminder_count=1,
        )
        
        # 検証
        assert result["ok"] is True
        
        # API呼び出しの検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://slack.com/api/chat.postMessage"
    
    def test_send_reminder_exceeds_max_count(self, notifier: SlackNotifier):
        """リマインダー送信回数上限超過のテスト"""
        # リマインダー送信（例外が発生するはず）
        with pytest.raises(ValueError) as exc_info:
            notifier.send_reminder(
                channel_id="C123456",
                session_id="test-session",
                content_type=ContentType.MINUTES,
                original_message_link="https://example.slack.com/archives/C123/p1234567890",
                reminder_count=4,  # 上限超過
            )
        
        assert "上限（3回）を超えています" in str(exc_info.value)


class TestSlackNotifierTool:
    """Slack Notifier ツール関数のテスト"""
    
    @patch("agents.tools.slack_notifier.SlackNotifier.send_message")
    def test_send_slack_approval_message_success(self, mock_send: Mock):
        """承認メッセージ送信ツールのテスト"""
        # モックレスポンスを設定
        mock_send.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        
        # ツール実行
        result = send_slack_approval_message(
            channel_id="C123456",
            session_id="test-session",
            content_type="minutes",
            content="これはテスト議事録です。",
            title="週次ミーティング",
            bot_token="xoxb-test-token",
        )
        
        # 検証
        assert "承認メッセージを送信しました" in result
        assert "1234567890.123456" in result
        
        # send_message が呼ばれたことを確認
        mock_send.assert_called_once()
    
    @patch("agents.tools.slack_notifier.SlackNotifier.send_message")
    def test_send_slack_approval_message_error(self, mock_send: Mock):
        """承認メッセージ送信ツールのエラーテスト"""
        # モックで例外を発生させる
        mock_send.side_effect = Exception("API Error")
        
        # ツール実行
        result = send_slack_approval_message(
            channel_id="C123456",
            session_id="test-session",
            content_type="minutes",
            content="これはテスト議事録です。",
            title="週次ミーティング",
            bot_token="xoxb-test-token",
        )
        
        # 検証
        assert "エラー" in result
        assert "API Error" in result
