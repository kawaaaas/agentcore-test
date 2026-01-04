"""エラー通知機能のユニットテスト。

Requirements: 6.2
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from agents.utils.error import create_error_notification, send_error_notification


class TestCreateErrorNotification:
    """create_error_notification関数のテスト"""
    
    def test_basic_error_notification(self):
        """基本的なエラー通知メッセージの生成"""
        # Arrange
        error_type = "Bedrock API Error"
        error_message = "API呼び出しが3回失敗しました"
        
        # Act
        notification = create_error_notification(
            error_type=error_type,
            error_message=error_message,
        )
        
        # Assert
        assert "blocks" in notification
        assert "text" in notification
        assert notification["text"] == f"エラーが発生しました: {error_type}"
        
        # ヘッダーブロックの確認
        header_block = notification["blocks"][0]
        assert header_block["type"] == "header"
        assert "⚠️ エラーが発生しました" in header_block["text"]["text"]
        
        # エラー種別と発生時刻のセクション
        fields_block = notification["blocks"][1]
        assert fields_block["type"] == "section"
        assert len(fields_block["fields"]) == 2
        assert error_type in fields_block["fields"][0]["text"]
        
        # エラー内容のセクション
        error_block = notification["blocks"][2]
        assert error_block["type"] == "section"
        assert error_message in error_block["text"]["text"]
    
    def test_error_notification_with_session_id(self):
        """セッションID付きエラー通知メッセージの生成"""
        # Arrange
        error_type = "S3 Save Error"
        error_message = "S3への保存に失敗しました"
        session_id = "session-123"
        
        # Act
        notification = create_error_notification(
            error_type=error_type,
            error_message=error_message,
            session_id=session_id,
        )
        
        # Assert
        # セッションIDブロックが含まれることを確認
        session_blocks = [
            block for block in notification["blocks"]
            if block.get("type") == "section" and "セッションID" in str(block)
        ]
        assert len(session_blocks) > 0
        assert session_id in str(session_blocks[0])
    
    def test_error_notification_with_context(self):
        """コンテキスト情報付きエラー通知メッセージの生成"""
        # Arrange
        error_type = "Validation Error"
        error_message = "ファイルサイズが上限を超えています"
        context = {
            "file_name": "meeting_20250104.txt",
            "file_size": "2MB",
            "max_size": "1MB",
        }
        
        # Act
        notification = create_error_notification(
            error_type=error_type,
            error_message=error_message,
            context=context,
        )
        
        # Assert
        # コンテキスト情報ブロックが含まれることを確認
        context_blocks = [
            block for block in notification["blocks"]
            if block.get("type") == "section" and "追加情報" in str(block)
        ]
        assert len(context_blocks) > 0
        
        # すべてのコンテキスト情報が含まれることを確認
        context_text = str(context_blocks[0])
        for key, value in context.items():
            assert key in context_text
            assert value in context_text
    
    def test_error_notification_structure(self):
        """エラー通知メッセージの構造が正しいことを確認"""
        # Arrange
        error_type = "Test Error"
        error_message = "Test message"
        
        # Act
        notification = create_error_notification(
            error_type=error_type,
            error_message=error_message,
        )
        
        # Assert
        blocks = notification["blocks"]
        
        # 最低限のブロック数を確認（ヘッダー、フィールド、エラー内容、区切り線、フッター）
        assert len(blocks) >= 5
        
        # 区切り線が含まれることを確認
        divider_blocks = [block for block in blocks if block.get("type") == "divider"]
        assert len(divider_blocks) > 0
        
        # フッターが含まれることを確認
        context_blocks = [block for block in blocks if block.get("type") == "context"]
        assert len(context_blocks) > 0


class TestSendErrorNotification:
    """send_error_notification関数のテスト"""
    
    def test_send_error_notification_success(self):
        """エラー通知の送信が成功する場合"""
        # Arrange
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
        }
        
        channel_id = "C1234567890"
        error_type = "Bedrock API Error"
        error_message = "API呼び出しが失敗しました"
        
        # Act
        response = send_error_notification(
            slack_client=mock_slack_client,
            channel_id=channel_id,
            error_type=error_type,
            error_message=error_message,
        )
        
        # Assert
        assert response["ok"] is True
        assert "ts" in response
        
        # Slack APIが正しく呼ばれたことを確認
        mock_slack_client.chat_postMessage.assert_called_once()
        call_args = mock_slack_client.chat_postMessage.call_args
        assert call_args.kwargs["channel"] == channel_id
        assert "blocks" in call_args.kwargs
        assert "text" in call_args.kwargs
    
    def test_send_error_notification_with_context(self):
        """コンテキスト情報付きエラー通知の送信"""
        # Arrange
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.return_value = {"ok": True}
        
        channel_id = "C1234567890"
        error_type = "S3 Error"
        error_message = "保存に失敗しました"
        context = {"bucket": "test-bucket", "key": "test-key"}
        session_id = "session-456"
        
        # Act
        response = send_error_notification(
            slack_client=mock_slack_client,
            channel_id=channel_id,
            error_type=error_type,
            error_message=error_message,
            context=context,
            session_id=session_id,
        )
        
        # Assert
        assert response["ok"] is True
        mock_slack_client.chat_postMessage.assert_called_once()
    
    def test_send_error_notification_failure(self):
        """Slack送信が失敗する場合"""
        # Arrange
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.side_effect = Exception("Slack API Error")
        
        channel_id = "C1234567890"
        error_type = "Test Error"
        error_message = "Test message"
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            send_error_notification(
                slack_client=mock_slack_client,
                channel_id=channel_id,
                error_type=error_type,
                error_message=error_message,
            )
        
        assert "Failed to send error notification to Slack" in str(exc_info.value)


class TestRetryWithErrorNotification:
    """リトライ機能とエラー通知の統合テスト"""
    
    def test_retry_with_error_callback(self):
        """リトライ失敗時にエラーコールバックが呼ばれることを確認"""
        from agents.utils.retry import with_retry
        
        # Arrange
        error_callback = MagicMock()
        
        @with_retry(max_retries=2, base_delay=0.01, on_final_failure=error_callback)
        def failing_function():
            raise ValueError("Test error")
        
        # Act & Assert
        with pytest.raises(ValueError):
            failing_function()
        
        # エラーコールバックが呼ばれたことを確認
        error_callback.assert_called_once()
        
        # コールバックの引数を確認
        call_args = error_callback.call_args
        exception, func_name, context = call_args[0]
        
        assert isinstance(exception, ValueError)
        assert func_name == "failing_function"
        assert "function_name" in context
        assert "max_retries" in context
        assert "error_type" in context
    
    def test_retry_success_no_callback(self):
        """リトライが成功した場合はコールバックが呼ばれないことを確認"""
        from agents.utils.retry import with_retry
        
        # Arrange
        error_callback = MagicMock()
        attempt_count = {"count": 0}
        
        @with_retry(max_retries=2, base_delay=0.01, on_final_failure=error_callback)
        def eventually_succeeds():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        # Act
        result = eventually_succeeds()
        
        # Assert
        assert result == "success"
        # エラーコールバックは呼ばれない
        error_callback.assert_not_called()
