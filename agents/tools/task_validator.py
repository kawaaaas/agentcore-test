"""
タスク検証ツール

タスクの妥当性を検証する。
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

from datetime import date
from typing import List

from agents.tools.task_models import Priority, Task, TaskList


class TaskValidationError(Exception):
    """タスク検証エラーを表す例外クラス"""
    pass


class Task_Validator:
    """
    タスク検証クラス
    
    抽出されたタスクの妥当性を検証する。
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    MAX_TITLE_LENGTH = 100
    
    @staticmethod
    def validate_task(task: Task) -> None:
        """
        単一タスクを検証する
        
        Args:
            task: 検証対象のタスク
            
        Raises:
            TaskValidationError: タスクが無効な場合
        """
        # 3.1: タイトルが空でないことを検証
        if not task.title or not task.title.strip():
            raise TaskValidationError("タイトルが空です")
        
        # 3.2: タイトルが100文字以内であることを検証
        if len(task.title) > Task_Validator.MAX_TITLE_LENGTH:
            raise TaskValidationError(
                f"タイトルが{Task_Validator.MAX_TITLE_LENGTH}文字を超えています: "
                f"{len(task.title)}文字"
            )
        
        # 3.3: 優先度が有効な値であることを検証
        if task.priority not in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            raise TaskValidationError(
                f"無効な優先度です: {task.priority}. "
                f"有効な値: {[p.value for p in Priority]}"
            )
        
        # 3.4: 期限が設定されている場合、日付形式が有効であることを検証
        if task.due_date is not None:
            if not isinstance(task.due_date, date):
                raise TaskValidationError(
                    f"無効な日付形式です: {task.due_date}. "
                    f"date型である必要があります"
                )
    
    @staticmethod
    def validate_task_list(task_list: TaskList) -> List[Task]:
        """
        タスクリストを検証し、有効なタスクのみを返す
        
        Args:
            task_list: 検証対象のタスクリスト
            
        Returns:
            List[Task]: 検証に合格したタスクのリスト
            
        Note:
            Requirements 3.5: 検証に合格したタスクのみがリストに含まれる
        """
        valid_tasks = []
        
        for task in task_list.tasks:
            try:
                Task_Validator.validate_task(task)
                valid_tasks.append(task)
            except TaskValidationError:
                # 検証に失敗したタスクはスキップ
                continue
        
        return valid_tasks
    
    @staticmethod
    def validate_and_filter(task_list: TaskList) -> TaskList:
        """
        タスクリストを検証し、無効なタスクを除外した新しいTaskListを返す
        
        Args:
            task_list: 検証対象のタスクリスト
            
        Returns:
            TaskList: 有効なタスクのみを含む新しいTaskList
        """
        valid_tasks = Task_Validator.validate_task_list(task_list)
        
        # 新しいTaskListを作成（有効なタスクのみ）
        return TaskList(
            session_id=task_list.session_id,
            minutes_id=task_list.minutes_id,
            tasks=valid_tasks,
            status=task_list.status,
            created_at=task_list.created_at,
            updated_at=task_list.updated_at,
        )
