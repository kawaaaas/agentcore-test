"""
Milestone Selector

期限に基づいて最適なマイルストーンを選択する機能を提供する。
Requirements: 5.1, 5.2, 5.3
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Milestone:
    """
    マイルストーン情報
    
    GitHubのマイルストーン情報を表現する。
    """
    
    def __init__(
        self,
        number: int,
        title: str,
        due_on: Optional[str] = None,
    ):
        """
        Milestoneを初期化
        
        Args:
            number: マイルストーン番号
            title: マイルストーンタイトル
            due_on: 期限（ISO 8601形式の文字列、例: "2025-01-31T23:59:59Z"）
        """
        self.number = number
        self.title = title
        self.due_on = due_on


class Milestone_Selector:
    """
    マイルストーン選択
    
    タスクの期限に基づいて、最も適切なマイルストーンを選択する機能を提供する。
    Requirements: 5.1, 5.2, 5.3
    """
    
    def select_milestone(
        self,
        due_date: Optional[str],
        milestones: list[Milestone],
    ) -> Optional[int]:
        """
        期限に最も近いマイルストーンを選択
        
        タスクの期限に基づいて、期限以降で最も近いマイルストーンを選択する。
        期限が「未定」の場合、または適切なマイルストーンが存在しない場合はNoneを返す。
        
        Args:
            due_date: タスクの期限（ISO 8601形式の文字列、例: "2025-01-31"）
            milestones: マイルストーンリスト
            
        Returns:
            マイルストーン番号、またはNone
            - 適切なマイルストーンが存在する場合: マイルストーン番号
            - 期限が「未定」の場合: None
            - 期限がNoneの場合: None
            - 適切なマイルストーンが存在しない場合: None
            
        Requirements: 5.1, 5.2, 5.3
        """
        # 期限が未指定または「未定」の場合はNoneを返す
        if not due_date or due_date == "未定":
            logger.info(f"期限が未定のためNoneを返します: due_date={due_date}")
            return None
        
        # マイルストーンリストが空の場合
        if not milestones:
            logger.info("マイルストーンリストが空です")
            return None
        
        try:
            # 期限をdatetimeオブジェクトに変換
            task_due_date = self._parse_date(due_date)
            if not task_due_date:
                logger.warning(f"期限のパースに失敗しました: due_date={due_date}")
                return None
            
            logger.info(f"マイルストーン選択開始: due_date={due_date}, milestones_count={len(milestones)}")
            
            # 期限以降のマイルストーンをフィルタリング
            valid_milestones = []
            for milestone in milestones:
                if milestone.due_on:
                    milestone_due_date = self._parse_date(milestone.due_on)
                    if milestone_due_date and milestone_due_date >= task_due_date:
                        valid_milestones.append((milestone, milestone_due_date))
            
            # 有効なマイルストーンが存在しない場合
            if not valid_milestones:
                logger.info(f"期限以降のマイルストーンが存在しません: due_date={due_date}")
                return None
            
            # 最も近いマイルストーンを選択（期限が最も早いもの）
            closest_milestone = min(valid_milestones, key=lambda x: x[1])
            selected_milestone = closest_milestone[0]
            
            logger.info(
                f"マイルストーン選択成功: "
                f"milestone_number={selected_milestone.number}, "
                f"milestone_title={selected_milestone.title}, "
                f"milestone_due_on={selected_milestone.due_on}"
            )
            
            return selected_milestone.number
            
        except Exception as e:
            # その他のエラー
            logger.error(f"予期しないエラー: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        日付文字列をdatetimeオブジェクトに変換
        
        ISO 8601形式の日付文字列をパースする。
        複数のフォーマットに対応する。
        
        Args:
            date_str: 日付文字列
            
        Returns:
            datetimeオブジェクト、またはNone
        """
        # サポートする日付フォーマット
        formats = [
            "%Y-%m-%d",                    # 2025-01-31
            "%Y-%m-%dT%H:%M:%S",           # 2025-01-31T23:59:59
            "%Y-%m-%dT%H:%M:%SZ",          # 2025-01-31T23:59:59Z
            "%Y-%m-%dT%H:%M:%S.%fZ",       # 2025-01-31T23:59:59.000Z
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # すべてのフォーマットで失敗した場合
        logger.warning(f"日付のパースに失敗しました: date_str={date_str}")
        return None
