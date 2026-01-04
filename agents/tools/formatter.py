"""
議事録フォーマッター

議事録をMarkdown形式に変換、またはMarkdownから復元する機能を提供する。
Requirements: 3.1, 3.2, 3.3, 3.4, 5.2, 5.4
"""

import re
from datetime import datetime
from typing import List

from agents.models.minutes import ActionItem, Minutes


class MinutesFormatter:
    """
    議事録フォーマッター
    
    議事録とMarkdown形式の相互変換を行う。
    """
    
    @staticmethod
    def to_markdown(minutes: Minutes) -> str:
        """
        議事録をMarkdown形式に変換する
        
        Requirements: 3.1, 3.2, 3.3, 2.5
        
        Args:
            minutes: 議事録オブジェクト
            
        Returns:
            Markdown形式の文字列
        """
        lines = []
        
        # H1見出し: タイトル (Requirement 3.1)
        lines.append(f"# {minutes.title}")
        lines.append("")
        
        # H2見出し: 日時 (Requirement 3.2)
        lines.append("## 日時")
        lines.append(minutes.date.strftime("%Y-%m-%d %H:%M"))
        lines.append("")
        
        # H2見出し: 参加者 (Requirement 3.2, 2.5)
        lines.append("## 参加者")
        if minutes.participants:
            for participant in minutes.participants:
                lines.append(f"- {participant}")
        else:
            # 参加者が空の場合は「不明」を出力 (Requirement 2.5)
            lines.append("不明")
        lines.append("")
        
        # H2見出し: 議題 (Requirement 3.2)
        lines.append("## 議題")
        if minutes.agenda:
            for item in minutes.agenda:
                lines.append(f"- {item}")
        else:
            lines.append("なし")
        lines.append("")
        
        # H2見出し: 議論内容 (Requirement 3.2)
        lines.append("## 議論内容")
        lines.append(minutes.discussion)
        lines.append("")
        
        # H2見出し: 決定事項 (Requirement 3.2)
        lines.append("## 決定事項")
        if minutes.decisions:
            for decision in minutes.decisions:
                lines.append(f"- {decision}")
        else:
            lines.append("なし")
        lines.append("")
        
        # H2見出し: アクションアイテム (Requirement 3.2, 3.3)
        lines.append("## アクションアイテム")
        if minutes.action_items:
            for action in minutes.action_items:
                # チェックボックス形式で出力 (Requirement 3.3)
                checkbox = "[x]" if action.completed else "[ ]"
                line = f"- {checkbox} {action.description}"
                
                # 担当者と期限を追加
                details = []
                if action.assignee:
                    details.append(f"担当: {action.assignee}")
                if action.due_date:
                    details.append(f"期限: {action.due_date}")
                
                if details:
                    line += f" ({', '.join(details)})"
                
                lines.append(line)
        else:
            lines.append("なし")
        lines.append("")
        
        return "\n".join(lines)

    @staticmethod
    def from_markdown(markdown: str) -> Minutes:
        """
        Markdown形式の文字列から議事録オブジェクトを復元する
        
        Requirements: 3.4, 5.4
        
        Args:
            markdown: Markdown形式の議事録文字列
            
        Returns:
            議事録オブジェクト
            
        Raises:
            ValueError: パースに失敗した場合
        """
        lines = markdown.strip().split("\n")
        
        # タイトルを抽出 (H1見出し)
        title_match = re.search(r"^# (.+)$", markdown, re.MULTILINE)
        if not title_match:
            raise ValueError("タイトル（H1見出し）が見つかりません")
        title = title_match.group(1).strip()
        
        # セクションを抽出するヘルパー関数
        def extract_section(section_name: str) -> str:
            """指定されたH2セクションの内容を抽出"""
            pattern = rf"^## {re.escape(section_name)}\s*\n(.*?)(?=^## |\Z)"
            match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
            return ""
        
        # 日時を抽出
        date_str = extract_section("日時")
        if not date_str:
            raise ValueError("日時セクションが見つかりません")
        
        try:
            # YYYY-MM-DD HH:MM形式をパース
            date = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(f"日時のパースに失敗しました: {date_str}")
        
        # 参加者を抽出
        participants_str = extract_section("参加者")
        participants: List[str] = []
        if participants_str and participants_str != "不明":
            for line in participants_str.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    participants.append(line[2:].strip())
        
        # 議題を抽出
        agenda_str = extract_section("議題")
        agenda: List[str] = []
        if agenda_str and agenda_str != "なし":
            for line in agenda_str.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    agenda.append(line[2:].strip())
        
        # 議論内容を抽出
        discussion = extract_section("議論内容")
        if not discussion:
            raise ValueError("議論内容セクションが見つかりません")
        
        # 決定事項を抽出
        decisions_str = extract_section("決定事項")
        decisions: List[str] = []
        if decisions_str and decisions_str != "なし":
            for line in decisions_str.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    decisions.append(line[2:].strip())
        
        # アクションアイテムを抽出
        action_items_str = extract_section("アクションアイテム")
        action_items: List[ActionItem] = []
        if action_items_str and action_items_str != "なし":
            for line in action_items_str.split("\n"):
                line = line.strip()
                # チェックボックス形式をパース: - [ ] または - [x]
                checkbox_match = re.match(r"^- \[([ x])\] (.+)$", line)
                if checkbox_match:
                    completed = checkbox_match.group(1) == "x"
                    rest = checkbox_match.group(2).strip()
                    
                    # 担当者と期限を抽出
                    assignee = None
                    due_date = None
                    
                    # (担当: xxx, 期限: yyyy-mm-dd) 形式を抽出
                    details_match = re.search(r"\((.+)\)$", rest)
                    if details_match:
                        description = rest[:details_match.start()].strip()
                        details = details_match.group(1)
                        
                        # 担当者を抽出
                        assignee_match = re.search(r"担当:\s*([^,)]+)", details)
                        if assignee_match:
                            assignee = assignee_match.group(1).strip()
                        
                        # 期限を抽出
                        due_date_match = re.search(r"期限:\s*(\d{4}-\d{2}-\d{2})", details)
                        if due_date_match:
                            due_date = due_date_match.group(1).strip()
                    else:
                        description = rest
                    
                    action_items.append(ActionItem(
                        description=description,
                        assignee=assignee,
                        due_date=due_date,
                        completed=completed,
                    ))
        
        return Minutes(
            title=title,
            date=date,
            participants=participants,
            agenda=agenda,
            discussion=discussion,
            decisions=decisions,
            action_items=action_items,
        )

    @staticmethod
    def generate_filename(minutes: Minutes) -> str:
        """
        議事録からファイル名を生成する
        
        Requirements: 5.2
        
        ファイル名形式: {YYYY-MM-DD}_{title-slug}.md
        
        Args:
            minutes: 議事録オブジェクト
            
        Returns:
            ファイル名（拡張子.md付き）
        """
        # 日付部分を生成 (YYYY-MM-DD)
        date_part = minutes.date.strftime("%Y-%m-%d")
        
        # タイトルをスラッグ化
        # 1. 小文字に変換
        slug = minutes.title.lower()
        
        # 2. 日本語文字、英数字、ハイフン、アンダースコア以外を削除
        # 日本語文字を保持しつつ、特殊文字を削除
        slug = re.sub(r'[^\w\s-]', '', slug, flags=re.UNICODE)
        
        # 3. 空白をハイフンに変換
        slug = re.sub(r'[\s_]+', '-', slug)
        
        # 4. 連続するハイフンを1つに
        slug = re.sub(r'-+', '-', slug)
        
        # 5. 前後のハイフンを削除
        slug = slug.strip('-')
        
        # 6. 空の場合はデフォルト値
        if not slug:
            slug = "untitled"
        
        # ファイル名を生成
        return f"{date_part}_{slug}.md"
