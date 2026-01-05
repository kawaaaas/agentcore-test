"""
タスクフォーマッター

タスクをMarkdown形式に変換、またはMarkdownから復元する機能を提供する。
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import re
from datetime import date
from typing import List

from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus


class Task_Formatter:
    """
    タスクフォーマッター
    
    タスクとMarkdown形式の相互変換を行う。
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    # 優先度の順序定義（ソート用）
    PRIORITY_ORDER = {
        Priority.HIGH: 0,
        Priority.MEDIUM: 1,
        Priority.LOW: 2,
    }
    
    @staticmethod
    def to_markdown(task_list: TaskList) -> str:
        """
        タスクリストをMarkdown形式に変換する
        
        Requirements: 4.1, 4.2, 4.3, 4.4
        
        Args:
            task_list: タスクリストオブジェクト
            
        Returns:
            Markdown形式の文字列
        """
        lines = []
        
        # タイトル
        lines.append("# タスクリスト")
        lines.append("")
        
        # メタデータ
        lines.append(f"- **Session ID**: {task_list.session_id}")
        lines.append(f"- **Minutes ID**: {task_list.minutes_id}")
        lines.append(f"- **Status**: {task_list.status.value}")
        lines.append("")
        
        # タスクが空の場合
        if not task_list.tasks:
            lines.append("タスクはありません。")
            return "\n".join(lines)
        
        # Requirement 4.2: 優先度でソート（high → medium → low）
        sorted_tasks = sorted(
            task_list.tasks,
            key=lambda t: Task_Formatter.PRIORITY_ORDER[t.priority]
        )
        
        # 優先度ごとにグループ化して出力
        current_priority = None
        for task in sorted_tasks:
            # 優先度が変わったら見出しを追加
            if task.priority != current_priority:
                current_priority = task.priority
                lines.append(f"## {current_priority.value.upper()}")
                lines.append("")
            
            # Requirement 4.3: チェックボックス形式で出力
            lines.append(f"- [ ] {task.title}")
            
            # Requirement 4.4: 担当者と期限を表示
            details = []
            if task.assignee:
                details.append(f"担当: {task.assignee}")
            if task.due_date:
                details.append(f"期限: {task.due_date.strftime('%Y-%m-%d')}")
            
            if details:
                lines.append(f"  - {', '.join(details)}")
            
            # 説明を追加
            lines.append(f"  - 説明: {task.description}")
            
            # タスクIDを追加（復元時に必要）
            lines.append(f"  - ID: {task.id}")
            
            # 元の議事録の引用を追加
            lines.append(f"  - 引用: {task.source_quote}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def from_markdown(markdown: str) -> TaskList:
        """
        Markdown形式の文字列からタスクリストオブジェクトを復元する
        
        Requirements: 4.5
        
        Args:
            markdown: Markdown形式のタスクリスト文字列
            
        Returns:
            タスクリストオブジェクト
            
        Raises:
            ValueError: パースに失敗した場合
        """
        lines = markdown.strip().split("\n")
        
        # メタデータを抽出
        session_id_match = re.search(r"\*\*Session ID\*\*:\s*(.+)", markdown)
        if not session_id_match:
            raise ValueError("Session IDが見つかりません")
        session_id = session_id_match.group(1).strip()
        
        minutes_id_match = re.search(r"\*\*Minutes ID\*\*:\s*(.+)", markdown)
        if not minutes_id_match:
            raise ValueError("Minutes IDが見つかりません")
        minutes_id = minutes_id_match.group(1).strip()
        
        status_match = re.search(r"\*\*Status\*\*:\s*(.+)", markdown)
        if not status_match:
            raise ValueError("Statusが見つかりません")
        status_str = status_match.group(1).strip()
        
        # ステータスを変換
        try:
            status = TaskListStatus(status_str)
        except ValueError:
            raise ValueError(f"無効なステータス: {status_str}")
        
        # タスクを抽出
        tasks: List[Task] = []
        
        # タスクのパターン: - [ ] タイトル
        task_pattern = r"^- \[ \] (.+)$"
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # タスクの開始を検出
            task_match = re.match(task_pattern, line)
            if task_match:
                title = task_match.group(1).strip()
                
                # タスクの詳細を抽出（次の行から）
                assignee = None
                due_date = None
                description = None
                task_id = None
                source_quote = None
                priority = Priority.MEDIUM  # デフォルト
                
                # 現在の優先度セクションを判定（直前のH2見出しから）
                for j in range(i - 1, -1, -1):
                    prev_line = lines[j].strip()
                    if prev_line.startswith("## "):
                        priority_str = prev_line[3:].strip().lower()
                        if priority_str == "high":
                            priority = Priority.HIGH
                        elif priority_str == "medium":
                            priority = Priority.MEDIUM
                        elif priority_str == "low":
                            priority = Priority.LOW
                        break
                
                # 詳細行を読み込む
                i += 1
                while i < len(lines):
                    detail_line = lines[i].strip()
                    
                    # 次のタスクまたはセクションに到達したら終了
                    if detail_line.startswith("- [ ]") or detail_line.startswith("## "):
                        i -= 1  # 1つ戻る
                        break
                    
                    # 詳細項目を抽出
                    if detail_line.startswith("- "):
                        detail_content = detail_line[2:].strip()
                        
                        # 担当者と期限を抽出
                        if "担当:" in detail_content and "期限:" in detail_content:
                            assignee_match = re.search(r"担当:\s*([^,]+)", detail_content)
                            if assignee_match:
                                assignee = assignee_match.group(1).strip()
                            
                            due_date_match = re.search(r"期限:\s*(\d{4}-\d{2}-\d{2})", detail_content)
                            if due_date_match:
                                due_date_str = due_date_match.group(1).strip()
                                try:
                                    due_date = date.fromisoformat(due_date_str)
                                except ValueError:
                                    pass  # 無効な日付はスキップ
                        elif "担当:" in detail_content:
                            assignee_match = re.search(r"担当:\s*(.+)", detail_content)
                            if assignee_match:
                                assignee = assignee_match.group(1).strip()
                        elif "期限:" in detail_content:
                            due_date_match = re.search(r"期限:\s*(\d{4}-\d{2}-\d{2})", detail_content)
                            if due_date_match:
                                due_date_str = due_date_match.group(1).strip()
                                try:
                                    due_date = date.fromisoformat(due_date_str)
                                except ValueError:
                                    pass
                        elif detail_content.startswith("説明:"):
                            description = detail_content[3:].strip()
                        elif detail_content.startswith("ID:"):
                            task_id = detail_content[3:].strip()
                        elif detail_content.startswith("引用:"):
                            source_quote = detail_content[3:].strip()
                    
                    i += 1
                
                # タスクを作成（必須フィールドが揃っている場合のみ）
                if description and source_quote:
                    task = Task(
                        id=task_id if task_id else None,  # Noneの場合は自動生成される
                        title=title,
                        description=description,
                        assignee=assignee,
                        due_date=due_date,
                        priority=priority,
                        source_quote=source_quote,
                    )
                    tasks.append(task)
            
            i += 1
        
        return TaskList(
            session_id=session_id,
            minutes_id=minutes_id,
            tasks=tasks,
            status=status,
        )
