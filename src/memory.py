"""
记忆系统模块 - 实现会话历史与用户数据持久化（功能亮点5）
支持会话ID隔离（功能亮点6）
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class ConversationMemory:
    """会话记忆管理器 - 支持持久化和会话隔离"""
    
    def __init__(self, memory_dir: str = "D:\\generated_outputs\\dev_team\\memory"):
        """初始化记忆系统"""
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 初始化SQLite数据库
        self.db_path = os.path.join(memory_dir, "conversation_memory.db")
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建会话表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            last_active TIMESTAMP,
            user_context TEXT
        )
        ''')
        
        # 创建消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            agent_name TEXT,
            FOREIGN KEY (session_id) REFERENCES conversations (session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str, user_context: str = "") -> bool:
        """创建新会话"""
        if self.get_session(session_id):
            return False  # 会话已存在
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO conversations (session_id, created_at, last_active, user_context)
        VALUES (?, ?, ?, ?)
        ''', (session_id, datetime.now(), datetime.now(), user_context))
        
        conn.commit()
        conn.close()
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM conversations WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "session_id": row[0],
                "created_at": row[1],
                "last_active": row[2],
                "user_context": row[3]
            }
        return None
    
    def add_message(self, session_id: str, role: str, content: str, agent_name: str = "") -> bool:
        """添加消息到会话"""
        # 确保会话存在
        if not self.get_session(session_id):
            self.create_session(session_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 添加消息
        cursor.execute('''
        INSERT INTO messages (session_id, role, content, timestamp, agent_name)
        VALUES (?, ?, ?, ?, ?)
        ''', (session_id, role, content, datetime.now(), agent_name))
        
        # 更新最后活跃时间
        cursor.execute('''
        UPDATE conversations SET last_active = ? WHERE session_id = ?
        ''', (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话的所有消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT role, content, timestamp, agent_name FROM messages
        WHERE session_id = ? ORDER BY timestamp ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
                "agent_name": row[3]
            }
            for row in rows
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """清空会话数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除消息
        cursor.execute('''
        DELETE FROM messages WHERE session_id = ?
        ''', (session_id,))
        
        # 删除会话
        cursor.execute('''
        DELETE FROM conversations WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_sessions(self) -> List[str]:
        """获取所有会话ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT session_id FROM conversations ORDER BY last_active DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]