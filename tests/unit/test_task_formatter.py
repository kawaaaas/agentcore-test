"""
タスクフォーマッターのユニットテスト

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from datetime import date

import pytest

from agents.tools.task_formatter import Task_Formatter
from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus


class TestTaskFormatter:
    """Task_Formatterのテスト"""
    
    def test_to_markdown_basic(self):
        """基本的なMarkdown変換をテスト (Requirements 4.1, 4.2, 4.3, 4.4)"""
        task1 = Task(
            title="高優先度タスク",
            description="これは高優先度のタスクです",
            assignee="山田太郎",
            due_date=date(2025, 12, 31),
            priority=Priority.HIGH,
            source_quote="議事録からの引用1",
        )
        task2 = Task(
            title="低優先度タスク",
            description="これは低優先度のタスクです",
            priority=Priority.LOW,
            source_quote="議事録からの引用2",
        )
        
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task1, task2],
        )
        
        markdown = Task_Formatter.to_markdown(task_list)
        
        # タイトルが含まれる
        assert "# タスクリスト" in markdown
        
        # メタデータが含まれる
        assert "**Session ID**: session-123" in markdown
        assert "**Minutes ID**: minutes-456" in markdown
        assert "**Status**: pending" in markdown
        
        # 優先度セクションが含まれる
        assert "## HIGH" in markdown
        assert "## LOW" in markdown
        
        # チェックボックス形式で出力される (Requirement 4.3)
        assert "- [ ] 高優先度タスク" in markdown
        assert "- [ ] 低優先度タスク" in markdown
        
        # 担当者と期限が表示される (Requirement 4.4)
        assert "担当: 山田太郎" in markdown
        assert "期限: 2025-12-31" in markdown
    
    def test_to_markdown_priority_sorting(self):
        """優先度でソートされることをテスト (Requirement 4.2)"""
        task_low = Task(
            title="低優先度",
            description="説明",
            priority=Priority.LOW,
            source_quote="引用",
        )
        task_high = Task(
            title="高優先度",
            description="説明",
            priority=Priority.HIGH,
            source_quote="引用",
        )
        task_medium = Task(
            title="中優先度",
            description="説明",
            priority=Priority.MEDIUM,
            source_quote="引用",
        )
        
        # 順不同でタスクを追加
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task_low, task_high, task_medium],
        )
        
        markdown = Task_Formatter.to_markdown(task_list)
        
        # HIGH → MEDIUM → LOWの順で出力される
        high_pos = markdown.find("## HIGH")
        medium_pos = markdown.find("## MEDIUM")
        low_pos = markdown.find("## LOW")
        
        assert high_pos < medium_pos < low_pos
    
    def test_to_markdown_empty_task_list(self):
        """空のタスクリストをMarkdownに変換"""
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[],
        )
        
        markdown = Task_Formatter.to_markdown(task_list)
        
        assert "タスクはありません。" in markdown
    
    def test_to_markdown_task_without_assignee_and_due_date(self):
        """担当者と期限がないタスクをMarkdownに変換"""
        task = Task(
            title="タスク",
            description="説明",
            assignee=None,
            due_date=None,
            priority=Priority.MEDIUM,
            source_quote="引用",
        )
        
        task_list = TaskList(
            session_id="session-123",
            minutes_id="minutes-456",
            tasks=[task],
        )
        
        markdown = Task_Formatter.to_markdown(task_list)
        
        # 担当者と期限の行が含まれない
        assert "担当:" not in markdown
        assert "期限:" not in markdown
    
    def test_from_markdown_basic(self):
        """基本的なMarkdownからの復元をテスト (Requirement 4.5)"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Minutes ID**: minutes-456
- **Status**: pending

## HIGH

- [ ] 高優先度タスク
  - 担当: 山田太郎, 期限: 2025-12-31
  - 説明: これは高優先度のタスクです
  - ID: task-id-1
  - 引用: 議事録からの引用1

## LOW

- [ ] 低優先度タスク
  - 説明: これは低優先度のタスクです
  - ID: task-id-2
  - 引用: 議事録からの引用2
"""
        
        task_list = Task_Formatter.from_markdown(markdown)
        
        assert task_list.session_id == "session-123"
        assert task_list.minutes_id == "minutes-456"
        assert task_list.status == TaskListStatus.PENDING
        assert len(task_list.tasks) == 2
        
        # 高優先度タスク
        high_task = task_list.tasks[0]
        assert high_task.title == "高優先度タスク"
        assert high_task.priority == Priority.HIGH
        assert high_task.assignee == "山田太郎"
        assert high_task.due_date == date(2025, 12, 31)
        assert high_task.description == "これは高優先度のタスクです"
        assert high_task.id == "task-id-1"
        assert high_task.source_quote == "議事録からの引用1"
        
        # 低優先度タスク
        low_task = task_list.tasks[1]
        assert low_task.title == "低優先度タスク"
        assert low_task.priority == Priority.LOW
        assert low_task.assignee is None
        assert low_task.due_date is None
    
    def test_from_markdown_missing_session_id(self):
        """Session IDがない場合にエラーを返す"""
        markdown = """# タスクリスト

