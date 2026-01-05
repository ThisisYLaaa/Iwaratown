#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动获取Git提交记录并更新update.md文件
"""

import os
import re
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple

class GitUpdateLogger:
    def __init__(self, update_md_path: str):
        """
        初始化Git更新日志记录器
        
        Args:
            update_md_path: update.md文件的路径
        """
        self.update_md_path = update_md_path
        self.repo_path = os.path.dirname(update_md_path)
        
    def run_git_command(self, command: List[str]) -> str:
        """
        运行Git命令并返回输出
        
        Args:
            command: Git命令列表
        
        Returns:
            Git命令的输出
        """
        result = subprocess.run(
            ['git'] + command,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode != 0:
            raise Exception(f"Git命令执行失败: {' '.join(command)}\n错误: {result.stderr}")
        
        return result.stdout.strip()
    
    def get_current_branch(self) -> str:
        """
        获取当前Git分支名称
        
        Returns:
            当前分支名称
        """
        return self.run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
    
    def get_git_commits(self, since_date: str = "") -> List[Dict[str, str]]:
        """
        获取Git提交记录
        
        Args:
            since_date: 只获取该日期之后的提交记录，格式为YYYY-MM-DD
        
        Returns:
            提交记录列表，每个记录包含哈希、作者、日期、分支和提交信息
        """
        # 构建Git命令
        command = [
            'log',
            '--pretty=format:%h %an %ad %s',
            '--date=short'
        ]
        
        if since_date:
            command.extend(['--since', since_date])
        
        # 运行命令获取输出
        output = self.run_git_command(command)
        
        # 获取当前分支名称
        current_branch = self.get_current_branch()
        
        # 解析输出
        commits = []
        for line in output.split('\n'):
            if not line:
                continue
            
            # 匹配提交记录格式：哈希 作者 日期 [分支] 提交信息
            match = re.match(r'^([0-9a-f]{7})\s+([^\s]+)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\s+\[(.*?)\]\s+(.+)$', line)
            if not match:
                # 尝试匹配旧格式：哈希 作者 日期 提交信息
                match = re.match(r'^([0-9a-f]{7})\s+([^\s]+)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\s+(.+)$', line)
            if match:
                commits.append({
                    'hash': match.group(1),
                    'author': match.group(2),
                    'date': match.group(3),
                    'branch': current_branch,
                    'message': match.group(4)
                })
        
        return commits
    
    def read_update_md(self) -> Tuple[str, Dict[str, List[str]]]:
        """
        读取现有的update.md文件
        
        Returns:
            元组，包含文件头部和日期到更新记录的映射
        """
        header = ""
        date_to_records = {}
        current_date = None
        
        if not os.path.exists(self.update_md_path):
            # 如果文件不存在，返回默认头部
            return ("# 更新日志\n\n## 日志书写规范\n\n1. **版本号记录规则**：\n   - 只在**更新版本号的那次更新**后记录新版本号\n   - 之后的**日常更新无需重复记录版本号**\n   - 直至**下一次版本号更新时**再进行记录\n\n2. **日期格式**：使用 `YYYY-MM-DD` 格式，如 `2025-12-27`\n\n3. **内容格式**：\n   - 每条更新记录以 `-` 开头\n   - 简短描述更新内容，使用中文\n   - 对于重大更新，可添加 `[重磅更新]` 标记\n\n4. **排序规则**：更新记录按**日期从新到旧**排列\n\n5. **提交记录**：\n   - 包含 Git 提交哈希、作者、日期和提交信息\n   - 格式：`- <哈希> <作者> <日期> <提交信息>`\n\n", date_to_records)
        
        with open(self.update_md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析文件
        in_header = True
        for line in lines:
            line_strip = line.strip()
            
            if in_header:
                if line_strip.startswith('## 20'):
                    # 开始日期部分，结束头部
                    in_header = False
                    current_date = line_strip[3:]
                    date_to_records[current_date] = []
                else:
                    header += line
            else:
                if line_strip.startswith('## 20'):
                    # 新的日期部分
                    current_date = line_strip[3:]
                    date_to_records[current_date] = []
                elif line_strip and current_date:
                    # 更新记录
                    date_to_records[current_date].append(line.rstrip())
        
        return header, date_to_records
    
    def write_update_md(self, header: str, date_to_records: Dict[str, List[str]]) -> None:
        """
        写入更新后的update.md文件
        
        Args:
            header: 文件头部
            date_to_records: 日期到更新记录的映射
        """
        with open(self.update_md_path, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write(header)
            
            # 按日期从新到旧排序
            sorted_dates = sorted(date_to_records.keys(), reverse=True)
            
            # 写入更新记录
            for date in sorted_dates:
                records = date_to_records[date]
                if records:
                    f.write(f"## {date}\n")
                    for record in records:
                        f.write(f"{record}\n")
                    f.write("\n")
    
    def get_latest_date_in_update_md(self, date_to_records: Dict[str, List[str]]) -> str:
        """
        获取update.md文件中最新的日期
        
        Args:
            date_to_records: 日期到更新记录的映射
        
        Returns:
            最新的日期，格式为YYYY-MM-DD
        """
        if not date_to_records:
            return "2020-01-01"  # 默认从2020年开始
        
        return max(date_to_records.keys())
    
    def is_commit_in_records(self, commit: Dict[str, str], records: List[str]) -> bool:
        """
        检查提交记录是否已经存在于更新记录中
        
        Args:
            commit: Git提交记录
            records: 更新记录列表
        
        Returns:
            如果已经存在返回True，否则返回False
        """
        commit_hash = commit['hash']
        for record in records:
            if commit_hash in record:
                return True
        return False
    
    def update_log(self) -> None:
        """
        更新update.md文件，添加新的Git提交记录
        """
        # 读取现有文件
        header, date_to_records = self.read_update_md()
        
        # 获取最新日期
        latest_date = self.get_latest_date_in_update_md(date_to_records)
        
        # 获取Git提交记录（从最新日期之后开始）
        commits = self.get_git_commits(latest_date)
        
        if not commits:
            print("没有新的Git提交记录需要添加到update.md")
            return
        
        # 按日期分组提交记录
        commit_by_date = {}
        for commit in commits:
            date = commit['date']
            if date not in commit_by_date:
                commit_by_date[date] = []
            commit_by_date[date].append(commit)
        
        # 添加新的提交记录到date_to_records
        new_records_added = 0
        for date, date_commits in commit_by_date.items():
            if date not in date_to_records:
                date_to_records[date] = []
            
            existing_records = date_to_records[date]
            
            for commit in date_commits:
                if not self.is_commit_in_records(commit, existing_records):
                    # 格式：- <哈希> <作者> <日期> <分支> <提交信息>
                    new_record = f"- {commit['hash']} {commit['author']} {commit['date']} [{commit['branch']}] {commit['message']}"
                    date_to_records[date].append(new_record)
                    new_records_added += 1
        
        if new_records_added > 0:
            # 写入更新后的文件
            self.write_update_md(header, date_to_records)
            print(f"已成功添加 {new_records_added} 条新的提交记录到update.md")
        else:
            print("没有新的Git提交记录需要添加到update.md")
    
    def add_manual_record(self, date: str, content: str) -> None:
        """
        手动添加更新记录
        
        Args:
            date: 日期，格式为YYYY-MM-DD
            content: 更新内容
        """
        # 读取现有文件
        header, date_to_records = self.read_update_md()
        
        if date not in date_to_records:
            date_to_records[date] = []
        
        # 检查记录是否已存在
        new_record = f"- {content}"
        if new_record not in date_to_records[date]:
            date_to_records[date].append(new_record)
            # 写入更新后的文件
            self.write_update_md(header, date_to_records)
            print(f"已成功添加手动记录到update.md")
        else:
            print("该记录已存在于update.md中")

def main():
    """
    主函数
    """
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    update_md_path = os.path.join(script_dir, 'update.md')
    
    logger = GitUpdateLogger(update_md_path)
    
    # 更新日志
    logger.update_log()

if __name__ == "__main__":
    main()
