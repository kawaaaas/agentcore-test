"""
タスク承認フローのユニットテスト

Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
"""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, Mock

import pytest

from agents.tools.task_approval_flow import TaskApprovalFlow
from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus


@pytest.fixture
def sample_task_list():
    """サンプルタスクリストを生成"""
    tasks = [
        Task(
            id="task-1",
            title="タスク1",
            description="タスク1の説明",
            assignee="田中",
            due_date=date(2025, 1, 15),
            priority=Priority.HIGH,
            source_quote="議事録からの引用1",
        ),
        Task(
            id="task-2",
            title="タスク2",
            description="タスク2の説明",
            assignee=None,
            due_date=None,
            priority=Priority.MEDIUM,
            source_quote="議事録からの引用2",
        ),
        Task(
            id="task-3",
            title="タスク3",
            description="タスク3の説明",
            assignee="佐藤",
            due_date=date(2025, 1, 20),
            priority=Priority.LOW,
            source_quote="議事録からの引用3",
        ),
    ]
    
    return TaskList(
        session_id="test-session-123",
        minutes_id="minutes-456",
        tasks=tasks,
        status=TaskListStatus.PENDING,
    )


@pytest.fixture
def approval_flow():
    """TaskApprovalFlowインスタンスを生成"""
    return TaskApprovalFlow()


class TestTaskApprovalMessage:
    """タスク承認メッセージ生成のテスト"""
    
    def test_create_task_approval_message_with_tasks(self, approval_flow, sample_task_list):
        """タスクがある場合の承認メッセージ生成"""
        # Requirements: 5.2
        
        session_id = "test-session-123"
        result = approval_flow.create_task_approval_message(sample_task_list, session_id)
        
        # メッセージ構造の検証
        assert "blocks" in result
        assert "text" in result
        assert result["text"] == "タスクが抽出されました: 3件"
        
        blocks = result["blocks"]
        
        # ヘッダーブロックの検証
        assert blocks[0]["type"] == "header"
        assert "タスクが抽出されました" in blocks[0]["text"]["text"]
        
        # タスク数の検証
        assert "3件" in blocks[1]["text"]["text"]
        
        # タスクセクションの検証（各タスクに削除ボタンがある）
        task_sections = [b for b in blocks if b.get("type") == "section" and b.get("accessory")]
        assert len(task_sections) == 3
        
        # 削除ボタンの検証
        for task_section in task_sections:
            assert task_section["accessory"]["type"] == "button"
            assert "削除" in task_section["accessory"]["text"]["text"]
            assert task_section["accessory"]["style"] == "danger"
        
        # アクションボタンの検証
        action_blocks = [b for b in blocks if b.get("type") == "actions"]
        assert len(action_blocks) == 1
        
        action_elements = action_blocks[0]["elements"]
        assert len(action_elements) == 3
        
        # 承認ボタン
        approve_button = action_elements[0]
        assert approve_button["action_id"] == "approve_tasks"
        assert approve_button["style"] == "primary"
        assert "承認" in approve_button["text"]["text"]
        
        # 修正ボタン
        revise_button = action_elements[1]
        assert revise_button["action_id"] == "request_task_revision"
        assert "修正" in revise_button["text"]["text"]
        
        # キャンセルボタン
        cancel_button = action_elements[2]
        assert cancel_button["action_id"] == "cancel_tasks"
        assert cancel_button["style"] == "danger"
        assert "キャンセル" in cancel_button["text"]["text"]
    
    def test_create_task_approval_message_empty_tasks(self, approval_flow):
        """タスクが空の場合の承認メッセージ生成"""
        # Requirements: 5.2
        
        empty_task_list = TaskList(
            session_id="test-session-123",
            minutes_id="minutes-456",
            tasks=[],
            status=TaskListStatus.PENDING,
        )
        
        session_id = "test-session-123"
        result = approval_flow.create_task_approval_message(empty_task_list, session_id)
        
        # メッセージ構造の検証
        assert "blocks" in result
        assert result["text"] == "タスクが抽出されました: 0件"
        
        blocks = result["blocks"]
        
        # 空メッセージの検証
        empty_message_blocks = [
            b for b in blocks 
            if b.get("type") == "section" and "タスクが見つかりませんでした" in b.get("text", {}).get("text", "")
        ]
        assert len(empty_message_blocks) == 1


