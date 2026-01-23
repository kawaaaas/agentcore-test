"""
Issue Formatterのユニットテスト

Issue_Formatterクラスの各メソッドをテストする。
"""

import pytest

from agents.models.github_models import Priority, Task
from agents.tools.issue_formatter import Issue_Formatter


class TestIssueFormatter:
    """Issue_Formatterのテストクラス"""
    
    def test_format_issue_body_with_all_fields(self):
        """全フィールドが設定されたタスクのフォーマット"""
        task = Task(
            title="テストタスク",
            description="これはテストタスクです",
            assignee="山田太郎",
            due_date="2025-01-31",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/123",
        )
        
        body = Issue_Formatter.format_issue_body(task)
        
        # 各セクションが含まれていることを確認
        assert "## 概要" in body
        assert "## 詳細" in body
        assert "## 関連議事録" in body
        assert "## 期限" in body
        assert "## 優先度" in body
        
        # 値が含まれていることを確認
        assert "これはテストタスクです" in body
        assert "https://example.com/minutes/123" in body
        assert "2025-01-31" in body
        assert "high" in body
    
    def test_format_issue_body_with_no_due_date(self):
        """期限が未定のタスクのフォーマット"""
        task = Task(
            title="テストタスク",
            description="期限未定のタスク",
            assignee="山田太郎",
            due_date=None,
            priority=Priority.MEDIUM,
            source_minutes_url="https://example.com/minutes/456",
        )
        
        body = Issue_Formatter.format_issue_body(task)
        
        # 「未定」が表示されることを確認
        assert "未定" in body
    
    def test_parse_issue_body_success(self):
        """正常なIssue本文のパース"""
        body = """## 概要

テスト説明

## 詳細

テスト説明

## 関連議事録

https://example.com/minutes/789

## 期限

2025-02-15

## 優先度

low"""
        
        result = Issue_Formatter.parse_issue_body(body)
        
        assert result["description"] == "テスト説明"
        assert result["source_minutes_url"] == "https://example.com/minutes/789"
        assert result["due_date"] == "2025-02-15"
        assert result["priority"] == Priority.LOW
    
    def test_parse_issue_body_with_no_due_date(self):
        """期限が「未定」のIssue本文のパース"""
        body = """## 概要

テスト説明

## 詳細

テスト説明

## 関連議事録

https://example.com/minutes/999

## 期限

未定

## 優先度

medium"""
        
        result = Issue_Formatter.parse_issue_body(body)
        
        assert result["due_date"] is None
        assert result["priority"] == Priority.MEDIUM
    
    def test_parse_issue_body_invalid_format(self):
        """不正なフォーマットのIssue本文のパース"""
        body = "これは不正なフォーマットです"
        
        with pytest.raises(ValueError, match="Issue本文のフォーマットが不正です"):
            Issue_Formatter.parse_issue_body(body)
    
    def test_parse_issue_body_invalid_priority(self):
        """不正な優先度を含むIssue本文のパース"""
        body = """## 概要

テスト説明

## 詳細

テスト説明

## 関連議事録

https://example.com/minutes/999

## 期限

未定

## 優先度

invalid"""
        
        with pytest.raises(ValueError, match="不正な優先度"):
            Issue_Formatter.parse_issue_body(body)
    
    def test_create_preview_with_all_fields(self):
        """全フィールドが設定されたタスクのプレビュー生成"""
        task = Task(
            title="プレビューテスト",
            description="プレビュー用の説明",
            assignee="佐藤花子",
            due_date="2025-03-01",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/111",
        )
        
        preview = Issue_Formatter.create_preview(task)
        
        # タイトルが太字で含まれることを確認
        assert "*プレビューテスト*" in preview
        assert "プレビュー用の説明" in preview
        assert "担当者: 佐藤花子" in preview
        assert "期限: 2025-03-01" in preview
        assert "優先度: high" in preview
    
    def test_create_preview_with_no_assignee(self):
        """担当者が未定のタスクのプレビュー生成"""
        task = Task(
            title="担当者未定タスク",
            description="担当者が決まっていません",
            assignee=None,
            due_date="2025-04-01",
            priority=Priority.LOW,
            source_minutes_url="https://example.com/minutes/222",
        )
        
        preview = Issue_Formatter.create_preview(task)
        
        assert "担当者: 未定" in preview
    
    def test_roundtrip_format_and_parse(self):
        """フォーマットとパースのラウンドトリップ"""
        original_task = Task(
            title="ラウンドトリップテスト",
            description="ラウンドトリップ用の説明",
            assignee="田中一郎",
            due_date="2025-05-01",
            priority=Priority.MEDIUM,
            source_minutes_url="https://example.com/minutes/333",
        )
        
        # フォーマット
        body = Issue_Formatter.format_issue_body(original_task)
        
        # パース
        parsed_data = Issue_Formatter.parse_issue_body(body)
        
        # 元のタスクと同じ情報が復元されることを確認
        assert parsed_data["description"] == original_task.description
        assert parsed_data["source_minutes_url"] == original_task.source_minutes_url
        assert parsed_data["due_date"] == original_task.due_date
        assert parsed_data["priority"] == original_task.priority
