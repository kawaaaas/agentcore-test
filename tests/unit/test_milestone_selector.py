"""
Milestone Selector のユニットテスト

Requirements: 5.1, 5.2, 5.3
"""

import pytest

from agents.tools.milestone_selector import Milestone, Milestone_Selector


class TestMilestoneSelector:
    """Milestone_Selector のテストクラス"""
    
    def setup_method(self):
        """各テストの前に実行される初期化処理"""
        self.selector = Milestone_Selector()
    
    def test_select_milestone_with_valid_due_date(self):
        """有効な期限で最も近いマイルストーンを選択"""
        # Arrange
        due_date = "2025-02-15"
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
            Milestone(number=3, title="v3.0", due_on="2025-04-30T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result == 1  # v1.0が最も近い
    
    def test_select_milestone_with_undefined_due_date(self):
        """期限が「未定」の場合はNoneを返す"""
        # Arrange
        due_date = "未定"
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result is None
    
    def test_select_milestone_with_none_due_date(self):
        """期限がNoneの場合はNoneを返す"""
        # Arrange
        due_date = None
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result is None
    
    def test_select_milestone_with_empty_milestones(self):
        """マイルストーンリストが空の場合はNoneを返す"""
        # Arrange
        due_date = "2025-02-15"
        milestones = []
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result is None
    
    def test_select_milestone_with_no_suitable_milestone(self):
        """適切なマイルストーンが存在しない場合はNoneを返す"""
        # Arrange
        due_date = "2025-05-15"  # すべてのマイルストーンより後
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result is None
    
    def test_select_milestone_with_exact_match(self):
        """期限と完全に一致するマイルストーンを選択"""
        # Arrange
        due_date = "2025-02-28"
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result == 1
    
    def test_select_milestone_with_multiple_valid_milestones(self):
        """複数の有効なマイルストーンから最も近いものを選択"""
        # Arrange
        due_date = "2025-01-15"
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
            Milestone(number=3, title="v3.0", due_on="2025-04-30T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result == 1  # v1.0が最も近い
    
    def test_select_milestone_with_milestone_without_due_date(self):
        """期限のないマイルストーンは無視される"""
        # Arrange
        due_date = "2025-02-15"
        milestones = [
            Milestone(number=1, title="v1.0", due_on=None),  # 期限なし
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
        ]
        
        # Act
        result = self.selector.select_milestone(due_date, milestones)
        
        # Assert
        assert result == 2  # 期限のあるv2.0が選択される
    
    def test_parse_date_with_various_formats(self):
        """様々な日付フォーマットをパース"""
        # Arrange
        date_formats = [
            "2025-01-31",
            "2025-01-31T23:59:59",
            "2025-01-31T23:59:59Z",
            "2025-01-31T23:59:59.000Z",
        ]
        
        # Act & Assert
        for date_str in date_formats:
            result = self.selector._parse_date(date_str)
            assert result is not None
            assert result.year == 2025
            assert result.month == 1
            assert result.day == 31
    
    def test_parse_date_with_invalid_format(self):
        """無効な日付フォーマットの場合はNoneを返す"""
        # Arrange
        invalid_date = "invalid-date"
        
        # Act
        result = self.selector._parse_date(invalid_date)
        
        # Assert
        assert result is None
