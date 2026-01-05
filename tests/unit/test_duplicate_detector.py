"""
重複タスク検出のユニットテスト

DuplicateDetectorの基本機能を検証する。
"""

import pytest
from datetime import date

from agents.tools.duplicate_detector import DuplicateDetector
from agents.tools.task_models import Task, Priority


class TestDuplicateDetector:
    """DuplicateDetectorのテストクラス"""
    
    def test_calculate_similarity_identical(self):
        """完全に一致するタイトルの類似度は1.0"""
        similarity = DuplicateDetector.calculate_similarity(
            "データベース設計を完了する",
            "データベース設計を完了する"
        )
        assert similarity == 1.0
    
    def test_calculate_similarity_case_insensitive(self):
        """大文字小文字を無視して類似度を計算"""
        similarity = DuplicateDetector.calculate_similarity(
            "Database Design",
            "database design"
        )
        assert similarity == 1.0
    
    def test_calculate_similarity_whitespace(self):
        """前後の空白を無視して類似度を計算"""
        similarity = DuplicateDetector.calculate_similarity(
            "  タスク完了  ",
            "タスク完了"
        )
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self):
        """完全に異なるタイトルの類似度は低い"""
        similarity = DuplicateDetector.calculate_similarity(
            "データベース設計",
            "フロントエンド実装"
        )
        assert similarity < 0.5
    
    def test_calculate_similarity_similar(self):
        """類似したタイトルの類似度は高い"""
        similarity = DuplicateDetector.calculate_similarity(
            "データベース設計を完了する",
            "データベース設計を完了"
        )
        assert similarity > 0.8
    
    def test_calculate_similarity_empty(self):
        """空文字列の類似度は0.0"""
        assert DuplicateDetector.calculate_similarity("", "test") == 0.0
        assert DuplicateDetector.calculate_similarity("test", "") == 0.0
        assert DuplicateDetector.calculate_similarity("", "") == 0.0
    
    def test_detect_duplicates_no_duplicates(self):
        """重複がない場合は空リストを返す"""
        tasks = [
            Task(
                title="タスク1",
                description="説明1",
                priority=Priority.HIGH,
                source_quote="引用1"
            ),
            Task(
                title="タスク2",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2"
            ),
        ]
        
        duplicates = DuplicateDetector.detect_duplicates(tasks)
        assert duplicates == []
    
    def test_detect_duplicates_with_duplicates(self):
        """重複がある場合はペアを返す"""
        tasks = [
            Task(
                title="データベース設計を完了する",
                description="説明1",
                priority=Priority.HIGH,
                source_quote="引用1"
            ),
            Task(
                title="データベース設計を完了",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2"
            ),
        ]
        
        duplicates = DuplicateDetector.detect_duplicates(tasks)
        assert len(duplicates) == 1
        assert duplicates[0] == (0, 1)
    
    def test_merge_duplicates_no_duplicates(self):
        """重複がない場合は元のリストを返す"""
        tasks = [
            Task(
                title="タスク1",
                description="説明1",
                priority=Priority.HIGH,
                source_quote="引用1"
            ),
            Task(
                title="タスク2",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2"
            ),
        ]
        
        result = DuplicateDetector.merge_duplicates(tasks)
        assert len(result) == 2
        assert result[0].title == "タスク1"
        assert result[1].title == "タスク2"
    
    def test_merge_duplicates_with_duplicates(self):
        """重複がある場合は統合する"""
        tasks = [
            Task(
                title="データベース設計を完了する",
                description="短い説明",
                priority=Priority.MEDIUM,
                source_quote="引用1"
            ),
            Task(
                title="データベース設計を完了",
                description="より詳細な説明でデータベーススキーマを設計する",
                priority=Priority.HIGH,
                source_quote="引用2"
            ),
        ]
        
        result = DuplicateDetector.merge_duplicates(tasks)
        assert len(result) == 1
        # より詳細な説明を持つタスクが優先される
        assert "より詳細な説明" in result[0].description
        # 最も高い優先度が選ばれる
        assert result[0].priority == Priority.HIGH
    
    def test_merge_duplicates_preserves_assignee(self):
        """担当者が設定されているタスクを優先"""
        tasks = [
            Task(
                title="データベース設計を完了する",
                description="説明1",
                priority=Priority.MEDIUM,
                source_quote="引用1",
                assignee=None
            ),
            Task(
                title="データベース設計を完了",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2",
                assignee="田中"
            ),
        ]
        
        result = DuplicateDetector.merge_duplicates(tasks)
        assert len(result) == 1
        assert result[0].assignee == "田中"
    
    def test_merge_duplicates_earliest_due_date(self):
        """最も早い期限を優先"""
        tasks = [
            Task(
                title="データベース設計を完了する",
                description="説明1",
                priority=Priority.MEDIUM,
                source_quote="引用1",
                due_date=date(2025, 2, 1)
            ),
            Task(
                title="データベース設計を完了",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2",
                due_date=date(2025, 1, 15)
            ),
        ]
        
        result = DuplicateDetector.merge_duplicates(tasks)
        assert len(result) == 1
        assert result[0].due_date == date(2025, 1, 15)
    
    def test_merge_duplicates_combines_source_quotes(self):
        """source_quoteを結合"""
        tasks = [
            Task(
                title="データベース設計を完了する",
                description="説明1",
                priority=Priority.MEDIUM,
                source_quote="引用1"
            ),
            Task(
                title="データベース設計を完了",
                description="説明2",
                priority=Priority.MEDIUM,
                source_quote="引用2"
            ),
        ]
        
        result = DuplicateDetector.merge_duplicates(tasks)
        assert len(result) == 1
        assert "引用1" in result[0].source_quote
        assert "引用2" in result[0].source_quote
        assert "---" in result[0].source_quote
    
    def test_merge_duplicates_empty_list(self):
        """空リストの場合は空リストを返す"""
        result = DuplicateDetector.merge_duplicates([])
        assert result == []
