# models/costhistory_crud.py
import logging
from models.erp_database_schema import get_connection

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
