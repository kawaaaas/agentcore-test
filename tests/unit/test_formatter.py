"""
議事録フォーマッターのユニットテスト

MinutesFormatterクラスの基本機能をテストする。
"""

from datetime import datetime

import pytest

from agents.models.minutes import ActionItem, Minutes
from agents.tools.formatter import MinutesFormatter


class TestMinutesFormatter:
    """MinutesFormatterのテストクラス"""
    
    def test_to_markdown_basic(self):
        """基本的な議事録をMarkdownに変換できる"""
        minutes = Minutes(
            title="週次ミーティング",
            date=datetime(2025, 1, 15, 10, 0),
            participants=["田中", "佐藤"],
            agenda=["進捗確認", "課題共有"],
            discussion="プロジェクトの進捗について議論しました。",
            decisions=["次回は来週水曜日に開催"],
            action_items=[
                ActionItem(
                    description="資料作成",
                    assignee="田中",
                    due_date="2025-01-20",
                    completed=False,
                )
            ],
        )
        
        markdown = MinutesFormatter.to_markdown(minutes)
        
        # H1見出しが含まれる
        assert "# 週次ミーティング" in markdown
        # H2見出しが含まれる
        assert "## 日時" in markdown
        assert "## 参加者" in markdown
        assert "## 議題" in markdown
        assert "## 議論内容" in markdown
        assert "## 決定事項" in markdown
        assert "## アクションアイテム" in markdown
        # チェックボックス形式
        assert "- [ ] 資料作成" in markdown
        assert "担当: 田中" in markdown
        assert "期限: 2025-01-20" in markdown
    
    def test_to_markdown_empty_participants(self):
        """参加者が空の場合は「不明」を出力"""
        minutes = Minutes(
            title="テスト会議",
            date=datetime(2025, 1, 15, 10, 0),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[],
        )
        
        markdown = MinutesFormatter.to_markdown(minutes)
        
        assert "## 参加者\n不明" in markdown
    
    def test_to_markdown_completed_action(self):
        """完了したアクションアイテムは[x]で表示"""
        minutes = Minutes(
            title="テスト会議",
            date=datetime(2025, 1, 15, 10, 0),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[
                ActionItem(
                    description="完了タスク",
                    completed=True,
                )
            ],
        )
        
        markdown = MinutesFormatter.to_markdown(minutes)
        
        assert "- [x] 完了タスク" in markdown
    
    def test_from_markdown_basic(self):
        """Markdownから議事録オブジェクトを復元できる"""
        markdown = """# 週次ミーティング

## 日時
2025-01-15 10:00

## 参加者
- 田中
- 佐藤

## 議題
- 進捗確認
- 課題共有

## 議論内容
プロジェクトの進捗について議論しました。

## 決定事項
- 次回は来週水曜日に開催

## アクションアイテム
- [ ] 資料作成 (担当: 田中, 期限: 2025-01-20)
"""
        
        minutes = MinutesFormatter.from_markdown(markdown)
        
        assert minutes.title == "週次ミーティング"
        assert minutes.date == datetime(2025, 1, 15, 10, 0)
        assert minutes.participants == ["田中", "佐藤"]
        assert minutes.agenda == ["進捗確認", "課題共有"]
        assert "プロジェクトの進捗について議論しました。" in minutes.discussion
        assert minutes.decisions == ["次回は来週水曜日に開催"]
        assert len(minutes.action_items) == 1
        assert minutes.action_items[0].description == "資料作成"
        assert minutes.action_items[0].assignee == "田中"
        assert minutes.action_items[0].due_date == "2025-01-20"
        assert minutes.action_items[0].completed is False
    
    def test_from_markdown_empty_participants(self):
        """参加者が「不明」の場合は空リストに変換"""
        markdown = """# テスト会議

## 日時
2025-01-15 10:00

## 参加者
不明

## 議題
なし

## 議論内容
テスト

## 決定事項
なし

## アクションアイテム
なし
"""
        
        minutes = MinutesFormatter.from_markdown(markdown)
        
        assert minutes.participants == []
        assert minutes.agenda == []
        assert minutes.decisions == []
        assert minutes.action_items == []
    
    def test_generate_filename_basic(self):
        """基本的なファイル名を生成できる"""
        minutes = Minutes(
            title="週次ミーティング",
            date=datetime(2025, 1, 15, 10, 0),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[],
        )
        
        filename = MinutesFormatter.generate_filename(minutes)
        
        assert filename == "2025-01-15_週次ミーティング.md"
    
    def test_generate_filename_with_special_chars(self):
        """特殊文字を含むタイトルからファイル名を生成"""
        minutes = Minutes(
            title="Q1 レビュー会議 (2025)",
            date=datetime(2025, 1, 15, 10, 0),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[],
        )
        
        filename = MinutesFormatter.generate_filename(minutes)
        
        # 特殊文字が削除され、スペースがハイフンに変換される
        assert filename == "2025-01-15_q1-レビュー会議-2025.md"
    
    def test_generate_filename_empty_title(self):
        """空のタイトルの場合はデフォルト値を使用"""
        minutes = Minutes(
            title="!!!",
            date=datetime(2025, 1, 15, 10, 0),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[],
        )
        
        filename = MinutesFormatter.generate_filename(minutes)
        
        assert filename == "2025-01-15_untitled.md"
    
    def test_roundtrip_conversion(self):
        """Markdown変換のラウンドトリップが正しく動作する"""
        original = Minutes(
            title="テスト会議",
            date=datetime(2025, 1, 15, 10, 0),
            participants=["田中", "佐藤"],
            agenda=["議題1", "議題2"],
            discussion="議論内容です。",
            decisions=["決定1", "決定2"],
            action_items=[
                ActionItem(
                    description="タスク1",
                    assignee="田中",
                    due_date="2025-01-20",
                    completed=False,
                ),
                ActionItem(
                    description="タスク2",
                    completed=True,
                ),
            ],
        )
        
        # to_markdown -> from_markdown
        markdown = MinutesFormatter.to_markdown(original)
        restored = MinutesFormatter.from_markdown(markdown)
        
        # 主要なフィールドが一致する
        assert restored.title == original.title
        assert restored.date == original.date
        assert restored.participants == original.participants
        assert restored.agenda == original.agenda
        assert restored.discussion == original.discussion
        assert restored.decisions == original.decisions
        assert len(restored.action_items) == len(original.action_items)
        
        for i, action in enumerate(restored.action_items):
            assert action.description == original.action_items[i].description
            assert action.assignee == original.action_items[i].assignee
            assert action.due_date == original.action_items[i].due_date
            assert action.completed == original.action_items[i].completed

