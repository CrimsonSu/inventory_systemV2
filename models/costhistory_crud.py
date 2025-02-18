import logging
from models.erp_database_schema import get_connection
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)

def add_cost_history(product_name: str, price: float):
    """
    新增一筆 CostHistory 紀錄，product_name 為產品名稱，price 為本次更新價格。
    UpdateTime 欄位採用預設的 CURRENT_TIMESTAMP 自動填入。
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO CostHistory (ProductName, Price)
            VALUES (?, ?)
        ''', (product_name, price))
        conn.commit()
        logging.info("成功新增 CostHistory 記錄：%s, 價格=%.2f", product_name, price)

def get_cost_history(product_name: Optional[str] = None) -> List[Dict]:
    """取得某產品的歷史價格記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT CostHistoryID, ProductName, Price, UpdateTime
            FROM CostHistory
        """
        params = []

        if product_name:
            query += " WHERE ProductName LIKE ?"
            params.append(f"%{product_name}%")

        query += " ORDER BY UpdateTime DESC"

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
