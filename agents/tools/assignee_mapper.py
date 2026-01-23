"""
Assignee Mapper

担当者名をGitHubユーザー名にマッピングする機能を提供する。
Requirements: 4.1, 4.2, 4.3, 4.4
"""

import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Assignee_Mapper:
    """
    担当者マッピング
    
    DynamoDBから担当者名とGitHubユーザー名のマッピングを取得し、
    担当者名をGitHubユーザー名に変換する機能を提供する。
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    
    def __init__(
        self,
        dynamodb_table_name: Optional[str] = None,
    ):
        """
        Assignee_Mapperを初期化
        
        Args:
            dynamodb_table_name: DynamoDBテーブル名（オプション、環境変数から取得）
        """
        self.dynamodb_table_name = dynamodb_table_name or os.environ.get(
            "DYNAMODB_ASSIGNEE_MAPPING_TABLE_NAME"
        )
        
        # DynamoDBクライアントの初期化
        if self.dynamodb_table_name:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table(self.dynamodb_table_name)
        else:
            self.dynamodb = None
            self.table = None
    
    def get_github_username(self, display_name: Optional[str]) -> Optional[str]:
        """
        担当者名をGitHubユーザー名にマッピング
        
        DynamoDBから担当者名に対応するGitHubユーザー名を取得する。
        マッピングが存在しない場合、または担当者が「未定」の場合はNoneを返す。
        
        Args:
            display_name: 担当者名（表示名）
            
        Returns:
            GitHubユーザー名、またはNone
            - マッピングが存在する場合: GitHubユーザー名
            - マッピングが存在しない場合: None
            - 担当者が「未定」の場合: None
            - 担当者がNoneの場合: None
            
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # 担当者が未指定または「未定」の場合はNoneを返す
        if not display_name or display_name == "未定":
            logger.info(f"担当者が未定のためNoneを返します: display_name={display_name}")
            return None
        
        # DynamoDBテーブルが初期化されていない場合
        if not self.table:
            logger.warning("DynamoDBテーブルが初期化されていません")
            return None
        
        try:
            # DynamoDBからマッピングを取得
            logger.info(f"担当者マッピングを取得: display_name={display_name}")
            response = self.table.get_item(Key={"display_name": display_name})
            
            # マッピングが存在する場合
            if "Item" in response:
                github_user = response["Item"].get("github_user")
                logger.info(f"マッピング取得成功: {display_name} -> {github_user}")
                return github_user
            else:
                # マッピングが存在しない場合
                logger.info(f"マッピングが存在しません: display_name={display_name}")
                return None
                
        except ClientError as e:
            # DynamoDBエラー
            logger.error(f"DynamoDBエラー: {e}")
            return None
        except Exception as e:
            # その他のエラー
            logger.error(f"予期しないエラー: {e}")
            return None
