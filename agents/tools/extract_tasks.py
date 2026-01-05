"""
タスク抽出ツール

議事録からアクションアイテム（タスク）を抽出するツール。
Bedrock Nova 2 Liteを使用した議事録解析を行う。

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import boto3
from pydantic import BaseModel, Field
from strands import tool

from agents.tools.duplicate_detector import DuplicateDetector
from agents.tools.task_models import Priority, Task, TaskList, TaskListStatus
from agents.tools.task_validator import Task_Validator
from agents.utils.error import send_error_notification
from agents.utils.retry import with_retry

# ロガー設定
logger = logging.getLogger(__name__)


class ExtractTasksInput(BaseModel):
    """タスク抽出の入力スキーマ"""
    
    minutes_text: str = Field(
        ...,
        description="承認済み議事録テキスト",
        min_length=10,
    )
    session_id: str = Field(
        ...,
        description="AgentCoreセッションID",
    )
    minutes_id: str = Field(
        ...,
        description="議事録ID",
    )
    memory_id: Optional[str] = Field(
        default=None,
        description="AgentCore Memory ID（LTM検索用）",
    )


class Task_Extractor:
    """
    タスク抽出クラス
    
    Bedrock Nova 2 Liteを使用して議事録からタスクを抽出する。
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6
    """
    
    def __init__(
        self,
        region_name: str = "us-west-2",
        model_id: str = "amazon.nova-lite-v1:0",
        slack_client: Optional[Any] = None,
        slack_channel_id: Optional[str] = None,
        memory_client: Optional[Any] = None,
    ):
        """
        初期化
        
        Args:
            region_name: AWSリージョン
            model_id: Bedrockモデル ID
            slack_client: Slack APIクライアント（エラー通知用、オプション）
            slack_channel_id: SlackチャンネルID（エラー通知用、オプション）
            memory_client: AgentCore Memoryクライアント（オプション）
        """
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
        )
        self.model_id = model_id
        self.region_name = region_name
        self.slack_client = slack_client
        self.slack_channel_id = slack_channel_id
        self.memory_client = memory_client
    
    def _create_error_handler(self, session_id: str):
        """
        エラーハンドラーを作成する
        
        Requirements: 7.2
        
        Args:
            session_id: セッションID
            
        Returns:
            エラーハンドラー関数
        """
        def error_handler(exc: Exception, func_name: str, context: Dict[str, Any]):
            """リトライ失敗時のエラーハンドラー"""
            # Requirement 7.3: エラー内容をログに記録
            logger.error(
                f"最終的にエラーが発生しました: {func_name} - {type(exc).__name__}: {str(exc)}"
            )
            
            # Requirement 7.2: Slackにエラー通知を送信
            if self.slack_client and self.slack_channel_id:
                try:
                    send_error_notification(
                        slack_client=self.slack_client,
                        channel_id=self.slack_channel_id,
                        error_type="Bedrock API Error",
                        error_message=f"{type(exc).__name__}: {str(exc)}",
                        context={
                            "function": func_name,
                            "model_id": self.model_id,
                            "region": self.region_name,
                        },
                        session_id=session_id,
                    )
                    logger.info("Slackにエラー通知を送信しました")
                except Exception as notify_error:
                    logger.error(f"Slackエラー通知の送信に失敗: {notify_error}")
        
        return error_handler
    
    def extract_tasks(
        self,
        minutes_text: str,
        session_id: str,
        minutes_id: str,
        memory_id: Optional[str] = None,
    ) -> TaskList:
        """
        議事録からタスクを抽出する
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6, 7.4
        
        Args:
            minutes_text: 承認済み議事録テキスト
            session_id: セッションID
            minutes_id: 議事録ID
            memory_id: Memory ID（LTM検索用）
            
        Returns:
            抽出されたタスクリスト
            
        Raises:
            ValueError: 入力検証エラー
            Exception: Bedrock API呼び出しエラー
        """
        logger.info(f"タスク抽出開始: session_id={session_id}, minutes_id={minutes_id}")
        
        # Requirement 1.1: 議事録が承認された場合、自動的にタスク抽出処理を開始
        # 入力検証
        if not minutes_text or len(minutes_text.strip()) < 10:
            logger.warning("議事録テキストが短すぎます")
            # Requirement 1.5: タスクが含まれない場合、空のTaskListを返す
            return TaskList(
                session_id=session_id,
                minutes_id=minutes_id,
                tasks=[],
                status=TaskListStatus.PENDING,
            )
        
        # Requirement 9.2, 9.3: 過去の修正パターンをLTMから検索して適用
        modification_patterns = []
        if memory_id:
            modification_patterns = self._search_modification_patterns_from_ltm(
                session_id=session_id,
                memory_id=memory_id,
            )
        
        # プロンプトを構築
        prompt = self._build_prompt(minutes_text)
        
        try:
            # Requirement 1.2: Nova 2 Liteを使用して議事録を解析
            # Requirement 7.1: Bedrock API呼び出しが失敗した場合、最大3回リトライ
            response_text = self._invoke_bedrock_with_retry(prompt, session_id)
            
            # レスポンスをパースしてタスクリストを構築
            raw_tasks = self._parse_response(response_text, minutes_text)
            
            # Requirement 9.3: 類似の修正パターンが見つかった場合、適用する
            if modification_patterns:
                logger.info(f"{len(modification_patterns)}件の修正パターンを適用します")
                raw_tasks = self._apply_modification_patterns(raw_tasks, modification_patterns)
            
        except Exception as e:
            # Requirement 7.4: タスク抽出が部分的に失敗した場合、成功したタスクのみを返す
            logger.error(f"タスク抽出中にエラーが発生しました: {e}")
            logger.info("空のタスクリストを返します")
            return TaskList(
                session_id=session_id,
                minutes_id=minutes_id,
                tasks=[],
                status=TaskListStatus.PENDING,
            )
        
        # Requirement 6.1, 6.2: 重複タスクを検出・統合
        logger.info(f"重複検出前のタスク数: {len(raw_tasks)}")
        deduplicated_tasks = DuplicateDetector.merge_duplicates(raw_tasks)
        logger.info(f"重複検出後のタスク数: {len(deduplicated_tasks)}")
        
        # タスクリストを作成
        task_list = TaskList(
            session_id=session_id,
            minutes_id=minutes_id,
            tasks=deduplicated_tasks,
            status=TaskListStatus.PENDING,
        )
        
        # Requirement 3.5: 検証に合格したタスクのみをTaskListに含める
        validated_task_list = Task_Validator.validate_and_filter(task_list)
        
        logger.info(f"タスク抽出完了: {len(validated_task_list.tasks)}個のタスクを抽出")
        
        # Requirement 1.5: タスクが含まれない場合、空のTaskListを返す
        return validated_task_list
    
    def _invoke_bedrock_with_retry(self, prompt: str, session_id: str) -> str:
        """
        リトライ付きでBedrock APIを呼び出す
        
        Requirements: 7.1, 7.2, 7.3
        
        Args:
            prompt: プロンプト文字列
            session_id: セッションID
            
        Returns:
            Bedrockのレスポンステキスト
            
        Raises:
            Exception: Bedrock API呼び出しエラー
        """
        # エラーハンドラーを作成
        error_handler = self._create_error_handler(session_id)
        
        # リトライ付きでBedrock APIを呼び出す
        @with_retry(
            max_retries=3,
            base_delay=1.0,
            exceptions=(Exception,),
            on_final_failure=error_handler,
        )
        def invoke():
            return self._invoke_bedrock(prompt)
        
        return invoke()
    
    def _search_modification_patterns_from_ltm(
        self,
        session_id: str,
        memory_id: str,
    ) -> List[Dict[str, Any]]:
        """
        LTMから過去の修正パターンを検索する
        
        Requirements: 9.2, 9.3, 9.4
        
        Args:
            session_id: AgentCoreセッションID
            memory_id: Memory ID
        
        Returns:
            修正パターンのリスト
        """
        if not self.memory_client:
            return []
        
        try:
            # LTMからセマンティック検索で修正パターンを取得
            # タスク抽出に関連する修正パターンを検索
            response = self.memory_client.retrieve_memories(
                session_id=session_id,
                memory_id=memory_id,
                query="タスク抽出の修正パターン",
                max_results=5,
            )
            
            # 検索結果をパース
            patterns = []
            memories = response.get("memories", [])
            
            for memory in memories:
                try:
                    content = memory.get("content", "")
                    pattern = json.loads(content)
                    patterns.append(pattern)
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"LTMから{len(patterns)}件の修正パターンを取得しました")
            return patterns
            
        except Exception as e:
            logger.warning(f"LTMからの修正パターン検索に失敗: {e}")
            return []
    
    def _apply_modification_patterns(
        self,
        tasks: List[Task],
        patterns: List[Dict[str, Any]],
    ) -> List[Task]:
        """
        修正パターンをタスクに適用する
        
        Requirements: 9.3, 9.4
        
        Args:
            tasks: タスクリスト
            patterns: 修正パターンのリスト
        
        Returns:
            修正パターンを適用したタスクリスト
        """
        if not patterns:
            return tasks
        
        # パターンを適用（簡易実装）
        # 実際の実装では、より高度なパターンマッチングを行う
        applied_tasks = []
        
        for task in tasks:
            modified_task = task
            
            # 各パターンをチェック
            for pattern in patterns:
                modification_type = pattern.get("modification_type")
                original = pattern.get("original", {})
                modified = pattern.get("modified", {})
                
                # タイトルが類似している場合、パターンを適用
                if self._is_similar_title(task.title, original.get("title", "")):
                    # 優先度の変更パターンを適用
                    if modification_type == "priority_change":
                        from agents.tools.task_models import Priority
                        priority_str = modified.get("priority", "medium")
                        if priority_str == "high":
                            modified_task.priority = Priority.HIGH
                        elif priority_str == "low":
                            modified_task.priority = Priority.LOW
                        else:
                            modified_task.priority = Priority.MEDIUM
                        
                        logger.info(f"修正パターンを適用: {task.title} の優先度を {priority_str} に変更")
                    
                    # 担当者の変更パターンを適用
                    elif modification_type == "assignee_change":
                        assignee = modified.get("assignee")
                        if assignee:
                            modified_task.assignee = assignee
                            logger.info(f"修正パターンを適用: {task.title} の担当者を {assignee} に変更")
            
            applied_tasks.append(modified_task)
        
        return applied_tasks
    
    def _is_similar_title(self, title1: str, title2: str, threshold: float = 0.7) -> bool:
        """
        タイトルの類似度を判定する
        
        Args:
            title1: タイトル1
            title2: タイトル2
            threshold: 類似度の閾値（デフォルト: 0.7）
        
        Returns:
            類似している場合True
        """
        if not title1 or not title2:
            return False
        
        # 簡易的な類似度判定（共通部分文字列の割合）
        title1_lower = title1.lower()
        title2_lower = title2.lower()
        
        # 完全一致
        if title1_lower == title2_lower:
            return True
        
        # 部分一致
        if title1_lower in title2_lower or title2_lower in title1_lower:
            return True
        
        # 単語レベルの一致率
        words1 = set(title1_lower.split())
        words2 = set(title2_lower.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        
        return similarity >= threshold
    
    def _build_prompt(self, minutes_text: str) -> str:
        """
        Bedrock用のプロンプトを構築する
        
        Requirements: 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        
        Args:
            minutes_text: 議事録テキスト
            
        Returns:
            プロンプト文字列
        """
        prompt = f"""あなたは議事録からアクションアイテム（タスク）を抽出する専門家です。
