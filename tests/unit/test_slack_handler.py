"""
Slack Handler のユニットテスト

SlackHandlerクラスの基本機能をテストする。
"""

import hashlib
import hmac
import json
import time

import pytest

from agents.tools.slack_handler import ActionType, SlackHandler


class TestSlackHandler:
    """SlackHandlerクラスのテスト"""
    
    @pytest.fixture
    def handler(self) -> SlackHandler:
        """SlackHandlerインスタンス"""
        return SlackHandler(signing_secret="test_signing_secret")
    
    def test_verify_signature_valid(self, handler: SlackHandler):
        """有効な署名の検証テスト"""
        timestamp = str(int(time.time()))
        body = "test_body"
        
        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = (
            "v0="
            + hmac.new(
                handler.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        
        result = handler.verify_signature(timestamp, body, signature)
        assert result is True
    
    def test_verify_signature_invalid(self, handler: SlackHandler):
        """無効な署名の検証テスト"""
        timestamp = str(int(time.time()))
        body = "test_body"
        invalid_signature = "v0=invalid_signature"
        
        result = handler.verify_signature(timestamp, body, invalid_signature)
        assert result is False
    
    def test_verify_signature_expired_timestamp(self, handler: SlackHandler):
        """期限切れタイムスタンプの検証テスト"""
        # 10分前のタイムスタンプ（5分の許容時間を超える）
        old_timestamp = str(int(time.time()) - 600)
        body = "test_body"
        
        # 正しい署名を生成（タイムスタンプは古い）
        sig_basestring = f"v0:{old_timestamp}:{body}"
        signature = (
            "v0="
            + hmac.new(
                handler.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        
        result = handler.verify_signature(old_timestamp, body, signature)
        assert result is False
    
    def test_verify_signature_invalid_timestamp_format(self, handler: SlackHandler):
        """無効なタイムスタンプフォーマットの検証テスト"""
        timestamp = "invalid_timestamp"
        body = "test_body"
        signature = "v0=some_signature"
        
        result = handler.verify_signature(timestamp, body, signature)
        assert result is False
    
    def test_parse_interaction_valid(self, handler: SlackHandler):
        """有効なペイロードのパーステスト"""
        payload_dict = {
            "type": "block_actions",
            "actions": [{"action_id": "approve_session123"}],
        }
        payload_str = json.dumps(payload_dict)
        
        result = handler.parse_interaction(payload_str)
        assert result == payload_dict
        assert result["type"] == "block_actions"
    
    def test_parse_interaction_invalid_json(self, handler: SlackHandler):
        """無効なJSONのパーステスト"""
        invalid_payload = "not a valid json"
        
        with pytest.raises(ValueError, match="Failed to parse interaction payload"):
            handler.parse_interaction(invalid_payload)
    
    def test_handle_block_action_approve(self, handler: SlackHandler):
        """承認アクションの処理テスト"""
        payload = {
            "actions": [
                {
                    "action_id": "approve_session123",
                    "value": "session123",
                }
            ]
        }
        
        action_type, session_id = handler.handle_block_action(payload)
        assert action_type == ActionType.APPROVE
        assert session_id == "session123"
    
    def test_handle_block_action_revise(self, handler: SlackHandler):
        """修正アクションの処理テスト"""
        payload = {
            "actions": [
                {
                    "action_id": "revise_session456",
                    "value": "session456",
                }
            ]
        }
        
        action_type, session_id = handler.handle_block_action(payload)
        assert action_type == ActionType.REVISE
        assert session_id == "session456"
    
    def test_handle_block_action_cancel(self, handler: SlackHandler):
        """キャンセルアクションの処理テスト"""
        payload = {
            "actions": [
                {
                    "action_id": "cancel_session789",
                    "value": "session789",
                }
            ]
        }
        
        action_type, session_id = handler.handle_block_action(payload)
        assert action_type == ActionType.CANCEL
        assert session_id == "session789"
    
    def test_handle_block_action_no_actions(self, handler: SlackHandler):
        """アクションなしのペイロード処理テスト"""
        payload = {"actions": []}
        
        with pytest.raises(ValueError, match="No actions found in payload"):
            handler.handle_block_action(payload)
    
    def test_handle_block_action_invalid_action_id(self, handler: SlackHandler):
        """無効なaction_idの処理テスト（アンダースコアなし）"""
        payload = {
            "actions": [
                {
                    "action_id": "invalidformat",
                    "value": "session123",
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Invalid action_id format"):
            handler.handle_block_action(payload)
    
    def test_handle_block_action_unknown_action_type(self, handler: SlackHandler):
        """未知のアクションタイプの処理テスト"""
        payload = {
            "actions": [
                {
                    "action_id": "unknown_session123",
                    "value": "session123",
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Unknown action type"):
            handler.handle_block_action(payload)
    
    def test_handle_view_submission_valid(self, handler: SlackHandler):
        """有効なビュー送信の処理テスト"""
        session_id = "session123"
        feedback_text = "これは修正内容です"
        
        payload = {
            "view": {
                "callback_id": f"feedback_modal_{session_id}",
                "state": {
                    "values": {
                        f"feedback_input_{session_id}": {
                            f"feedback_text_{session_id}": {
                                "value": feedback_text,
                            }
                        }
                    }
                },
            }
        }
        
        result_session_id, result_feedback = handler.handle_view_submission(payload)
        assert result_session_id == session_id
        assert result_feedback == feedback_text
    
    def test_handle_view_submission_empty_feedback(self, handler: SlackHandler):
        """空のフィードバックの処理テスト"""
        session_id = "session123"
        
        payload = {
            "view": {
                "callback_id": f"feedback_modal_{session_id}",
                "state": {
                    "values": {
                        f"feedback_input_{session_id}": {
                            f"feedback_text_{session_id}": {
                                "value": "   ",  # 空白のみ
                            }
                        }
                    }
                },
            }
        }
        
        with pytest.raises(ValueError, match="Feedback text cannot be empty"):
            handler.handle_view_submission(payload)
    
    def test_handle_view_submission_whitespace_only(self, handler: SlackHandler):
        """空白のみのフィードバックの処理テスト"""
        session_id = "session123"
        
        payload = {
            "view": {
                "callback_id": f"feedback_modal_{session_id}",
                "state": {
                    "values": {
                        f"feedback_input_{session_id}": {
                            f"feedback_text_{session_id}": {
                                "value": "\n\t  \n",
                            }
                        }
                    }
                },
            }
        }
        
        with pytest.raises(ValueError, match="Feedback text cannot be empty"):
            handler.handle_view_submission(payload)
    
    def test_handle_view_submission_invalid_callback_id(self, handler: SlackHandler):
        """無効なcallback_idの処理テスト"""
        payload = {
            "view": {
                "callback_id": "invalid_callback_id",
                "state": {"values": {}},
            }
        }
        
        with pytest.raises(ValueError, match="Invalid callback_id format"):
            handler.handle_view_submission(payload)
    
    def test_handle_view_submission_missing_input_block(self, handler: SlackHandler):
        """入力ブロックが見つからない場合のテスト"""
        session_id = "session123"
        
        payload = {
            "view": {
                "callback_id": f"feedback_modal_{session_id}",
                "state": {
                    "values": {}  # 入力ブロックなし
                },
            }
        }
        
        with pytest.raises(ValueError, match="Input block not found"):
            handler.handle_view_submission(payload)
    
    def test_handle_view_submission_strips_whitespace(self, handler: SlackHandler):
        """フィードバックテキストの前後空白削除テスト"""
        session_id = "session123"
        feedback_text = "  修正内容  "
        
        payload = {
            "view": {
                "callback_id": f"feedback_modal_{session_id}",
                "state": {
                    "values": {
                        f"feedback_input_{session_id}": {
                            f"feedback_text_{session_id}": {
                                "value": feedback_text,
                            }
                        }
                    }
                },
            }
        }
        
        result_session_id, result_feedback = handler.handle_view_submission(payload)
        assert result_feedback == "修正内容"  # 前後の空白が削除される

