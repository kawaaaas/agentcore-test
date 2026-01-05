"""
タスク抽出のユニットテスト

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from agents.tools.extract_tasks import Task_Extractor
from agents.tools.task_models import Priority, TaskListStatus


class TestTaskExtractor:
    """Task_Extractorのテスト"""
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_with_valid_minutes(self, mock_boto_client):
        """有効な議事録からタスクを抽出できることを確認 (Requirement 1.1, 1.2)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        # Bedrockのレスポンスをモック
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps([
                                {
                                    "title": "APIの実装",
                                    "description": "ユーザー認証APIを実装する",
                                    "assignee": "田中",
                                    "due_date": "2025-01-15",
                                    "priority": "high",
                                    "source_quote": "田中さんは来週までにユーザー認証APIを実装してください"
                                },
                                {
                                    "title": "ドキュメント作成",
                                    "description": "API仕様書を作成する",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "medium",
                                    "source_quote": "API仕様書を作成する必要があります"
                                }
                            ])
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = """
        # 会議議事録
        
        ## アクションアイテム
        - 田中さんは来週までにユーザー認証APIを実装してください
        - API仕様書を作成する必要があります
        """
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert task_list.session_id == "session-123"
        assert task_list.minutes_id == "minutes-456"
        assert task_list.status == TaskListStatus.PENDING
        assert len(task_list.tasks) == 2
        
        # 最初のタスク
        task1 = task_list.tasks[0]
        assert task1.title == "APIの実装"
        assert task1.description == "ユーザー認証APIを実装する"
        assert task1.assignee == "田中"
        assert task1.due_date == date(2025, 1, 15)
        assert task1.priority == Priority.HIGH
        
        # 2番目のタスク
        task2 = task_list.tasks[1]
        assert task2.title == "ドキュメント作成"
        assert task2.assignee is None
        assert task2.due_date is None
        assert task2.priority == Priority.MEDIUM
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_with_empty_minutes(self, mock_boto_client):
        """空の議事録から空のタスクリストを返すことを確認 (Requirement 1.5)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        minutes_text = ""
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert len(task_list.tasks) == 0
        assert task_list.status == TaskListStatus.PENDING
        
        # Bedrockが呼ばれないことを確認
        mock_bedrock.converse.assert_not_called()
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_with_short_minutes(self, mock_boto_client):
        """短すぎる議事録から空のタスクリストを返すことを確認 (Requirement 1.5)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        minutes_text = "短い"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert len(task_list.tasks) == 0
        
        # Bedrockが呼ばれないことを確認
        mock_bedrock.converse.assert_not_called()
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_with_no_tasks_in_response(self, mock_boto_client):
        """タスクが含まれない議事録から空のタスクリストを返すことを確認 (Requirement 1.5)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        # Bedrockが空の配列を返す
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": "[]"
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = "これは単なる情報共有の会議でした。特にアクションアイテムはありません。"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert len(task_list.tasks) == 0
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_with_duplicate_detection(self, mock_boto_client):
        """重複タスクが統合されることを確認 (Requirement 6.1, 6.2)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        # 類似したタスクを含むレスポンス
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps([
                                {
                                    "title": "APIを実装する",
                                    "description": "短い説明",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "medium",
                                    "source_quote": "引用1"
                                },
                                {
                                    "title": "APIを実装する",
                                    "description": "より詳細な説明でこちらの方が情報が多い",
                                    "assignee": "田中",
                                    "due_date": "2025-01-15",
                                    "priority": "high",
                                    "source_quote": "引用2"
                                }
                            ])
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = "APIを実装する必要があります。"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        # 重複が統合されて1つになる
        assert len(task_list.tasks) == 1
        
        # より詳細な説明を持つタスクが優先される
        task = task_list.tasks[0]
        assert "より詳細な説明" in task.description
        assert task.assignee == "田中"
        assert task.priority == Priority.HIGH
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_truncates_long_titles(self, mock_boto_client):
        """長すぎるタイトルが100文字に切り詰められることを確認 (Requirement 2.2)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        # 長いタイトルを含むレスポンス
        long_title = "あ" * 150  # 150文字
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps([
                                {
                                    "title": long_title,
                                    "description": "説明",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "medium",
                                    "source_quote": "引用"
                                }
                            ])
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = "タスクを抽出してください"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        # タイトルが100文字に切り詰められる
        assert len(task_list.tasks) == 1
        assert len(task_list.tasks[0].title) == 100
        assert task_list.tasks[0].title == "あ" * 100
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_handles_json_in_code_block(self, mock_boto_client):
        """マークダウンコードブロック内のJSONを正しくパースできることを確認"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        # マークダウンコードブロックで囲まれたJSON
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": "```json\n" + json.dumps([
                                {
                                    "title": "タスク",
                                    "description": "説明",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "medium",
                                    "source_quote": "引用"
                                }
                            ]) + "\n```"
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = "タスクを抽出してください"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].title == "タスク"
    
    @patch("agents.tools.extract_tasks.boto3.client")
    def test_extract_tasks_priority_estimation(self, mock_boto_client):
        """優先度が正しく推定されることを確認 (Requirement 2.6)"""
        # Arrange
        mock_bedrock = MagicMock()
        mock_boto_client.return_value = mock_bedrock
        
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps([
                                {
                                    "title": "緊急タスク",
                                    "description": "至急対応が必要",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "high",
                                    "source_quote": "至急対応してください"
                                },
                                {
                                    "title": "通常タスク",
                                    "description": "通常の対応",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "medium",
                                    "source_quote": "対応してください"
                                },
                                {
                                    "title": "低優先度タスク",
                                    "description": "時間があれば対応",
                                    "assignee": None,
                                    "due_date": None,
                                    "priority": "low",
                                    "source_quote": "時間があれば対応してください"
                                }
                            ])
                        }
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = mock_response
        
        minutes_text = "様々な優先度のタスクがあります"
        
        # Act
        extractor = Task_Extractor()
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id="session-123",
            minutes_id="minutes-456",
        )
        
        # Assert
        assert len(task_list.tasks) == 3
        assert task_list.tasks[0].priority == Priority.HIGH
        assert task_list.tasks[1].priority == Priority.MEDIUM
        assert task_list.tasks[2].priority == Priority.LOW
    
    def test_build_prompt_includes_requirements(self):
        """プロンプトに必要な要件が含まれることを確認 (Requirement 1.3, 1.4)"""
        # Arrange
        extractor = Task_Extractor()
        minutes_text = "テスト議事録"
        
        # Act
        prompt = extractor._build_prompt(minutes_text)
        
        # Assert
        # Requirement 1.3: アクションアイテムセクション優先
        assert "アクションアイテムセクション優先" in prompt or "アクションアイテム" in prompt
        
        # Requirement 1.4: 暗黙的タスク抽出
        assert "暗黙的" in prompt or "決定事項" in prompt
        
        # 必須フィールドの説明
        assert "title" in prompt
        assert "description" in prompt
        assert "priority" in prompt
        assert "source_quote" in prompt
        
        # 優先度の説明
        assert "high" in prompt
        assert "medium" in prompt
        assert "low" in prompt
        
        # 議事録テキストが含まれる
        assert minutes_text in prompt