以下の議事録を分析し、タスクを抽出してください。

# 抽出ルール

## 優先順位
1. **アクションアイテムセクション優先**: 「アクションアイテム」「TODO」「タスク」などのセクションを優先的に解析してください
2. **暗黙的タスク抽出**: 議論内容や決定事項からも、実行が必要な暗黙的なタスクを抽出してください

## タスクの判定基準
以下のいずれかに該当する内容をタスクとして抽出してください：
- 「〜する」「〜を行う」などの動詞で終わる文
- 担当者が明記されている項目
- 期限が設定されている項目
- 「TODO」「アクション」「対応」「確認」「検討」「作成」「実装」などのキーワードを含む項目
- 決定事項に基づいて実行が必要な作業

## タスク情報の抽出
各タスクについて、以下の情報を抽出してください：

### 必須フィールド
- **title**: タスクのタイトル（100文字以内に要約）
- **description**: タスクの詳細説明
- **priority**: 優先度（high/medium/low）
  - high: 「至急」「緊急」「今週中」「ASAP」などのキーワードがある場合
  - medium: 期限が明示されているが緊急ではない場合
  - low: 期限が明示されていない、または長期的なタスク
- **source_quote**: 元の議事録の該当箇所（そのまま引用）

### オプションフィールド
- **assignee**: 担当者（明示されていない場合はnull）
- **due_date**: 期限（YYYY-MM-DD形式、明示されていない場合はnull）