class TestTaskRevisionModal:
    """タスク修正モーダル生成のテスト"""
    
    def test_create_task_revision_modal(self, approval_flow, sample_task_list):
        """タスク修正モーダルの生成"""
        # Requirements: 5.4
        
        session_id = "test-session-123"
        result = approval_flow.create_task_revision_modal(session_id, sample_task_list)
        
        # モーダル構造の検証
        assert result["type"] == "modal"
        assert result["callback_id"] == f"task_revision_modal_{session_id}"
        
        # タイトルの検証
        assert "タスクの修正" in result["title"]["text"]
        
        # ボタンの検証
        assert "修正を送信" in result["submit"]["text"]
        assert "キャンセル" in result["close"]["text"]
        
        # 入力ブロックの検証
        blocks = result["blocks"]
        input_blocks = [b for b in blocks if b.get("type") == "input"]
        assert len(input_blocks) == 1
        
        input_block = input_blocks[0]
        assert input_block["block_id"] == "task_revision_instructions"
        assert input_block["element"]["action_id"] == "task_revision_text"
        assert input_block["element"]["multiline"] is True
        
        # メタデータの検証
        metadata = json.loads(result["private_metadata"])
        assert metadata["session_id"] == session_id


class TestAddTaskModal:
    """タスク追加モーダル生成のテスト"""
    
    def test_create_add_task_modal(self, approval_flow):
        """タスク追加モーダルの生成"""
        # Requirements: 5.6
        
        session_id = "test-session-123"
        result = approval_flow.create_add_task_modal(session_id)
        
        # モーダル構造の検証
        assert result["type"] == "modal"
        assert result["callback_id"] == f"add_task_modal_{session_id}"
        
        # タイトルの検証
        assert "タスクの追加" in result["title"]["text"]
        
        # ボタンの検証
        assert "追加" in result["submit"]["text"]
        assert "キャンセル" in result["close"]["text"]
        
        # 入力ブロックの検証
        blocks = result["blocks"]
        input_blocks = [b for b in blocks if b.get("type") == "input"]
        assert len(input_blocks) == 3
        
        # タイトル入力
        title_block = input_blocks[0]
        assert title_block["block_id"] == "task_title"
        assert title_block["element"]["action_id"] == "title_input"
        
        # 説明入力
        description_block = input_blocks[1]
        assert description_block["block_id"] == "task_description"
        assert description_block["element"]["action_id"] == "description_input"
        assert description_block["element"]["multiline"] is True
        
        # 担当者入力（オプション）
        assignee_block = input_blocks[2]
        assert assignee_block["block_id"] == "task_assignee"
        assert assignee_block["element"]["action_id"] == "assignee_input"
        assert assignee_block["optional"] is True


class TestActionHandling:
    """アクション処理のテスト"""
    
    def test_handle_approve_action(self, approval_flow):
        """承認アクションの処理"""
        # Requirements: 5.3
        
        session_id = "test-session-123"
        user_id = "user-456"
        
        result = approval_flow.handle_action("approve_tasks", session_id, user_id)
        
        # 状態遷移の検証: PENDING → APPROVED
        assert result["status"] == TaskListStatus.APPROVED
        assert "承認されました" in result["message"]
        assert result["user_id"] == user_id
        assert isinstance(result["updated_at"], datetime)
    
    def test_handle_revision_action(self, approval_flow):
        """修正リクエストアクションの処理"""
        # Requirements: 5.4
        
        session_id = "test-session-123"
        user_id = "user-456"
        
        result = approval_flow.handle_action("request_task_revision", session_id, user_id)
        
        # 状態遷移の検証: PENDING → REVISION_REQUESTED
        assert result["status"] == TaskListStatus.REVISION_REQUESTED
        assert "修正内容を入力してください" in result["message"]
        assert result["user_id"] == user_id
        assert isinstance(result["updated_at"], datetime)
    
    def test_handle_cancel_action(self, approval_flow):
        """キャンセルアクションの処理"""
        # Requirements: 5.4
        
        session_id = "test-session-123"
        user_id = "user-456"
        
        result = approval_flow.handle_action("cancel_tasks", session_id, user_id)
        
        # 状態遷移の検証: PENDING → CANCELLED
        assert result["status"] == TaskListStatus.CANCELLED
        assert "キャンセルされました" in result["message"]
        assert result["user_id"] == user_id
        assert isinstance(result["updated_at"], datetime)
    
    def test_handle_unknown_action(self, approval_flow):
        """不明なアクションの処理"""
        session_id = "test-session-123"
        
        with pytest.raises(ValueError, match="Unknown action_id"):
            approval_flow.handle_action("unknown_action", session_id)


