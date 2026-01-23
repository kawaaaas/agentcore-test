"""
Issue Formatter

GitHub Issueの本文フォーマットとパース機能を提供する。
Requirements: 2.4, 9.1, 9.2, 9.3
"""

import re
from typing import Optional

from agents.models.github_models import Priority, Task


class Issue_Formatter:
    """
    Issue本文のフォーマットとパース
    
    タスクからGitHub Issue本文を生成し、逆にIssue本文から
    タスク情報を復元する機能を提供する。
    Requirements: 2.4, 9.1, 9.2, 9.3
    """
    
    # Issue本文のテンプレート
    TEMPLATE = """## 概要

{description}

## 詳細

{description}

## 関連議事録

{source_minutes_url}

## 期限

{due_date}

## 優先度

{priority}
"""
    
    # パース用の正規表現パターン
    SECTION_PATTERN = re.compile(
        r"## 概要\s*\n\n(.*?)\n\n## 詳細\s*\n\n(.*?)\n\n## 関連議事録\s*\n\n(.*?)\n\n## 期限\s*\n\n(.*?)\n\n## 優先度\s*\n\n(.*?)$",
        re.DOTALL
    )
    
    @staticmethod
    def format_issue_body(task: Task) -> str:
        """
        タスクからIssue本文を生成
        
        Taskオブジェクトを受け取り、Issue_Templateに従って
        Markdown形式のIssue本文を生成する。
        
        Args:
            task: タスク情報
            
        Returns:
            フォーマットされたIssue本文（Markdown形式）
            
        Requirements: 2.4, 9.1, 9.2
        """
        # 期限の表示（未定の場合は「未定」と表示）
        due_date_display = task.due_date if task.due_date else "未定"
        
        # 優先度の表示
        priority_display = task.priority.value
        
        # テンプレートに値を埋め込む
        body = Issue_Formatter.TEMPLATE.format(
            description=task.description,
            source_minutes_url=task.source_minutes_url,
            due_date=due_date_display,
            priority=priority_display,
        )
        
        return body.strip()
    
    @staticmethod
    def parse_issue_body(body: str) -> dict:
        """
        Issue本文からタスク情報を復元
        
        Issue本文をパースして、元のタスク情報を抽出する。
        format_issue_body()で生成された本文から情報を復元できる。
        
        Args:
            body: Issue本文（Markdown形式）
            
        Returns:
            タスク情報を含む辞書
            - description: タスクの説明
            - source_minutes_url: 元の議事録URL
            - due_date: 期限（「未定」の場合はNone）
            - priority: 優先度
            
        Raises:
            ValueError: 本文のフォーマットが不正な場合
            
        Requirements: 9.3, 9.4
        """
        # 正規表現でセクションを抽出
        match = Issue_Formatter.SECTION_PATTERN.search(body)
        
        if not match:
            raise ValueError("Issue本文のフォーマットが不正です")
        
        # 各セクションを取得
        overview = match.group(1).strip()
        description = match.group(2).strip()
        source_minutes_url = match.group(3).strip()
        due_date_str = match.group(4).strip()
        priority_str = match.group(5).strip()
        
        # 期限の処理（「未定」の場合はNone）
        due_date = None if due_date_str == "未定" else due_date_str
        
        # 優先度の変換
        try:
            priority = Priority(priority_str)
        except ValueError:
            raise ValueError(f"不正な優先度: {priority_str}")
        
        return {
            "description": description,
            "source_minutes_url": source_minutes_url,
            "due_date": due_date,
            "priority": priority,
        }
    
    @staticmethod
    def create_preview(task: Task) -> str:
        """
        Slack用プレビューテキスト生成
        
        タスク情報から、Slackで表示するための
        簡潔なプレビューテキストを生成する。
        
        Args:
            task: タスク情報
            
        Returns:
            プレビューテキスト
            
        Requirements: 6.2
        """
        # 担当者の表示
        assignee_display = task.assignee if task.assignee else "未定"
        
        # 期限の表示
        due_date_display = task.due_date if task.due_date else "未定"
        
        # プレビューテキストの生成
        preview = f"""*{task.title}*

{task.description}

• 担当者: {assignee_display}
• 期限: {due_date_display}
• 優先度: {task.priority.value}
"""
        
        return preview.strip()
