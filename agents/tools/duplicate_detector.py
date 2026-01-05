"""
重複タスク検出

タスクリスト内の重複タスクを検出し、統合する。
Requirements: 6.1, 6.2, 6.3, 6.4
"""

from typing import List, Tuple

from agents.tools.task_models import Task


class DuplicateDetector:
    """
    重複タスク検出器
    
    Levenshtein距離ベースの類似度計算により、重複タスクを検出・統合する。
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    
    SIMILARITY_THRESHOLD = 0.8  # 80%以上で重複とみなす
    
    @staticmethod
    def calculate_similarity(title1: str, title2: str) -> float:
        """
        2つのタイトル間の類似度を計算する
        
        Levenshtein距離を使用して、0.0（完全に異なる）から1.0（完全に一致）の
        範囲で類似度を返す。
        
        Args:
            title1: 比較対象のタイトル1
            title2: 比較対象のタイトル2
            
        Returns:
            類似度（0.0 ~ 1.0）
            
        Requirements: 6.3
        """
        if not title1 or not title2:
            return 0.0
        
        # 正規化: 小文字化、前後の空白削除
        t1 = title1.strip().lower()
        t2 = title2.strip().lower()
        
        if t1 == t2:
            return 1.0
        
        # Levenshtein距離を計算
        distance = DuplicateDetector._levenshtein_distance(t1, t2)
        
        # 類似度に変換（長い方の文字列長で正規化）
        max_len = max(len(t1), len(t2))
        if max_len == 0:
            return 1.0
        
        similarity = 1.0 - (distance / max_len)
        return max(0.0, similarity)  # 負の値を防ぐ
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        Levenshtein距離を計算する
        
        動的計画法を使用して、2つの文字列間の編集距離を計算する。
        
        Args:
            s1: 文字列1
            s2: 文字列2
            
        Returns:
            Levenshtein距離
        """
        if len(s1) < len(s2):
            return DuplicateDetector._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        # 前の行を保持
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 挿入、削除、置換のコストを計算
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def detect_duplicates(tasks: List[Task]) -> List[Tuple[int, int]]:
        """
        タスクリスト内の重複タスクを検出する
        
        類似度が80%以上のタスクペアを重複として検出する。
        
        Args:
            tasks: タスクリスト
            
        Returns:
            重複タスクのインデックスペアのリスト [(i, j), ...]
            iは保持するタスク、jは統合されるタスク
            
        Requirements: 6.1, 6.3
        """
        duplicates = []
        processed = set()
        
        for i in range(len(tasks)):
            if i in processed:
                continue
            
            for j in range(i + 1, len(tasks)):
                if j in processed:
                    continue
                
                similarity = DuplicateDetector.calculate_similarity(
                    tasks[i].title,
                    tasks[j].title
                )
                
                if similarity >= DuplicateDetector.SIMILARITY_THRESHOLD:
                    duplicates.append((i, j))
                    processed.add(j)  # jは統合されるのでマーク
        
        return duplicates
    
    @staticmethod
    def merge_duplicates(tasks: List[Task]) -> List[Task]:
        """
        重複タスクを統合する
        
        重複として検出されたタスクを統合し、より詳細な説明を持つタスクを優先する。
        
        Args:
            tasks: タスクリスト
            
        Returns:
            重複を統合した新しいタスクリスト
            
        Requirements: 6.1, 6.2, 6.4
        """
        if not tasks:
            return []
        
        # 重複を検出
        duplicates = DuplicateDetector.detect_duplicates(tasks)
        
        if not duplicates:
            return tasks.copy()
        
        # 統合されるタスクのインデックスを収集
        merged_indices = set()
        merge_map = {}  # {統合先インデックス: [統合元インデックス, ...]}
        
        for keep_idx, merge_idx in duplicates:
            merged_indices.add(merge_idx)
            if keep_idx not in merge_map:
                merge_map[keep_idx] = []
            merge_map[keep_idx].append(merge_idx)
        
        # 新しいタスクリストを構築
        result = []
        for i, task in enumerate(tasks):
            if i in merged_indices:
                # このタスクは他のタスクに統合される
                continue
            
            if i in merge_map:
                # このタスクに他のタスクを統合する
                merged_task = DuplicateDetector._merge_task_details(
                    task,
                    [tasks[j] for j in merge_map[i]]
                )
                result.append(merged_task)
            else:
                # 重複なし
                result.append(task)
        
        return result
    
    @staticmethod
    def _merge_task_details(primary: Task, others: List[Task]) -> Task:
        """
        タスクの詳細を統合する
        
        より詳細な説明を持つタスクの情報を優先する。
        
        Args:
            primary: 統合先のタスク
            others: 統合元のタスクリスト
            
        Returns:
            統合されたタスク
            
        Requirements: 6.4
        """
        # 最も詳細な説明を選択
        all_tasks = [primary] + others
        most_detailed = max(all_tasks, key=lambda t: len(t.description))
        
        # 最も詳細なタスクをベースにコピーを作成
        merged = most_detailed.model_copy(deep=True)
        
        # 担当者: 設定されているものを優先
        for task in all_tasks:
            if task.assignee:
                merged.assignee = task.assignee
                break
        
        # 期限: 最も早い期限を優先
        dates = [t.due_date for t in all_tasks if t.due_date]
        if dates:
            merged.due_date = min(dates)
        
        # 優先度: 最も高い優先度を優先
        priority_order = {"high": 3, "medium": 2, "low": 1}
        highest_priority = max(
            all_tasks,
            key=lambda t: priority_order.get(t.priority.value, 0)
        )
        merged.priority = highest_priority.priority
        
        # source_quoteを結合（重複を避ける）
        quotes = []
        seen = set()
        for task in all_tasks:
            quote = task.source_quote.strip()
            if quote and quote not in seen:
                quotes.append(quote)
                seen.add(quote)
        merged.source_quote = "\n---\n".join(quotes)
        
        return merged
