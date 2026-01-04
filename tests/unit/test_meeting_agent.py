"""
Meeting Agent の統合テスト

エージェントの初期化と基本機能をテストする。
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# テスト用の環境変数を設定
os.environ["BEDROCK_MODEL_ID"] = "amazon.nova-lite-v1:0"
os.environ["AWS_REGION"] = "us-west-2"
os.environ["AGENTCORE_MEMORY_ENABLED"] = "false"  # テスト時はMemoryを無効化

from agents.meeting_agent import (
    create_agent,
    create_memory_session_manager,
    create_memory_client,
    save_minutes_to_s3,
    SYSTEM_PROMPT,
)
from agents.models.minutes import Minutes, ActionItem
from datetime import datetime


class TestMeetingAgent:
    """Meeting Agent のテストクラス"""
    
    def test_system_prompt_contains_requirements(self):
        """システムプロンプトが必要な要素を含むことを確認"""
        assert "議事録生成" in SYSTEM_PROMPT
        assert "タスク抽出" in SYSTEM_PROMPT
        assert "修正パターン" in SYSTEM_PROMPT
        assert "Requirements" in SYSTEM_PROMPT
    
    def test_create_agent_success(self):
        """エージェントが正常に作成できることを確認"""
        agent = create_agent()
        
        assert agent is not None
        # エージェントが正常に作成されたことを確認
        # Strands Agentの内部構造は変わる可能性があるため、
        # 単にインスタンスが作成されたことを確認する
        assert str(type(agent)) == "<class 'strands.agent.agent.Agent'>"
    
    def test_create_memory_session_manager_disabled(self):
        """Memory無効時にNoneが返されることを確認"""
        with patch.dict(os.environ, {"AGENTCORE_MEMORY_ENABLED": "false"}):
            manager = create_memory_session_manager()
            assert manager is None
    
    def test_create_memory_session_manager_no_memory_id(self):
        """Memory ID未設定時にNoneが返されることを確認"""
        with patch.dict(os.environ, {"AGENTCORE_MEMORY_ENABLED": "true", "AGENTCORE_MEMORY_ID": ""}):
            manager = create_memory_session_manager()
            assert manager is None
    
    def test_create_memory_client_disabled(self):
        """Memory無効時にNoneが返されることを確認"""
        with patch.dict(os.environ, {"AGENTCORE_MEMORY_ENABLED": "false"}):
            client = create_memory_client()
            assert client is None
    
    @patch("agents.meeting_agent.boto3.client")
    def test_save_minutes_to_s3_success(self, mock_boto_client):
        """S3保存が正常に動作することを確認"""
        # モックS3クライアントを設定
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # テスト用の議事録を作成
        minutes = Minutes(
            title="テスト会議",
            date=datetime(2025, 1, 4, 10, 0),
            participants=["田中", "佐藤"],
            agenda=["議題1", "議題2"],
            discussion="テスト議論内容",
            decisions=["決定事項1"],
            action_items=[
                ActionItem(
                    description="タスク1",
                    assignee="田中",
                    due_date="2025-01-10",
                    completed=False,
                )
            ],
        )
        
        # S3保存を実行（bucket_nameを明示的に渡す）
        filename = save_minutes_to_s3(
            minutes=minutes,
            session_id="test-session-123",
            source_file="test-transcript.txt",
            approver="佐藤",
            bucket_name="test-bucket",
        )
        
        # ファイル名が正しい形式であることを確認
        assert filename.startswith("2025-01-04_")
        assert filename.endswith(".md")
        
        # S3のput_objectが呼ばれたことを確認
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args
        
        # バケット名とキーが正しいことを確認
        assert call_args.kwargs["Bucket"] == "test-bucket"
        assert call_args.kwargs["Key"] == filename
        
        # メタデータが含まれていることを確認
        metadata = call_args.kwargs["Metadata"]
        assert "session-id" in metadata
        assert metadata["session-id"] == "test-session-123"
        assert "source-file" in metadata
        assert metadata["source-file"] == "test-transcript.txt"
        assert "approver" in metadata
        assert metadata["approver"] == "佐藤"
    
    def test_save_minutes_to_s3_no_bucket_name(self):
        """バケット名未設定時にエラーが発生することを確認"""
        minutes = Minutes(
            title="テスト会議",
            date=datetime.now(),
            participants=[],
            agenda=[],
            discussion="テスト",
            decisions=[],
            action_items=[],
        )
        
        with patch.dict(os.environ, {"MINUTES_BUCKET_NAME": ""}):
            with pytest.raises(ValueError, match="MINUTES_BUCKET_NAME"):
                save_minutes_to_s3(
                    minutes=minutes,
                    session_id="test-session",
                    source_file="test.txt",
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