# 出力形式

JSON配列形式で出力してください。各タスクは以下の構造を持ちます：

```json
[
  {{
    "title": "タスクタイトル（100文字以内）",
    "description": "タスクの詳細説明",
    "assignee": "担当者名またはnull",
    "due_date": "YYYY-MM-DDまたはnull",
    "priority": "high|medium|low",
    "source_quote": "元の議事録の該当箇所"
  }}
]
```

# 議事録

{minutes_text}

# 出力

上記の議事録から抽出したタスクをJSON配列形式で出力してください。
タスクが1つもない場合は、空の配列 [] を返してください。
"""
        return prompt
    
    @with_retry(
        max_retries=3,
        base_delay=1.0,
        exceptions=(Exception,),
    )
    def _invoke_bedrock(self, prompt: str) -> str:
        """
        Bedrock Nova 2 Liteを呼び出す（内部メソッド）
        
        このメソッドは_invoke_bedrock_with_retryから呼び出される。
        直接呼び出さないこと。
        
        Requirements: 1.2
        
        Args:
            prompt: プロンプト文字列
            
        Returns:
            Bedrockのレスポンステキスト
            
        Raises:
            Exception: Bedrock API呼び出しエラー
        """
        logger.info("Bedrock API呼び出し開始")
        
        # Converse APIを使用
        response = self.bedrock_client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt,
                        }
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.3,  # 一貫性を重視
            },
        )
        
        response_text = response["output"]["message"]["content"][0]["text"]
        
        logger.info(f"Bedrock API呼び出し完了: {len(response_text)}文字")
        
        return response_text
    
    def _parse_response(
        self,
        response_text: str,
        minutes_text: str,
    ) -> List[Task]:
        """
        Bedrockのレスポンスをパースしてタスクリストを構築する
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        
        Args:
            response_text: Bedrockのレスポンステキスト
            minutes_text: 元の議事録テキスト（フォールバック用）
            
        Returns:
            タスクのリスト
        """
        tasks = []
        
        try:
            # JSONを抽出（マークダウンのコードブロックに囲まれている場合に対応）
            json_text = response_text.strip()
            
            # ```json ... ``` の形式の場合、中身を抽出
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                json_text = "\n".join(json_lines)
            
            # JSONをパース
            task_data_list = json.loads(json_text)
            
            if not isinstance(task_data_list, list):
                logger.warning("レスポンスがリスト形式ではありません")
                return []
            
            # 各タスクデータをTaskオブジェクトに変換
            for task_data in task_data_list:
                try:
                    # 必須フィールドの確認
                    if not all(k in task_data for k in ["title", "description", "priority", "source_quote"]):
                        logger.warning(f"必須フィールドが不足しています: {task_data}")
                        continue
                    
                    # Requirement 2.2: タイトルを100文字以内に要約
                    title = task_data["title"][:100]
                    
                    # Requirement 2.3: 説明に元の議事録の該当箇所を引用
                    description = task_data["description"]
                    source_quote = task_data["source_quote"]
                    
                    # Requirement 2.4: 担当者が明示されていない場合は「未定」（None）
                    assignee = task_data.get("assignee")
                    
                    # Requirement 2.5: 期限が明示されていない場合は「未定」（None）
                    due_date_str = task_data.get("due_date")
                    due_date = None
                    if due_date_str and due_date_str != "null":
                        try:
                            due_date = date.fromisoformat(due_date_str)
                        except ValueError:
                            logger.warning(f"無効な日付形式: {due_date_str}")
                    
                    # Requirement 2.6: 優先度を判定（high/medium/low）
                    priority_str = task_data.get("priority", "medium").lower()
                    if priority_str == "high":
                        priority = Priority.HIGH
                    elif priority_str == "low":
                        priority = Priority.LOW
                    else:
                        priority = Priority.MEDIUM
                    
                    # Taskオブジェクトを作成
                    task = Task(
                        title=title,
                        description=description,
                        assignee=assignee,
                        due_date=due_date,
                        priority=priority,
                        source_quote=source_quote,
                    )
                    
                    tasks.append(task)
                    
                except Exception as e:
                    logger.warning(f"タスクのパースに失敗: {e}, data={task_data}")
                    continue
            
            logger.info(f"{len(tasks)}個のタスクをパースしました")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー: {e}")
            logger.error(f"レスポンステキスト: {response_text[:500]}")
        except Exception as e:
            logger.error(f"レスポンスのパースエラー: {e}")
        
        return tasks


@tool
def extract_tasks_from_minutes(
    minutes_text: str,
    session_id: str,
    minutes_id: str,
    memory_id: Optional[str] = None,
) -> dict:
    """
    承認済み議事録からタスクを抽出する
    
    このツールはBedrock Nova 2 Liteを使用して議事録を解析し、
    アクションアイテムを構造化されたタスクリストとして抽出します。
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.6
    
    Args:
        minutes_text: 承認済み議事録テキスト
        session_id: AgentCoreセッションID
        minutes_id: 議事録ID
        memory_id: AgentCore Memory ID（LTM検索用、オプション）
    
    Returns:
        dict: 抽出結果
            - success: 処理成功フラグ
            - task_list: TaskListオブジェクト（辞書形式）
            - task_count: タスク数
            - message: メッセージ
    """
    try:
        # Task_Extractorを初期化
        extractor = Task_Extractor()
        
        # タスクを抽出
        task_list = extractor.extract_tasks(
            minutes_text=minutes_text,
            session_id=session_id,
            minutes_id=minutes_id,
            memory_id=memory_id,
        )
        
        return {
            "success": True,
            "task_list": task_list.model_dump(),
            "task_count": len(task_list.tasks),
            "message": f"{len(task_list.tasks)}個のタスクを抽出しました",
        }
        
    except Exception as e:
        logger.error(f"タスク抽出エラー: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_count": 0,
            "message": "タスク抽出に失敗しました",
        }
