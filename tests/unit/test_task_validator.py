"""
タスク検証のユニットテスト

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

from datetime import date

import pytest

from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus
from agents.tools.task_validator import Task_Validator, TaskValidationError


class TestTaskValidator:
    """Task_Validatorのテスト"""
    
    def test_validate_valid_task(self):
        """有効なタスクの検証が成功することを確認"""
        task = Task(
            title="有効なタスク",
            description="説明",
            assignee="担当者",
            due_date=date(2025, 12, 31),
            priority=Priority.HIGH,
            source_quote="引用",
        )
        
        # 例外が発生しないことを確認
        Task_Validator.validate_task(task)
    
    def test_validate_task_empty_title(self):
        """空のタイトルで検証が失敗することを確認 (Requirement 3.1)"""
        # Pydanticの検証をバイパスして空のタイトルを設定
        task = Task(
            title="一時的なタイトル",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        task.title = ""  # 強制的に空文字列を設定
        
        with pytest.raises(TaskValidationError) as exc_info:
            Task_Validator.validate_task(task)
        
        assert "タイトルが空です" in str(exc_info.value)
    
    def test_validate_task_whitespace_only_title(self):
        """空白のみのタイトルで検証が失敗することを確認 (Requirement 3.1)"""
        task = Task(
            title="   ",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        
        with pytest.raises(TaskValidationError) as exc_info:
            Task_Validator.validate_task(task)
        
        assert "タイトルが空です" in str(exc_info.value)
    
    def test_validate_task_title_exceeds_max_length(self):
        """タイトルが100文字を超える場合に検証が失敗することを確認 (Requirement 3.2)"""
        # Pydanticの検証をバイパスして長いタイトルを設定
        task = Task(
            title="一時的なタイトル",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        task.title = "あ" * 101  # 強制的に101文字を設定
        
        with pytest.raises(TaskValidationError) as exc_info:
            Task_Validator.validate_task(task)
        
        assert "100文字を超えています" in str(exc_info.value)
    
    def test_validate_task_title_exactly_100_chars(self):
        """タイトルがちょうど100文字の場合は検証が成功することを確認"""
        task = Task(
            title="あ" * 100,
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        
        # 例外が発生しないことを確認
        Task_Validator.validate_task(task)
    
    def test_validate_task_invalid_priority(self):
        """無効な優先度で検証が失敗することを確認 (Requirement 3.3)"""
        # Pydanticの検証をバイパスして無効な優先度を設定
        task = Task(
            title="タスク",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        # 強制的に無効な値を設定
        task.priority = "invalid"
        
        with pytest.raises(TaskValidationError) as exc_info:
            Task_Validator.validate_task(task)
        
        assert "無効な優先度です" in str(exc_info.value)
    
    def test_validate_task_valid_due_date(self):
        """有効な期限で検証が成功することを確認 (Requirement 3.4)"""
        task = Task(
            title="タスク",
            description="説明",
            due_date=date(2025, 12, 31),
            priority=Priority.HIGH,
            source_quote="引用",
        )
        
        # 例外が発生しないことを確認
        Task_Validator.validate_task(task)
    
    def test_validate_task_invalid_due_date_format(self):
        """無効な日付形式で検証が失敗することを確認 (Requirement 3.4)"""
        task = Task(
            title="タスク",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        # 強制的に無効な日付形式を設定
        task.due_date = "2025-12-31"  # 文字列（date型ではない）
        
        with pytest.raises(TaskValidationError) as exc_info:
            Task_Validator.validate_task(task)
        
        assert "無効な日付形式です" in str(exc_info.value)
    
    def test_validate_task_list_all_valid(self):
        """すべて有効なタスクのリストを検証 (Requirement 3.5)"""
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
        
        valid_tasks = Task_Validator.validate_task_list(task_list)
        
        assert len(valid_tasks) == 2
        assert valid_tasks[0].title == "タスク1"
        assert valid_tasks[1].title == "タスク2"
    
    def test_validate_task_list_with_invalid_tasks(self):
        """無効なタスクを含むリストを検証 (Requirement 3.5)"""
        task1 = Task(
            title="有効なタスク",
            description="説明1",
            priority=Priority.HIGH,
            source_quote="引用1",
        )
        task2 = Task(
            title="一時的なタイトル",
            description="説明2",
            priority=Priority.LOW,
            source_quote="引用2",
        )
        task2.title = ""  # 無効（空のタイトル）に変更
        
        task3 = Task(
            title="もう一つの有効なタスク",
            description="説明3",
            priority=Priority.MEDIUM,
            source_quote="引用3",
        )
        
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task1, task2, task3],
        )
        
        valid_tasks = Task_Validator.validate_task_list(task_list)
        
        # 無効なタスクは除外され、有効なタスクのみが返される
        assert len(valid_tasks) == 2
        assert valid_tasks[0].title == "有効なタスク"
        assert valid_tasks[1].title == "もう一つの有効なタスク"
    
    def test_validate_and_filter_creates_new_task_list(self):
        """validate_and_filterが新しいTaskListを作成することを確認"""
        task1 = Task(
            title="有効なタスク",
            description="説明1",
            priority=Priority.HIGH,
            source_quote="引用1",
        )
        task2 = Task(
            title="一時的なタイトル",
            description="説明2",
            priority=Priority.LOW,
            source_quote="引用2",
        )
        task2.title = ""  # 無効に変更
        
        original_task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task1, task2],
            status=TaskListStatus.PENDING,
        )
        
        filtered_task_list = Task_Validator.validate_and_filter(original_task_list)
        
        # 新しいTaskListが作成される
        assert filtered_task_list.session_id == original_task_list.session_id
        assert filtered_task_list.minutes_id == original_task_list.minutes_id
        assert filtered_task_list.status == original_task_list.status
        
        # 有効なタスクのみが含まれる
        assert len(filtered_task_list.tasks) == 1
        assert filtered_task_list.tasks[0].title == "有効なタスク"
        
        # 元のTaskListは変更されない
        assert len(original_task_list.tasks) == 2
    
    def test_validate_empty_task_list(self):
        """空のタスクリストを検証"""
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[],
        )
        
        valid_tasks = Task_Validator.validate_task_list(task_list)
        
        assert len(valid_tasks) == 0
