"""
Task_Persistence ユニットテスト

タスク永続化機能のテスト。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus
from agents.tools.task_persistence import Task_Persistence


@pytest.fixture
def sample_task():
    """サンプルタスクを生成"""
    return Task(
        id="task-001",
        title="テストタスク",
        description="これはテスト用のタスクです",
        assignee="田中太郎",
        due_date=None,
        priority=Priority.HIGH,
        source_quote="議事録からの引用",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
    )


@pytest.fixture
def sample_task_list(sample_task):
    """サンプルタスクリストを生成"""
    return TaskList(
        session_id="session-123",
        minutes_id="minutes-456",
        tasks=[sample_task],
        status=TaskListStatus.PENDING,
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        updated_at=datetime(2025, 1, 1, 10, 0, 0),
    )


@pytest.fixture
def mock_memory_client():
    """モックMemoryクライアントを生成"""
    client = MagicMock()
    client.create_blob_event.return_value = {"eventId": "blob-123"}
    client.get_event.return_value = {
        "content": '{"session_id":"session-123","minutes_id":"minutes-456","tasks":[{"id":"task-001","title":"テストタスク","description":"これはテスト用のタスクです","assignee":"田中太郎","due_date":null,"priority":"high","source_quote":"議事録からの引用","created_at":"2025-01-01T10:00:00"}],"status":"pending","created_at":"2025-01-01T10:00:00","updated_at":"2025-01-01T10:00:00"}'
    }
    return client


@pytest.fixture
def mock_dynamodb_table():
    """モックDynamoDBテーブルを生成"""
    table = MagicMock()
    table.put_item.return_value = {}
    table.get_item.return_value = {
        "Item": {
            "session_id": "session-123",
            "status": "pending",
            "minutes_id": "minutes-456",
            "task_count": 1,
            "memory_blob_id": "blob-123",
            "created_at": "2025-01-01T10:00:00",
            "updated_at": "2025-01-01T10:00:00",
            "expires_at": "2025-01-02T10:00:00",
        }
    }
    return table


class TestTaskPersistence:
    """Task_Persistenceのテストクラス"""
    
    def test_init_with_clients(self, mock_memory_client):
        """初期化テスト: クライアントを指定"""
        persistence = Task_Persistence(
            memory_client=mock_memory_client,
            dynamodb_table_name="test-table",
        )
        
        assert persistence.memory_client == mock_memory_client
        assert persistence.dynamodb_table_name == "test-table"
    
    def test_init_without_clients(self):
        """初期化テスト: クライアントなし"""
        persistence = Task_Persistence()
        
        assert persistence.memory_client is None
        assert persistence.dynamodb_table_name is None
    
    @patch("agents.tools.task_persistence.boto3")
    def test_save_pending_tasks_success(
        self,
        mock_boto3,
        mock_memory_client,
        mock_dynamodb_table,
        sample_task_list,
    ):
        """save_pending_tasks: 正常系"""
        # DynamoDBモックを設定
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        persistence = Task_Persistence(
            memory_client=mock_memory_client,
            dynamodb_table_name="test-table",
        )
        persistence.table = mock_dynamodb_table
        
        # 保存実行
        blob_id = persistence.save_pending_tasks(
            session_id="session-123",
            task_list=sample_task_list,
            slack_channel_id="C123456",
            slack_message_ts="1234567890.123456",
        )
        
        # 検証
        assert blob_id == "blob-123"
        
        # Memory APIが呼ばれたことを確認
        mock_memory_client.create_blob_event.assert_called_once()
        call_args = mock_memory_client.create_blob_event.call_args
        assert call_args[1]["session_id"] == "session-123"
        assert "content" in call_args[1]
        
        # DynamoDB put_itemが呼ばれたことを確認
        mock_dynamodb_table.put_item.assert_called_once()
        put_item_args = mock_dynamodb_table.put_item.call_args[1]["Item"]
        assert put_item_args["session_id"] == "session-123"
        assert put_item_args["status"] == "pending"
        assert put_item_args["task_count"] == 1
        assert put_item_args["memory_blob_id"] == "blob-123"
        assert put_item_args["slack_channel_id"] == "C123456"
        assert put_item_args["slack_message_ts"] == "1234567890.123456"
    
    def test_save_pending_tasks_no_memory_client(self, sample_task_list):
        """save_pending_tasks: Memory clientが未初期化"""
        persistence = Task_Persistence()
        
        with pytest.raises(ValueError, match="Memory client is not initialized"):
            persistence.save_pending_tasks(
                session_id="session-123",
                task_list=sample_task_list,
            )
    
    def test_save_pending_tasks_no_dynamodb_table(
        self,
        mock_memory_client,
        sample_task_list,
    ):
        """save_pending_tasks: DynamoDBテーブルが未初期化"""
        persistence = Task_Persistence(memory_client=mock_memory_client)
        
        with pytest.raises(ValueError, match="DynamoDB table is not initialized"):
            persistence.save_pending_tasks(
                session_id="session-123",
                task_list=sample_task_list,
            )
    
    @patch("agents.tools.task_persistence.boto3")
    def test_load_pending_tasks_success(
        self,
        mock_boto3,
        mock_memory_client,
        mock_dynamodb_table,
    ):
        """load_pending_tasks: 正常系"""
        # DynamoDBモックを設定
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        persistence = Task_Persistence(
            memory_client=mock_memory_client,
            dynamodb_table_name="test-table",
        )
        persistence.table = mock_dynamodb_table
        
        # 復元実行
        task_list = persistence.load_pending_tasks(session_id="session-123")
        
        # 検証
        assert task_list.session_id == "session-123"
        assert task_list.minutes_id == "minutes-456"
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].id == "task-001"
        assert task_list.tasks[0].title == "テストタスク"
        assert task_list.status == TaskListStatus.PENDING
        
        # DynamoDB get_itemが呼ばれたことを確認
        mock_dynamodb_table.get_item.assert_called_once_with(
            Key={"session_id": "session-123"}
        )
        
        # Memory APIが呼ばれたことを確認
        mock_memory_client.get_event.assert_called_once_with(
            session_id="session-123",
            event_id="blob-123",
        )
    
    def test_load_pending_tasks_no_memory_client(self):
        """load_pending_tasks: Memory clientが未初期化"""
        persistence = Task_Persistence()
        
        with pytest.raises(ValueError, match="Memory client is not initialized"):
            persistence.load_pending_tasks(session_id="session-123")
    
    def test_load_pending_tasks_no_dynamodb_table(self, mock_memory_client):
        """load_pending_tasks: DynamoDBテーブルが未初期化"""
        persistence = Task_Persistence(memory_client=mock_memory_client)
        
        with pytest.raises(ValueError, match="DynamoDB table is not initialized"):
            persistence.load_pending_tasks(session_id="session-123")
    
    @patch("agents.tools.task_persistence.boto3")
    def test_load_pending_tasks_not_found(
        self,
        mock_boto3,
        mock_memory_client,
        mock_dynamodb_table,
    ):
        """load_pending_tasks: session_idが見つからない"""
        # DynamoDBモックを設定（Itemなし）
        mock_dynamodb_table.get_item.return_value = {}
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        persistence = Task_Persistence(
            memory_client=mock_memory_client,
            dynamodb_table_name="test-table",
        )
        persistence.table = mock_dynamodb_table
        
        # 復元実行
        with pytest.raises(KeyError, match="No pending tasks found"):
            persistence.load_pending_tasks(session_id="nonexistent-session")