class TestTaskOperations:
    """タスク操作のテスト"""
    
    def test_delete_task(self, approval_flow, sample_task_list):
        """タスクの削除"""
        # Requirements: 5.5
        
        task_id_to_delete = "task-2"
        
        # 削除前のタスク数
        assert len(sample_task_list.tasks) == 3
        
        # タスクを削除
        updated_task_list = approval_flow.delete_task(
            sample_task_list, 
            task_id_to_delete,
            user_id="user-123"
        )
        
        # 削除後のタスク数
        assert len(updated_task_list.tasks) == 2
        
        # 削除されたタスクが含まれていないことを確認
        task_ids = [t.id for t in updated_task_list.tasks]
        assert task_id_to_delete not in task_ids
        
        # 他のタスクは残っていることを確認
        assert "task-1" in task_ids
        assert "task-3" in task_ids
        
        # updated_atが更新されていることを確認
        assert updated_task_list.updated_at > sample_task_list.updated_at
    
    def test_delete_nonexistent_task(self, approval_flow, sample_task_list):
        """存在しないタスクの削除"""
        # Requirements: 5.5
        
        with pytest.raises(ValueError, match="Task with id .* not found"):
            approval_flow.delete_task(sample_task_list, "nonexistent-task-id")
    
    def test_add_task(self, approval_flow, sample_task_list):
        """タスクの追加"""
        # Requirements: 5.6
        
        new_task = Task(
            id="task-4",
            title="新しいタスク",
            description="新しいタスクの説明",
            assignee="鈴木",
            due_date=date(2025, 1, 25),
            priority=Priority.MEDIUM,
            source_quote="新しい引用",
        )
        
        # 追加前のタスク数
        assert len(sample_task_list.tasks) == 3
        
        # タスクを追加
        updated_task_list = approval_flow.add_task(
            sample_task_list, 
            new_task,
            user_id="user-123"
        )
        
        # 追加後のタスク数
        assert len(updated_task_list.tasks) == 4
        
        # 追加されたタスクが含まれていることを確認
        task_ids = [t.id for t in updated_task_list.tasks]
        assert "task-4" in task_ids
        
        # 追加されたタスクの内容を確認
        added_task = next(t for t in updated_task_list.tasks if t.id == "task-4")
        assert added_task.title == "新しいタスク"
        assert added_task.assignee == "鈴木"
        
        # updated_atが更新されていることを確認
        assert updated_task_list.updated_at > sample_task_list.updated_at


class TestPersistence:
    """永続化のテスト"""
    
    def test_save_pending_tasks_without_clients(self, approval_flow, sample_task_list):
        """クライアントが初期化されていない場合のエラー"""
        # Requirements: 8.1, 8.2
        
        session_id = "test-session-123"
        
        with pytest.raises(ValueError, match="Memory client is not initialized"):
            approval_flow.save_pending_tasks(session_id, sample_task_list)
    
    def test_get_pending_tasks_without_clients(self, approval_flow):
        """クライアントが初期化されていない場合のエラー"""
        # Requirements: 8.1, 8.2
        
        session_id = "test-session-123"
        
        with pytest.raises(ValueError, match="Memory client is not initialized"):
            approval_flow.get_pending_tasks(session_id)
    
    def test_save_and_get_pending_tasks(self, sample_task_list):
        """承認待ちタスクの保存と取得"""
        # Requirements: 8.1, 8.2, 8.3, 8.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_blob_event.return_value = {"eventId": "blob-123"}
        mock_memory_client.get_event.return_value = {
            "content": sample_task_list.model_dump_json()
        }
        
        mock_table = Mock()
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {
            "Item": {
                "session_id": "test-session-123",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "memory_blob_id": "blob-123",
                "expires_at": (datetime.now()).isoformat(),
                "task_count": 3,
            }
        }
        
        # TaskApprovalFlowインスタンスを作成
        approval_flow = TaskApprovalFlow(
            memory_client=mock_memory_client,
        )
        approval_flow.table = mock_table
        
        session_id = "test-session-123"
        
        # 保存
        blob_id = approval_flow.save_pending_tasks(
            session_id,
            sample_task_list,
            slack_channel_id="C123456",
            slack_message_ts="1234567890.123456",
        )
        
        assert blob_id == "blob-123"
        
        # Memory APIが呼ばれたことを確認
        mock_memory_client.create_blob_event.assert_called_once()
        
        # DynamoDB APIが呼ばれたことを確認
        mock_table.put_item.assert_called_once()
        
        # 取得
        retrieved_task_list = approval_flow.get_pending_tasks(session_id)
        
        # 取得したタスクリストの検証
        assert retrieved_task_list.session_id == sample_task_list.session_id
        assert retrieved_task_list.minutes_id == sample_task_list.minutes_id
        assert len(retrieved_task_list.tasks) == len(sample_task_list.tasks)
        
        # Memory APIが呼ばれたことを確認
        mock_memory_client.get_event.assert_called_once()
        
        # DynamoDB APIが呼ばれたことを確認
        mock_table.get_item.assert_called_once()


