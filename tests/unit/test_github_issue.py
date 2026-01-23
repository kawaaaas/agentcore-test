"""
GitHub Issue Creator のユニットテスト

Issue_Creatorクラスの基本機能をテストする。
"""

import pytest

from agents.models.github_models import IssueRequest, Priority, Task
from agents.tools.assignee_mapper import Assignee_Mapper
from agents.tools.github_issue import Issue_Creator
from agents.tools.milestone_selector import Milestone, Milestone_Selector


class TestIssueCreator:
    """Issue_Creatorのテスト"""
    
    def test_get_priority_label(self):
        """優先度からラベル文字列を生成できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        # 各優先度のラベルを確認
        assert creator._get_priority_label(Priority.HIGH) == "priority: high"
        assert creator._get_priority_label(Priority.MEDIUM) == "priority: medium"
        assert creator._get_priority_label(Priority.LOW) == "priority: low"
    
    def test_build_labels_with_priority_only(self):
        """優先度ラベルのみを構築できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        labels = creator._build_labels(task)
        
        assert labels == ["priority: high"]
    
    def test_build_labels_with_custom_labels(self):
        """カスタムラベルを含むラベルリストを構築できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            priority=Priority.MEDIUM,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        custom_labels = ["bug", "enhancement"]
        labels = creator._build_labels(task, custom_labels)
        
        assert labels == ["priority: medium", "bug", "enhancement"]
    
    def test_build_assignees_without_mapper(self):
        """担当者マッピングなしの場合、空リストを返すこと"""
        # Assignee_Mapperをモック（DynamoDBテーブルなし）
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
            assignee_mapper=Assignee_Mapper(dynamodb_table_name=None),
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            assignee="山田太郎",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        assignees = creator._build_assignees(task)
        
        assert assignees == []
    
    def test_build_assignees_with_unassigned(self):
        """担当者が「未定」の場合、空リストを返すこと"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            assignee="未定",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        assignees = creator._build_assignees(task)
        
        assert assignees == []
    
    def test_select_milestone_without_milestones(self):
        """マイルストーンリストが空の場合、Noneを返すこと"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            due_date="2025-01-31",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        milestone = creator._select_milestone(task, milestones=[])
        
        assert milestone is None
    
    def test_select_milestone_with_valid_milestone(self):
        """適切なマイルストーンが存在する場合、選択できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            due_date="2025-01-31",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
            Milestone(number=2, title="v2.0", due_on="2025-03-31T23:59:59Z"),
        ]
        
        milestone = creator._select_milestone(task, milestones)
        
        # 期限以降で最も近いマイルストーンが選択される
        assert milestone == 1
    
    def test_create_issue_request(self):
        """Issue作成リクエストを構築できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        task = Task(
            title="テストタスク",
            description="テスト説明",
            assignee="未定",
            due_date="2025-01-31",
            priority=Priority.HIGH,
            source_minutes_url="https://example.com/minutes/1",
        )
        
        milestones = [
            Milestone(number=1, title="v1.0", due_on="2025-02-28T23:59:59Z"),
        ]
        
        issue_request = creator.create_issue_request(
            task=task,
            custom_labels=["bug"],
            milestones=milestones,
        )
        
        assert isinstance(issue_request, IssueRequest)
        assert issue_request.title == "テストタスク"
        assert "テスト説明" in issue_request.body
        assert "priority: high" in issue_request.labels
        assert "bug" in issue_request.labels
        assert issue_request.assignees == []
        assert issue_request.milestone == 1
    
    def test_get_issue_url(self):
        """Issue URLを生成できること"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        url = creator.get_issue_url(123)
        
        assert url == "https://github.com/test-owner/test-repo/issues/123"
    
    def test_create_issues_batch_returns_correct_count(self):
        """一括作成で正しい数の結果を返すこと"""
        creator = Issue_Creator(
            repository_owner="test-owner",
            repository_name="test-repo",
        )
        
        tasks = [
            Task(
                title=f"タスク{i}",
                description=f"説明{i}",
                priority=Priority.HIGH,
                source_minutes_url=f"https://example.com/minutes/{i}",
            )
            for i in range(3)
        ]
        
        # GitHub APIクライアントなしで実行（失敗する）
        results = creator.create_issues_batch(tasks)
        
        # 入力タスク数と同じ数の結果が返される
        assert len(results) == 3
        
        # すべて失敗している（APIクライアントが未設定のため）
        assert all(not r.success for r in results)
