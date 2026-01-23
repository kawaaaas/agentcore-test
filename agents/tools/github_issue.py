"""
GitHub Issue Creator

GitHub Issuesの作成機能を提供する。
Requirements: 2.1, 2.5, 2.6, 3.1, 3.5, 3.6, 4.1, 4.3, 4.4, 5.1, 5.3, 7.1, 7.2, 7.3, 8.1
"""

import logging
import time
from typing import Optional

from agents.models.github_models import IssueRequest, IssueResult, Priority, Task
from agents.tools.assignee_mapper import Assignee_Mapper
from agents.tools.issue_formatter import Issue_Formatter
from agents.tools.milestone_selector import Milestone, Milestone_Selector

logger = logging.getLogger(__name__)


class Issue_Creator:
    """
    GitHub Issue作成
    
    タスクからGitHub Issueを作成する機能を提供する。
    ラベル、担当者、マイルストーンの設定を統合する。
    Requirements: 2.1, 2.5, 2.6, 3.1, 3.5, 3.6, 4.1, 4.3, 4.4, 5.1, 5.3, 7.1, 7.2, 7.3, 8.1
    """
    
    def __init__(
        self,
        repository_owner: str,
        repository_name: str,
        assignee_mapper: Optional[Assignee_Mapper] = None,
        milestone_selector: Optional[Milestone_Selector] = None,
        max_retries: int = 3,
    ):
        """
        Issue_Creatorを初期化
        
        Args:
            repository_owner: リポジトリオーナー
            repository_name: リポジトリ名
            assignee_mapper: 担当者マッパー（オプション）
            milestone_selector: マイルストーンセレクター（オプション）
            max_retries: 最大リトライ回数（デフォルト: 3）
        """
        self.repository_owner = repository_owner
        self.repository_name = repository_name
        self.assignee_mapper = assignee_mapper or Assignee_Mapper()
        self.milestone_selector = milestone_selector or Milestone_Selector()
        self.max_retries = max_retries
        self.issue_formatter = Issue_Formatter()
    
    def _get_priority_label(self, priority: Priority) -> str:
        """
        優先度からラベル文字列を生成
        
        優先度をGitHub Issueのラベル形式に変換する。
        
        Args:
            priority: タスクの優先度
            
        Returns:
            ラベル文字列（例: "priority: high"）
            
        Requirements: 3.1, 3.2, 3.3, 3.4
        """
        return f"priority: {priority.value}"
    
    def _build_labels(
        self,
        task: Task,
        custom_labels: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Issueに設定するラベルリストを構築
        
        優先度ラベルとカスタムラベルを組み合わせる。
        
        Args:
            task: タスク情報
            custom_labels: カスタムラベルリスト（オプション）
            
        Returns:
            ラベルリスト
            
        Requirements: 3.1, 3.6
        """
        labels = []
        
        # 優先度ラベルを追加
        priority_label = self._get_priority_label(task.priority)
        labels.append(priority_label)
        
        # カスタムラベルを追加
        if custom_labels:
            labels.extend(custom_labels)
        
        logger.info(f"ラベルリスト構築: labels={labels}")
        return labels
    
    def _build_assignees(self, task: Task) -> list[str]:
        """
        Issueに設定する担当者リストを構築
        
        タスクの担当者名をGitHubユーザー名にマッピングする。
        マッピングが存在しない場合は空リストを返す。
        
        Args:
            task: タスク情報
            
        Returns:
            担当者リスト（GitHubユーザー名）
            
        Requirements: 4.1, 4.3, 4.4
        """
        assignees = []
        
        # 担当者マッピングを取得
        github_username = self.assignee_mapper.get_github_username(task.assignee)
        
        if github_username:
            assignees.append(github_username)
            logger.info(f"担当者設定: {task.assignee} -> {github_username}")
        else:
            logger.info(f"担当者マッピングなし: assignee={task.assignee}")
        
        return assignees
    
    def _select_milestone(
        self,
        task: Task,
        milestones: Optional[list[Milestone]] = None,
    ) -> Optional[int]:
        """
        Issueに設定するマイルストーンを選択
        
        タスクの期限に基づいて最適なマイルストーンを選択する。
        適切なマイルストーンが存在しない場合はNoneを返す。
        
        Args:
            task: タスク情報
            milestones: マイルストーンリスト（オプション）
            
        Returns:
            マイルストーン番号、またはNone
            
        Requirements: 5.1, 5.3
        """
        if not milestones:
            logger.info("マイルストーンリストが空です")
            return None
        
        milestone_number = self.milestone_selector.select_milestone(
            task.due_date,
            milestones,
        )
        
        if milestone_number:
            logger.info(f"マイルストーン選択: milestone_number={milestone_number}")
        else:
            logger.info("適切なマイルストーンが見つかりませんでした")
        
        return milestone_number
    
    def create_issue_request(
        self,
        task: Task,
        custom_labels: Optional[list[str]] = None,
        milestones: Optional[list[Milestone]] = None,
    ) -> IssueRequest:
        """
        タスクからIssue作成リクエストを構築
        
        タスク情報を元に、GitHub APIに送信するIssue作成リクエストを構築する。
        ラベル、担当者、マイルストーンの設定を統合する。
        
        Args:
            task: タスク情報
            custom_labels: カスタムラベルリスト（オプション）
            milestones: マイルストーンリスト（オプション）
            
        Returns:
            Issue作成リクエスト
            
        Requirements: 2.1, 3.1, 3.6, 4.1, 4.3, 4.4, 5.1, 5.3
        """
        # Issue本文を生成
        body = self.issue_formatter.format_issue_body(task)
        
        # ラベルを構築
        labels = self._build_labels(task, custom_labels)
        
        # 担当者を構築
        assignees = self._build_assignees(task)
        
        # マイルストーンを選択
        milestone = self._select_milestone(task, milestones)
        
        # IssueRequestを構築
        issue_request = IssueRequest(
            title=task.title,
            body=body,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
        )
        
        logger.info(
            f"Issue作成リクエスト構築完了: "
            f"title={task.title}, "
            f"labels={labels}, "
            f"assignees={assignees}, "
            f"milestone={milestone}"
        )
        
        return issue_request
    
    def create_issue(
        self,
        task: Task,
        custom_labels: Optional[list[str]] = None,
        milestones: Optional[list[Milestone]] = None,
        github_api_client=None,
    ) -> IssueResult:
        """
        単一Issueを作成
        
        タスクからGitHub Issueを作成する。
        リトライロジック（最大3回、指数バックオフ）を実装する。
        
        Args:
            task: タスク情報
            custom_labels: カスタムラベルリスト（オプション）
            milestones: マイルストーンリスト（オプション）
            github_api_client: GitHub APIクライアント（テスト用）
            
        Returns:
            Issue作成結果
            
        Requirements: 2.1, 2.5, 2.6, 8.1
        """
        logger.info(f"Issue作成開始: task_title={task.title}")
        
        # Issue作成リクエストを構築
        issue_request = self.create_issue_request(task, custom_labels, milestones)
        
        # リトライロジック
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # GitHub APIを呼び出し（実装は後続タスクで追加）
                if github_api_client:
                    response = github_api_client.create_issue(
                        owner=self.repository_owner,
                        repo=self.repository_name,
                        issue_request=issue_request,
                    )
                    
                    # 成功結果を返す
                    issue_url = self.get_issue_url(response["number"])
                    result = IssueResult(
                        task_title=task.title,
                        success=True,
                        issue_url=issue_url,
                        issue_number=response["number"],
                    )
                    
                    logger.info(
                        f"Issue作成成功: "
                        f"task_title={task.title}, "
                        f"issue_number={response['number']}, "
                        f"issue_url={issue_url}"
                    )
                    
                    return result
                else:
                    # APIクライアントが未設定の場合（開発中）
                    raise NotImplementedError("GitHub APIクライアントが未設定です")
                    
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Issue作成失敗（試行 {attempt + 1}/{self.max_retries}）: "
                    f"task_title={task.title}, "
                    f"error={str(e)}"
                )
                
                # 最後の試行でない場合は指数バックオフで待機
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 1秒、2秒、4秒
                    logger.info(f"リトライ待機: {wait_time}秒")
                    time.sleep(wait_time)
        
        # すべてのリトライが失敗した場合
        error_message = f"Issue作成失敗（{self.max_retries}回リトライ）: {str(last_error)}"
        logger.error(error_message)
        
        result = IssueResult(
            task_title=task.title,
            success=False,
            error_message=error_message,
        )
        
        return result
    
    def get_issue_url(self, issue_number: int) -> str:
        """
        Issue番号からIssue URLを生成
        
        Args:
            issue_number: Issue番号
            
        Returns:
            Issue URL
            
        Requirements: 2.5
        """
        url = f"https://github.com/{self.repository_owner}/{self.repository_name}/issues/{issue_number}"
        return url
    
    def create_issues_batch(
        self,
        tasks: list[Task],
        custom_labels: Optional[list[str]] = None,
        milestones: Optional[list[Milestone]] = None,
        github_api_client=None,
    ) -> list[IssueResult]:
        """
        複数Issueを一括作成
        
        タスクリストから複数のGitHub Issueを一括作成する。
        各Issueの作成結果を個別に追跡する。
        
        Args:
            tasks: タスクリスト
            custom_labels: カスタムラベルリスト（オプション）
            milestones: マイルストーンリスト（オプション）
            github_api_client: GitHub APIクライアント（テスト用）
            
        Returns:
            Issue作成結果リスト
            
        Requirements: 7.1, 7.2, 7.3
        """
        logger.info(f"一括Issue作成開始: tasks_count={len(tasks)}")
        
        results = []
        
        for task in tasks:
            # 各Issueを個別に作成
            result = self.create_issue(
                task=task,
                custom_labels=custom_labels,
                milestones=milestones,
                github_api_client=github_api_client,
            )
            results.append(result)
        
        # 成功数と失敗数を集計
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        logger.info(
            f"一括Issue作成完了: "
            f"total={len(results)}, "
            f"success={success_count}, "
            f"failure={failure_count}"
        )
        
        return results