- **Minutes ID**: minutes-456
- **Status**: pending
"""
        
        with pytest.raises(ValueError) as exc_info:
            Task_Formatter.from_markdown(markdown)
        
        assert "Session ID" in str(exc_info.value)
    
    def test_from_markdown_missing_minutes_id(self):
        """Minutes IDがない場合にエラーを返す"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Status**: pending
"""
        
        with pytest.raises(ValueError) as exc_info:
            Task_Formatter.from_markdown(markdown)
        
        assert "Minutes ID" in str(exc_info.value)
    
    def test_from_markdown_invalid_status(self):
        """無効なステータスの場合にエラーを返す"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Minutes ID**: minutes-456
- **Status**: invalid_status
"""
        
        with pytest.raises(ValueError) as exc_info:
            Task_Formatter.from_markdown(markdown)
        
        assert "無効なステータス" in str(exc_info.value)
    
    def test_roundtrip_conversion(self):
        """ラウンドトリップ変換をテスト (Requirement 4.5)"""
        task1 = Task(
            title="タスク1",
            description="説明1",
            assignee="担当者1",
            due_date=date(2025, 6, 15),
            priority=Priority.HIGH,
            source_quote="引用1",
        )
        task2 = Task(
            title="タスク2",
            description="説明2",
            priority=Priority.MEDIUM,
            source_quote="引用2",
        )
        task3 = Task(
            title="タスク3",
            description="説明3",
            assignee="担当者3",
            priority=Priority.LOW,
            source_quote="引用3",
        )
        
        original_task_list = TaskList(
            session_id="session-abc",
            minutes_id="minutes-xyz",
            tasks=[task1, task2, task3],
            status=TaskListStatus.APPROVED,
        )
        
        # TaskList → Markdown → TaskList
        markdown = Task_Formatter.to_markdown(original_task_list)
        restored_task_list = Task_Formatter.from_markdown(markdown)
        
        # メタデータが一致
        assert restored_task_list.session_id == original_task_list.session_id
        assert restored_task_list.minutes_id == original_task_list.minutes_id
        assert restored_task_list.status == original_task_list.status
        
        # タスク数が一致
        assert len(restored_task_list.tasks) == len(original_task_list.tasks)
        
        # 各タスクの内容が一致
        for original, restored in zip(original_task_list.tasks, restored_task_list.tasks):
            assert restored.title == original.title
            assert restored.description == original.description
            assert restored.assignee == original.assignee
            assert restored.due_date == original.due_date
            assert restored.priority == original.priority
            assert restored.source_quote == original.source_quote
            assert restored.id == original.id
    
    def test_from_markdown_task_with_only_assignee(self):
        """担当者のみが設定されたタスクを復元"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Minutes ID**: minutes-456
- **Status**: pending

## MEDIUM

- [ ] タスク
  - 担当: 担当者
  - 説明: 説明
  - ID: task-id
  - 引用: 引用
"""
        
        task_list = Task_Formatter.from_markdown(markdown)
        
        assert len(task_list.tasks) == 1
        task = task_list.tasks[0]
        assert task.assignee == "担当者"
        assert task.due_date is None
    
    def test_from_markdown_task_with_only_due_date(self):
        """期限のみが設定されたタスクを復元"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Minutes ID**: minutes-456
- **Status**: pending

## MEDIUM

- [ ] タスク
  - 期限: 2025-12-31
  - 説明: 説明
  - ID: task-id
  - 引用: 引用
"""
        
        task_list = Task_Formatter.from_markdown(markdown)
        
        assert len(task_list.tasks) == 1
        task = task_list.tasks[0]
        assert task.assignee is None
        assert task.due_date == date(2025, 12, 31)
    
    def test_from_markdown_empty_task_list(self):
        """空のタスクリストを復元"""
        markdown = """# タスクリスト

- **Session ID**: session-123
- **Minutes ID**: minutes-456
- **Status**: pending

タスクはありません。
"""
        
        task_list = Task_Formatter.from_markdown(markdown)
        
        assert task_list.session_id == "session-123"
        assert task_list.minutes_id == "minutes-456"
        assert len(task_list.tasks) == 0
