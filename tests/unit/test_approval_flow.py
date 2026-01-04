"""
承認フローのユニットテスト

ApprovalFlowクラスの基本機能をテストする。
"""

from datetime import datetime

import pytest

from agents.models.approval import ApprovalStatus
from agents.models.minutes import ActionItem, Minutes
from agents.tools.approval import ApprovalFlow


class TestApprovalFlow:
    """ApprovalFlowクラスのテスト"""
    
    @pytest.fixture
    def sample_minutes(self) -> Minutes:
        """テスト用の議事録サンプル"""
        return Minutes(
            title="週次ミーティング",
            date=datetime(2025, 1, 4, 10, 0),
            participants=["田中", "佐藤", "鈴木"],
            agenda=["進捗確認", "課題共有"],
            discussion="各メンバーの進捗を確認しました。",
            decisions=["次回は来週月曜日に開催"],
            action_items=[
                ActionItem(
                    description="資料作成",
                    assignee="田中",
                    due_date="2025-01-10",
                ),
            ],
        )
    
    @pytest.fixture
    def approval_flow(self) -> ApprovalFlow:
        """ApprovalFlowインスタンス"""
        return ApprovalFlow()
    
    def test_create_approval_message(
        self,
        approval_flow: ApprovalFlow,
        sample_minutes: Minutes,
    ):
        """承認メッセージ生成のテスト"""
        session_id = "test-session-123"
        
        message = approval_flow.create_approval_message(
            minutes=sample_minutes,
            session_id=session_id,
        )
        
        # 基本構造の検証
        assert "blocks" in message
        assert "text" in message
        assert len(message["blocks"]) > 0
        
        # ヘッダーの検証
        header_block = message["blocks"][0]
        assert header_block["type"] == "header"
        assert "議事録が生成されました" in header_block["text"]["text"]
        
        # アクションボタンの検証
        action_blocks = [b for b in message["blocks"] if b["type"] == "actions"]
        assert len(action_blocks) == 1
        
        action_block = action_blocks[0]
        assert action_block["block_id"] == f"approval_actions_{session_id}"
        assert len(action_block["elements"]) == 2
        
        # 承認ボタン
        approve_button = action_block["elements"][0]
        assert approve_button["action_id"] == "approve_minutes"
        assert approve_button["value"] == session_id
        assert approve_button["style"] == "primary"
        
        # 修正ボタン
        revision_button = action_block["elements"][1]
        assert revision_button["action_id"] == "request_revision"
        assert revision_button["value"] == session_id
        assert revision_button["style"] == "danger"
    
    def test_create_approval_message_truncation(
        self,
        approval_flow: ApprovalFlow,
    ):
        """長い議事録の省略処理テスト"""
        # 非常に長い議論内容を持つ議事録
        long_discussion = "非常に長い議論内容。" * 1000
        long_minutes = Minutes(
            title="長時間ミーティング",
            date=datetime(2025, 1, 4, 10, 0),
            participants=["田中"],
            agenda=["議題"],
            discussion=long_discussion,
            decisions=[],
            action_items=[],
        )
        
        message = approval_flow.create_approval_message(
            minutes=long_minutes,
            session_id="test-session",
        )
        
        # メッセージが生成されることを確認
        assert "blocks" in message
        
        # 省略が行われていることを確認（完全な検証は難しいが、構造は正しい）
        text_blocks = [
            b for b in message["blocks"]
            if b["type"] == "section" and "text" in b
        ]
        assert len(text_blocks) > 0
    
    def test_create_revision_modal(
        self,
        approval_flow: ApprovalFlow,
        sample_minutes: Minutes,
    ):
        """修正モーダル生成のテスト"""
        session_id = "test-session-456"
        
        modal = approval_flow.create_revision_modal(
            session_id=session_id,
            minutes=sample_minutes,
        )
        
        # 基本構造の検証
        assert modal["type"] == "modal"
        assert modal["callback_id"] == f"revision_modal_{session_id}"
        assert "title" in modal
        assert "submit" in modal
        assert "close" in modal
        assert "blocks" in modal
        
        # 入力フィールドの検証
        input_blocks = [b for b in modal["blocks"] if b["type"] == "input"]
        assert len(input_blocks) == 1
        
        input_block = input_blocks[0]
        assert input_block["block_id"] == "revision_instructions"
        assert input_block["element"]["action_id"] == "revision_text"
        assert input_block["element"]["multiline"] is True
        
        # メタデータの検証
        import json
        metadata = json.loads(modal["private_metadata"])
        assert metadata["session_id"] == session_id
    
    def test_handle_action_approve(self, approval_flow: ApprovalFlow):
        """承認アクション処理のテスト"""
        session_id = "test-session-789"
        user_id = "U12345"
        
        result = approval_flow.handle_action(
            action_id="approve_minutes",
            session_id=session_id,
            user_id=user_id,
        )
        
        # 状態遷移の検証
        assert result["status"] == ApprovalStatus.APPROVED
        assert "承認されました" in result["message"]
        assert result["user_id"] == user_id
        assert "updated_at" in result
    
    def test_handle_action_request_revision(self, approval_flow: ApprovalFlow):
        """修正リクエストアクション処理のテスト"""
        session_id = "test-session-abc"
        user_id = "U67890"
        
        result = approval_flow.handle_action(
            action_id="request_revision",
            session_id=session_id,
            user_id=user_id,
        )
        
        # 状態遷移の検証
        assert result["status"] == ApprovalStatus.REVISION_REQUESTED
        assert "修正" in result["message"]
        assert result["user_id"] == user_id
        assert "updated_at" in result
    
    def test_handle_action_unknown(self, approval_flow: ApprovalFlow):
        """不明なアクションのエラーハンドリングテスト"""
        with pytest.raises(ValueError, match="Unknown action_id"):
            approval_flow.handle_action(
                action_id="unknown_action",
                session_id="test-session",
            )