class TestSTMIntegration:
    """STM連携のテスト"""
    
    def test_save_conversation_to_stm(self):
        """STMへの会話保存"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        session_id = "test-session-123"
        actor_id = "user-456"
        role = "user"
        message = "タスクリストを承認しました"
        
        # STMに会話を保存
        event_id = approval_flow.save_conversation_to_stm(
            session_id=session_id,
            actor_id=actor_id,
            role=role,
            message=message,
        )
        
        # イベントIDが返されることを確認
        assert event_id == "event-123"
        
        # Memory APIが呼ばれたことを確認
        mock_memory_client.create_event.assert_called_once_with(
            session_id=session_id,
            actor_id=actor_id,
            role=role,
            content=message,
        )
    
    def test_save_conversation_to_stm_without_client(self):
        """Memory clientがない場合のSTM保存"""
        # Requirements: 9.5
        
        approval_flow = TaskApprovalFlow()
        
        # Memory clientがない場合はNoneを返す
        event_id = approval_flow.save_conversation_to_stm(
            session_id="test-session-123",
            actor_id="user-456",
            role="user",
            message="テストメッセージ",
        )
        
        assert event_id is None
    
    def test_handle_action_saves_to_stm(self):
        """アクション処理時にSTMに保存されることを確認"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        session_id = "test-session-123"
        user_id = "user-456"
        
        # 承認アクションを実行
        result = approval_flow.handle_action("approve_tasks", session_id, user_id)
        
        # STMに保存されたことを確認
        mock_memory_client.create_event.assert_called_once()
        call_args = mock_memory_client.create_event.call_args
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["actor_id"] == user_id
        assert call_args[1]["role"] == "user"
        assert "承認" in call_args[1]["content"]
    
    def test_delete_task_saves_to_stm(self, sample_task_list):
        """タスク削除時にSTMに保存されることを確認"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        user_id = "user-456"
        task_id = "task-1"
        
        # タスクを削除
        updated_task_list = approval_flow.delete_task(
            sample_task_list,
            task_id,
            user_id=user_id,
        )
        
        # STMに保存されたことを確認
        mock_memory_client.create_event.assert_called_once()
        call_args = mock_memory_client.create_event.call_args
        assert call_args[1]["session_id"] == sample_task_list.session_id
        assert call_args[1]["actor_id"] == user_id
        assert call_args[1]["role"] == "user"
        assert "削除" in call_args[1]["content"]
    
    def test_add_task_saves_to_stm(self, sample_task_list):
        """タスク追加時にSTMに保存されることを確認"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        user_id = "user-456"
        new_task = Task(
            id="task-4",
            title="新しいタスク",
            description="新しいタスクの説明",
            assignee="鈴木",
            due_date=date(2025, 1, 25),
            priority=Priority.MEDIUM,
            source_quote="新しい引用",
        )
        
        # タスクを追加
        updated_task_list = approval_flow.add_task(
            sample_task_list,
            new_task,
            user_id=user_id,
        )
        
        # STMに保存されたことを確認
        mock_memory_client.create_event.assert_called_once()
        call_args = mock_memory_client.create_event.call_args
        assert call_args[1]["session_id"] == sample_task_list.session_id
        assert call_args[1]["actor_id"] == user_id
        assert call_args[1]["role"] == "user"
        assert "追加" in call_args[1]["content"]
    
    def test_handle_revision_submission(self):
        """修正指示送信時にSTMに保存されることを確認"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        session_id = "test-session-123"
        user_id = "user-456"
        revision_instructions = "タスク1の担当者を変更してください"
        
        # 修正指示を送信
        approval_flow.handle_revision_submission(
            session_id=session_id,
            user_id=user_id,
            revision_instructions=revision_instructions,
        )
        
        # STMに保存されたことを確認
        mock_memory_client.create_event.assert_called_once()
        call_args = mock_memory_client.create_event.call_args
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["actor_id"] == user_id
        assert call_args[1]["role"] == "user"
        assert revision_instructions in call_args[1]["content"]
    
    def test_create_task_approval_message_saves_to_stm(self, sample_task_list):
        """タスク承認メッセージ生成時にSTMに保存されることを確認"""
        # Requirements: 9.5
        
        # モッククライアントを作成
        mock_memory_client = Mock()
        mock_memory_client.create_event.return_value = {"eventId": "event-123"}
        
        approval_flow = TaskApprovalFlow(memory_client=mock_memory_client)
        
        session_id = "test-session-123"
        
        # メッセージを生成
        result = approval_flow.create_task_approval_message(
            sample_task_list,
            session_id,
        )
        
        # STMに保存されたことを確認
        mock_memory_client.create_event.assert_called_once()
        call_args = mock_memory_client.create_event.call_args
        assert call_args[1]["session_id"] == session_id
        assert call_args[1]["actor_id"] == "assistant"
        assert call_args[1]["role"] == "assistant"
        assert "抽出" in call_args[1]["content"]
