"""
タスクモデルのユニットテスト

Requirements: 2.1, 2.2, 2.4, 2.5
"""

from datetime import date, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus


class TestPriority:
    """Priority Enumのテスト"""
    
    def test_priority_values(self):
        """優先度の値が正しいことを確認"""
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestTask:
    """Taskモデルのテスト"""
    
    def test_create_task_with_all_fields(self):
        """すべてのフィールドを指定してタスクを作成"""
        task = Task(
            title="テストタスク",
            description="これはテスト用のタスクです",
            assignee="山田太郎",
            due_date=date(2025, 12, 31),
            priority=Priority.HIGH,
            source_quote="議事録からの引用",
        )
        
        assert task.title == "テストタスク"
        assert task.description == "これはテスト用のタスクです"
        assert task.assignee == "山田太郎"
        assert task.due_date == date(2025, 12, 31)
        assert task.priority == Priority.HIGH
        assert task.source_quote == "議事録からの引用"
        
        # IDは自動生成される
        assert task.id is not None
        assert UUID(task.id)  # 有効なUUIDであることを確認
        
        # created_atは自動生成される
        assert isinstance(task.created_at, datetime)
    
    def test_create_task_with_optional_fields_none(self):
        """オプションフィールドをNoneにしてタスクを作成"""
        task = Task(
            title="タスク",
            description="説明",
            assignee=None,
            due_date=None,
            priority=Priority.MEDIUM,
            source_quote="引用",
        )
        
        assert task.assignee is None
        assert task.due_date is None
    
    def test_task_title_min_length(self):
        """タイトルの最小長制約をテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="",  # 空文字列
                description="説明",
                priority=Priority.LOW,
                source_quote="引用",
            )
        
        assert "title" in str(exc_info.value)
    
    def test_task_title_max_length(self):
        """タイトルの最大長制約をテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="あ" * 101,  # 101文字
                description="説明",
                priority=Priority.LOW,
                source_quote="引用",
            )
        
        assert "title" in str(exc_info.value)
    
    def test_task_title_exactly_100_chars(self):
        """タイトルがちょうど100文字の場合は成功"""
        task = Task(
            title="あ" * 100,
            description="説明",
            priority=Priority.LOW,
            source_quote="引用",
        )
        
        assert len(task.title) == 100
    
    def test_task_description_required(self):
        """説明が必須であることをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="タイトル",
                priority=Priority.LOW,
                source_quote="引用",
            )
        
        assert "description" in str(exc_info.value)
    
    def test_task_source_quote_required(self):
        """引用が必須であることをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="タイトル",
                description="説明",
                priority=Priority.LOW,
            )
        
        assert "source_quote" in str(exc_info.value)


class TestTaskListStatus:
    """TaskListStatus Enumのテスト"""
    
    def test_status_values(self):
        """ステータスの値が正しいことを確認"""
        assert TaskListStatus.PENDING.value == "pending"
        assert TaskListStatus.APPROVED.value == "approved"
        assert TaskListStatus.REVISION_REQUESTED.value == "revision_requested"
        assert TaskListStatus.CANCELLED.value == "cancelled"


class TestTaskList:
    """TaskListモデルのテスト"""
    
    def test_create_task_list_with_tasks(self):
        """タスクを含むタスクリストを作成"""
        task1 = Task(
            title="タスク1",
            description="説明1",
            priority=Priority.HIGH,
            source_quote="引用1",
        )
        task2 = Task(
            title="タスク2",
            description="説明2",
            priority=Priority.LOW,
            source_quote="引用2",
        )
        
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task1, task2],
        )
        
        assert task_list.session_id == "session-123"
        assert task_list.minutes_id == "minutes-456"
        assert len(task_list.tasks) == 2
        assert task_list.status == TaskListStatus.PENDING  # デフォルト値
        assert isinstance(task_list.created_at, datetime)
        assert isinstance(task_list.updated_at, datetime)
    
    def test_create_empty_task_list(self):
        """空のタスクリストを作成"""
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        assert len(task_list.tasks) == 0
        assert task_list.status == TaskListStatus.PENDING
    
    def test_task_list_with_custom_status(self):
        """カスタムステータスでタスクリストを作成"""
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            status=TaskListStatus.APPROVED,
        )
        
        assert task_list.status == TaskListStatus.APPROVED
    
    def test_task_list_session_id_required(self):
        """session_idが必須であることをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            TaskList(
                minutes_id="minutes-456",
            )
        
        assert "session_id" in str(exc_info.value)
    
    def test_task_list_minutes_id_required(self):
        """minutes_idが必須であることをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            TaskList(
                session_id="session-123",
            )
        
        assert "minutes_id" in str(exc_info.value)
