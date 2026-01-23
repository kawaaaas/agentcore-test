"""
GitHub Integration Tools

Strands Agents SDK の @tool デコレータを使用した GitHub 連携ツール。
AgentCore Gateway 経由で GitHub API に接続し、Issue の作成と重複チェックを行う。

Requirements: 2.1, 7.1, 10.1
"""

import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from strands import tool

from agents.models.github_models import IssueResult, Priority, Task
from agents.tools.assignee_mapper import Assignee_Mapper
from agents.tools.duplicate_detector import Duplicate_Detector, Issue
from agents.tools.github_issue import Issue_Creator
from agents.tools.milestone_selector import Milestone, Milestone_Selector

# ロギング設定
logger = logging.getLogger(__name__)

# 環境変数から設定を取得
GITHUB_REPOSITORY_OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "")
GITHUB_REPOSITORY_NAME = os.getenv("GITHUB_REPOSITORY_NAME", "")


class CreateGitHubIssueInput(BaseModel):
    """単一Issue作成の入力スキーマ"""
    
    title: str = Field(..., description="タスクタイトル", max_length=100)
    description: str = Field(..., description="タスクの説明")
    assignee: Optional[str] = Field(None, description="担当者名（未定の場合はnull）")
    due_date: Optional[str] = Field(None, description="期限（YYYY-MM-DD形式、未定の場合はnull）")
    priority: str = Field(..., description="優先度（high/medium/low）")
    source_minutes_url: str = Field(..., description="元の議事録URL")
    custom_labels: Optional[List[str]] = Field(None, description="カスタムラベルリスト")


class CreateGitHubIssuesBatchInput(BaseModel):
    """一括Issue作成の入力スキーマ"""
    
    tasks: List[Dict[str, Any]] = Field(..., description="タスクリスト")
    custom_labels: Optional[List[str]] = Field(None, description="カスタムラベルリスト")


class CheckDuplicateIssueInput(BaseModel):
    """重複チェックの入力スキーマ"""
    
    title: str = Field(..., description="チェック対象のタイトル")
    threshold: Optional[float] = Field(0.8, description="重複判定の閾値（0.0〜1.0）")


@tool
def create_github_issue(
    title: str,
    description: str,
    priority: str,
    source_minutes_url: str,
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    custom_labels: Optional[List[str]] = None,
    repository_owner: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    単一のGitHub Issueを作成する
    
    タスク情報からGitHub Issueを作成します。
    ラベル、担当者、マイルストーンを自動設定します。
    
    Requirements: 2.1
    
    Args:
        title: タスクタイトル（100文字以内）
        description: タスクの説明
        priority: 優先度（high/medium/low）
        source_minutes_url: 元の議事録URL
        assignee: 担当者名（オプション、未定の場合はnull）
        due_date: 期限（オプション、YYYY-MM-DD形式、未定の場合はnull）
        custom_labels: カスタムラベルリスト（オプション）
        repository_owner: リポジトリオーナー（オプション、環境変数から取得）
        repository_name: リポジトリ名（オプション、環境変数から取得）
    
    Returns:
        dict: Issue作成結果
            - success: 成功フラグ
            - issue_url: 作成されたIssue URL（成功時）
            - issue_number: Issue番号（成功時）
            - error_message: エラーメッセージ（失敗時）
    """
    try:
        logger.info(f"GitHub Issue作成開始: title={title}")
        
        # リポジトリ情報を取得
        owner = repository_owner or GITHUB_REPOSITORY_OWNER
        repo = repository_name or GITHUB_REPOSITORY_NAME
        
        if not owner or not repo:
            error_msg = "リポジトリ情報が設定されていません（GITHUB_REPOSITORY_OWNER, GITHUB_REPOSITORY_NAME）"
            logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
            }
        
        # 優先度をPriorityに変換
        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        priority_enum = priority_map.get(priority.lower(), Priority.MEDIUM)
        
        # Taskオブジェクトを作成
        task = Task(
            title=title,
            description=description,
            assignee=assignee,
            due_date=due_date,
            priority=priority_enum,
            source_minutes_url=source_minutes_url,
        )
        
        # Issue_Creatorを初期化
        issue_creator = Issue_Creator(
            repository_owner=owner,
            repository_name=repo,
        )
        
        # Issueを作成
        # 注意: 実際のGitHub API呼び出しは後続タスクで実装
        # 現時点ではモックとして動作
        result = issue_creator.create_issue(
            task=task,
            custom_labels=custom_labels,
            milestones=None,  # マイルストーン取得は後続タスクで実装
            github_api_client=None,  # APIクライアントは後続タスクで実装
        )
        
        # 結果を返す
        return {
            "success": result.success,
            "task_title": result.task_title,
            "issue_url": result.issue_url,
            "issue_number": result.issue_number,
            "error_message": result.error_message,
        }
        
    except Exception as e:
        logger.error(f"GitHub Issue作成エラー: {e}")
        return {
            "success": False,
            "error_message": f"Issue作成に失敗しました: {str(e)}",
        }


@tool
def create_github_issues_batch(
    tasks: List[Dict[str, Any]],
    custom_labels: Optional[List[str]] = None,
    repository_owner: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    複数のGitHub Issueを一括作成する
    
    タスクリストから複数のGitHub Issueを一括作成します。
    各Issueの作成結果を個別に追跡します。
    
    Requirements: 7.1
    
    Args:
        tasks: タスクリスト（各タスクは辞書形式）
            - title: タスクタイトル
            - description: タスクの説明
            - assignee: 担当者名（オプション）
            - due_date: 期限（オプション、YYYY-MM-DD形式）
            - priority: 優先度（high/medium/low）
            - source_minutes_url: 元の議事録URL
        custom_labels: カスタムラベルリスト（オプション）
        repository_owner: リポジトリオーナー（オプション、環境変数から取得）
        repository_name: リポジトリ名（オプション、環境変数から取得）
    
    Returns:
        dict: 一括作成結果
            - success: 全体の成功フラグ
            - total: 総タスク数
            - success_count: 成功数
            - failure_count: 失敗数
            - results: 各Issueの作成結果リスト
    """
    try:
        logger.info(f"GitHub Issue一括作成開始: tasks_count={len(tasks)}")
        
        # リポジトリ情報を取得
        owner = repository_owner or GITHUB_REPOSITORY_OWNER
        repo = repository_name or GITHUB_REPOSITORY_NAME
        
        if not owner or not repo:
            error_msg = "リポジトリ情報が設定されていません（GITHUB_REPOSITORY_OWNER, GITHUB_REPOSITORY_NAME）"
            logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg,
                "total": len(tasks),
                "success_count": 0,
                "failure_count": len(tasks),
                "results": [],
            }
        
        # 優先度マッピング
        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        
        # Taskオブジェクトリストを作成
        task_objects = []
        for task_data in tasks:
            try:
                priority_str = task_data.get("priority", "medium").lower()
                priority_enum = priority_map.get(priority_str, Priority.MEDIUM)
                
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    assignee=task_data.get("assignee"),
                    due_date=task_data.get("due_date"),
                    priority=priority_enum,
                    source_minutes_url=task_data["source_minutes_url"],
                )
                task_objects.append(task)
            except Exception as e:
                logger.warning(f"タスクのパースに失敗: {e}, data={task_data}")
                continue
        
        # Issue_Creatorを初期化
        issue_creator = Issue_Creator(
            repository_owner=owner,
            repository_name=repo,
        )
        
        # 一括作成
        # 注意: 実際のGitHub API呼び出しは後続タスクで実装
        results = issue_creator.create_issues_batch(
            tasks=task_objects,
            custom_labels=custom_labels,
            milestones=None,  # マイルストーン取得は後続タスクで実装
            github_api_client=None,  # APIクライアントは後続タスクで実装
        )
        
        # 成功数と失敗数を集計
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        
        logger.info(
            f"GitHub Issue一括作成完了: "
            f"total={len(results)}, "
            f"success={success_count}, "
            f"failure={failure_count}"
        )
        
        # 結果を返す
        return {
            "success": failure_count == 0,
            "total": len(results),
            "success_count": success_count,
            "failure_count": failure_count,
            "results": [
                {
                    "task_title": r.task_title,
                    "success": r.success,
                    "issue_url": r.issue_url,
                    "issue_number": r.issue_number,
                    "error_message": r.error_message,
                }
                for r in results
            ],
        }
        
    except Exception as e:
        logger.error(f"GitHub Issue一括作成エラー: {e}")
        return {
            "success": False,
            "error_message": f"一括作成に失敗しました: {str(e)}",
            "total": len(tasks),
            "success_count": 0,
            "failure_count": len(tasks),
            "results": [],
        }


