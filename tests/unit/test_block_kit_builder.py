"""
Block Kit Builder のユニットテスト

BlockKitBuilderクラスの基本機能をテストする。
"""

from datetime import datetime

import pytest

from agents.tools.block_kit_builder import (
    ActionType,
    BlockKitBuilder,
    BlockType,
    ContentType,
    StatusType,
)


class TestBlockKitBuilder:
    """BlockKitBuilderクラスのテスト"""
    
    @pytest.fixture
    def builder(self) -> BlockKitBuilder:
        """BlockKitBuilderインスタンス"""
        return BlockKitBuilder()
    
    def test_create_approval_message_basic(self, builder: BlockKitBuilder):
        """承認メッセージ生成の基本テスト"""
        session_id = "test-session-123"
        content = "これはテスト用の議事録です。"
        title = "週次ミーティング"
        
        blocks = builder.create_approval_message(
            session_id=session_id,
            content_type=ContentType.MINUTES,
            content=content,
            title=title,
        )
        
        # ブロック数の検証
        assert len(blocks) > 0
        
        # ヘッダーブロックの検証
        header_block = blocks[0]
        assert header_block["type"] == BlockType.HEADER.value
        assert "議事録" in header_block["text"]["text"]
        
        # アクションブロックの検証
        action_blocks = [b for b in blocks if b["type"] == BlockType.ACTIONS.value]
        assert len(action_blocks) == 1
        
        action_block = action_blocks[0]
        assert len(action_block["elements"]) == 3
        
        # ボタンの検証
        buttons = action_block["elements"]
        action_ids = [btn["action_id"] for btn in buttons]
        assert f"{ActionType.APPROVE.value}_{session_id}" in action_ids
        assert f"{ActionType.REVISE.value}_{session_id}" in action_ids
        assert f"{ActionType.CANCEL.value}_{session_id}" in action_ids
    
    def test_create_approval_message_tasks(self, builder: BlockKitBuilder):
        """タスク用承認メッセージ生成のテスト"""
        session_id = "test-session-456"
        content = "タスク1: 資料作成\nタスク2: レビュー"
        title = "抽出されたタスク"
        
        blocks = builder.create_approval_message(
            session_id=session_id,
            content_type=ContentType.TASKS,
            content=content,
            title=title,
        )
        
        # ヘッダーにタスクが含まれることを確認
        header_block = blocks[0]
        assert "タスク" in header_block["text"]["text"]
    
    def test_create_approval_message_truncation(self, builder: BlockKitBuilder):
        """長いコンテンツの切り詰めテスト"""
        session_id = "test-session-789"
        # 3000文字を超える長いコンテンツ
        long_content = "非常に長いテキスト。" * 500
        title = "長い議事録"
        
        blocks = builder.create_approval_message(
            session_id=session_id,
            content_type=ContentType.MINUTES,
            content=long_content,
            title=title,
        )
        
        # コンテンツセクションを取得
        content_blocks = [
            b for b in blocks
            if b["type"] == BlockType.SECTION.value and b.get("text")
        ]
        
        # 少なくとも1つのコンテンツブロックが存在
        assert len(content_blocks) > 0
        
        # いずれかのブロックに省略記号が含まれることを確認
        has_truncation = any(
            "省略" in block["text"]["text"]
            for block in content_blocks
        )
        assert has_truncation
    
    def test_create_status_message_approved(self, builder: BlockKitBuilder):
        """承認済みステータスメッセージのテスト"""
        original_blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "テスト"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "内容"}},
            {"type": "actions", "elements": []},
        ]
        
        updated_blocks = builder.create_status_message(
            original_blocks=original_blocks,
            status=StatusType.APPROVED,
            message="承認が完了しました",
        )
        
        # アクションブロックが削除されていることを確認
        action_blocks = [b for b in updated_blocks if b["type"] == BlockType.ACTIONS.value]
        assert len(action_blocks) == 0
        
        # コンテキストブロックが追加されていることを確認
        context_blocks = [b for b in updated_blocks if b["type"] == BlockType.CONTEXT.value]
        assert len(context_blocks) == 1
        
        context_block = context_blocks[0]
        context_text = " ".join([elem["text"] for elem in context_block["elements"]])
        assert "承認済み" in context_text
        assert "承認が完了しました" in context_text
    
    def test_create_status_message_revising(self, builder: BlockKitBuilder):
        """修正中ステータスメッセージのテスト"""
        original_blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "テスト"}},
        ]
        
        updated_blocks = builder.create_status_message(
            original_blocks=original_blocks,
            status=StatusType.REVISING,
        )
        
        # コンテキストブロックを確認
        context_blocks = [b for b in updated_blocks if b["type"] == BlockType.CONTEXT.value]
        assert len(context_blocks) == 1
        
        context_text = " ".join([elem["text"] for elem in context_blocks[0]["elements"]])
        assert "修正中" in context_text
    
    def test_create_status_message_error(self, builder: BlockKitBuilder):
        """エラーステータスメッセージのテスト"""
        original_blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "テスト"}},
        ]
        
        updated_blocks = builder.create_status_message(
            original_blocks=original_blocks,
            status=StatusType.ERROR,
            message="処理中にエラーが発生しました",
        )
        
        # コンテキストブロックを確認
        context_blocks = [b for b in updated_blocks if b["type"] == BlockType.CONTEXT.value]
        assert len(context_blocks) == 1
        
        context_text = " ".join([elem["text"] for elem in context_blocks[0]["elements"]])
        assert "エラー" in context_text
        assert "処理中にエラーが発生しました" in context_text
    
    def test_create_reminder_message(self, builder: BlockKitBuilder):
        """リマインダーメッセージ生成のテスト"""
        session_id = "test-session-reminder"
        original_link = "https://example.slack.com/archives/C123/p1234567890"
        reminder_count = 2
        
        blocks = builder.create_reminder_message(
            session_id=session_id,
            content_type=ContentType.MINUTES,
            original_message_link=original_link,
            reminder_count=reminder_count,
        )
        
        # ヘッダーブロックの検証
        header_block = blocks[0]
        assert header_block["type"] == BlockType.HEADER.value
        assert "リマインダー" in header_block["text"]["text"]
        
        # メッセージセクションの検証
        section_blocks = [b for b in blocks if b["type"] == BlockType.SECTION.value]
        assert len(section_blocks) > 0
        
        # リンクが含まれることを確認
        section_text = section_blocks[0]["text"]["text"]
        assert original_link in section_text
        
        # コンテキストブロックの検証
        context_blocks = [b for b in blocks if b["type"] == BlockType.CONTEXT.value]
        assert len(context_blocks) == 1
        
        context_text = context_blocks[0]["elements"][0]["text"]
        assert str(reminder_count) in context_text
        assert "3" in context_text  # 最大回数
    
    def test_create_feedback_modal_minutes(self, builder: BlockKitBuilder):
        """議事録用フィードバックモーダル生成のテスト"""
        session_id = "test-session-modal"
        
        modal = builder.create_feedback_modal(
            session_id=session_id,
            content_type=ContentType.MINUTES,
        )
        
        # 基本構造の検証
        assert modal["type"] == "modal"
        assert modal["callback_id"] == f"feedback_modal_{session_id}"
        
        # タイトルの検証
        assert "議事録" in modal["title"]["text"]
        
        # ボタンの検証
        assert modal["submit"]["text"] == "送信"
        assert modal["close"]["text"] == "キャンセル"
        
        # 入力ブロックの検証
        assert len(modal["blocks"]) == 1
        input_block = modal["blocks"][0]
        assert input_block["type"] == BlockType.INPUT.value
        assert input_block["block_id"] == f"feedback_input_{session_id}"
        
        # 入力エレメントの検証
        element = input_block["element"]
        assert element["type"] == "plain_text_input"
        assert element["action_id"] == f"feedback_text_{session_id}"
        assert element["multiline"] is True
    
    def test_create_feedback_modal_tasks(self, builder: BlockKitBuilder):
        """タスク用フィードバックモーダル生成のテスト"""
        session_id = "test-session-modal-tasks"
        
        modal = builder.create_feedback_modal(
            session_id=session_id,
            content_type=ContentType.TASKS,
        )
        
        # タイトルにタスクが含まれることを確認
        assert "タスク" in modal["title"]["text"]
    
    def test_truncate_text_short(self, builder: BlockKitBuilder):
        """短いテキストの切り詰めテスト（切り詰めなし）"""
        short_text = "短いテキスト"
        result = builder._truncate_text(short_text)
        
        # 切り詰めが発生しないことを確認
        assert result == short_text
    
    def test_truncate_text_long(self, builder: BlockKitBuilder):
        """長いテキストの切り詰めテスト"""
        long_text = "非常に長いテキスト。" * 500
        result = builder._truncate_text(long_text, max_length=100)
        
        # 切り詰めが発生することを確認（サフィックスを含めて少し長くなる可能性がある）
        assert len(result) < len(long_text)
        assert "省略" in result
    
    def test_truncate_text_exact_limit(self, builder: BlockKitBuilder):
        """ちょうど制限文字数のテキストのテスト"""
        text = "a" * 100
        result = builder._truncate_text(text, max_length=100)
        
        # 切り詰めが発生しないことを確認
        assert result == text

