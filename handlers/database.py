import sqlite3
from datetime import datetime
import pytz
from typing import List, Optional, Dict, Any

TIMEZONE = pytz.timezone('Asia/Shanghai')

class Database:
    def __init__(self, db_path: str = 'sign_data.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 启用行工厂模式
        self._create_tables()

    def _create_tables(self):
        """初始化所有数据表"""
        with self.conn:
            # 用户基础数据表
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    total_days INTEGER DEFAULT 0,
                    consecutive_days INTEGER DEFAULT 0,
                    last_sign TIMESTAMP,
                    energy_total INTEGER DEFAULT 0,
                    consecutive_bonus INTEGER DEFAULT 0
                )
            ''')

            # 每日签到记录表
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_sign (
                    date DATE PRIMARY KEY,
                    user_ids TEXT
                )
            ''')

            # 下班打卡记录表
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS off_records (
                    user_id TEXT,
                    off_date DATE,
                    message TEXT,
                    PRIMARY KEY (user_id, off_date)
                )
            ''')

    # 签到相关方法
    def get_daily_sign(self, date: str) -> List[str]:
        """获取指定日期的签到用户列表"""
        cursor = self.conn.execute(
            'SELECT user_ids FROM daily_sign WHERE date = ?',
            (date,)
        )
        result = cursor.fetchone()
        return result['user_ids'].split(',') if result and result['user_ids'] else []

    def update_daily_sign(self, date: str, user_id: str):
        """更新每日签到记录"""
        existing = self.get_daily_sign(date)
        if user_id not in existing:
            updated = ','.join(existing + [user_id]) if existing else user_id
            self.conn.execute(
                'INSERT OR REPLACE INTO daily_sign VALUES (?, ?)',
                (date, updated)
            )
            self.conn.commit()

    # 用户数据操作
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户完整数据"""
        cursor = self.conn.execute(
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def update_user(self, user_data: Dict[str, Any]):
        """更新用户数据"""
        self.conn.execute('''
            INSERT OR REPLACE INTO users 
            VALUES (:user_id, :username, :total_days, :consecutive_days,
                    :last_sign, :energy_total, :consecutive_bonus)
        ''', user_data)
        self.conn.commit()

    # 下班打卡功能
    def record_offline(self, user_id: str, message: str):
        """记录下班打卡"""
        today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        self.conn.execute('''
            INSERT OR IGNORE INTO off_records VALUES (?, ?, ?)
        ''', (user_id, today, message))
        self.conn.commit()

    def get_today_off_status(self, user_id: str) -> Optional[str]:
        """获取今日下班打卡状态"""
        today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        cursor = self.conn.execute('''
            SELECT message FROM off_records
            WHERE user_id = ? AND off_date = ?
        ''', (user_id, today))
        result = cursor.fetchone()
        return result['message'] if result else None

    # 管理功能
    def reset_data(self):
        """清空所有数据（开发环境用）"""
        with self.conn:
            self.conn.execute('DELETE FROM users')
            self.conn.execute('DELETE FROM daily_sign')
            self.conn.execute('DELETE FROM off_records')

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

# 使用示例
if __name__ == '__main__':
    db = Database()
    
    # 测试签到功能
    test_user = {
        'user_id': '123',
        'username': '测试用户',
        'total_days': 1,
        'consecutive_days': 1,
        'last_sign': datetime.now().isoformat(),
        'energy_total': 20,
        'consecutive_bonus': 0
    }
    db.update_user(test_user)
    db.update_daily_sign('2023-09-15', '123')
    
    # 测试下班打卡
    db.record_offline('123', '测试语录')
    print(db.get_today_off_status('123'))  # 输出: 测试语录
    
    db.close()