@tool
def check_duplicate_issue(
    title: str,
    threshold: Optional[float] = 0.8,
    repository_owner: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    重複Issueをチェックする
    
    指定されたタイトルと既存のIssueを比較し、重複を検出します。
    類似度が閾値以上の場合に重複とみなします。
    
    Requirements: 10.1
    
    Args:
        title: チェック対象のタイトル
        threshold: 重複判定の閾値（0.0〜1.0、デフォルト: 0.8）
        repository_owner: リポジトリオーナー（オプション、環境変数から取得）
        repository_name: リポジトリ名（オプション、環境変数から取得）
    
    Returns:
        dict: 重複チェック結果
            - is_duplicate: 重複フラグ
            - duplicates: 重複Issueリスト
                - number: Issue番号
                - title: Issueタイトル
                - url: Issue URL
                - state: Issueの状態（open/closed）
    """
    try:
        logger.info(f"重複Issueチェック開始: title={title}")
        
        # リポジトリ情報を取得
        owner = repository_owner or GITHUB_REPOSITORY_OWNER
        repo = repository_name or GITHUB_REPOSITORY_NAME
        
        if not owner or not repo:
            error_msg = "リポジトリ情報が設定されていません（GITHUB_REPOSITORY_OWNER, GITHUB_REPOSITORY_NAME）"
            logger.error(error_msg)
            return {
                "is_duplicate": False,
                "error_message": error_msg,
                "duplicates": [],
            }
        
        # 既存Issueを取得
        # 注意: 実際のGitHub API呼び出しは後続タスクで実装
        # 現時点ではモックとして空リストを返す
        existing_issues: List[Issue] = []
        
        # TODO: GitHub APIから既存Issueを取得
        # existing_issues = fetch_existing_issues(owner, repo)
        
        # Duplicate_Detectorを初期化
        detector = Duplicate_Detector()
        
        # 重複を検出
        duplicates = detector.find_duplicates(
            title=title,
            existing_issues=existing_issues,
            threshold=threshold,
        )
        
        # 結果を返す
        is_duplicate = len(duplicates) > 0
        
        logger.info(
            f"重複Issueチェック完了: "
            f"is_duplicate={is_duplicate}, "
            f"duplicates_count={len(duplicates)}"
        )
        
        return {
            "is_duplicate": is_duplicate,
            "duplicates": [
                {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.url,
                    "state": issue.state,
                }
                for issue in duplicates
            ],
        }
        
    except Exception as e:
        logger.error(f"重複Issueチェックエラー: {e}")
        return {
            "is_duplicate": False,
            "error_message": f"重複チェックに失敗しました: {str(e)}",
            "duplicates": [],
        }
