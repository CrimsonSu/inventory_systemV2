import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from erp_database_schema import get_connection, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_items() -> List[Dict]:
    """取得所有項目"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ItemMaster")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
def add_item(item_name: str, item_type: str, category: Optional[str], unit: Optional[str]):
    """新增項目"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO ItemMaster (ItemName, ItemType, Category, Unit)
                VALUES (?, ?, ?, ?)
            ''', (item_name, item_type, category, unit))
            conn.commit()
            logging.info("成功新增項目: %s", item_name)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("唯一性約束失敗: %s", e)
            raise ValueError("項目插入失敗")

# === CRUD Functions for Stock ===
def add_stock(item_id, warehouse_id, quantity, batch_no, expire_date):
    """新增庫存記錄，捕捉唯一性衝突並處理事務回滾"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Stock (ItemID, WarehouseID, Quantity, BatchNo, ExpireDate) VALUES (?, ?, ?, ?, ?)",
                (item_id, warehouse_id, quantity, batch_no, expire_date)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"唯一性衝突錯誤: {e}")
            raise ValueError("庫存記錄插入失敗，可能是唯一性約束衝突")

def get_stocks():
    """取得所有庫存記錄，返回字典格式"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stock")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_stock_by_item(item_id):
    """依 ItemID 查詢庫存記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stock WHERE ItemID = ?", (item_id,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def update_stock(stock_id, **kwargs):
    """更新庫存記錄，允許 0 值並處理安全更新"""
    allowed_fields = {
        "new_item_id": "ItemID",
        "new_warehouse_id": "WarehouseID",
        "new_quantity": "Quantity",
        "new_batch_no": "BatchNo",
        "new_expire_date": "ExpireDate"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return  # 無需更新

    query = f"UPDATE Stock SET {', '.join(fields)} WHERE StockID = ?"
    values.append(stock_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()

def adjust_stock(stock_id, delta_quantity):
    """調整庫存數量，防止負庫存"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Stock SET Quantity = Quantity + ? WHERE StockID = ?",
                (delta_quantity, stock_id)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"庫存調整失敗: {e}")
            raise ValueError("庫存調整失敗，可能導致負庫存")

def delete_stock(stock_id):
    """刪除指定的庫存記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Stock WHERE StockID = ?", (stock_id,))
        conn.commit()

# 測試範例（可以移除或放在 main.py 中）
if __name__ == "__main__":
    # 初始化資料表
    create_tables()

    # 新增測試庫存記錄
    add_stock(item_id=1, warehouse_id=1, quantity=100, batch_no="B001", expire_date="2025-12-31")

    # 查詢所有庫存記錄
    stocks = get_stocks()
    for stock in stocks:
        print(f"StockID: {stock['StockID']}, ItemID: {stock['ItemID']}, WarehouseID: {stock['WarehouseID']}, Quantity: {stock['Quantity']}")

    # 更新測試庫存記錄
    update_stock(stock_id=1, new_quantity=150)

    # 查詢單筆庫存記錄
    stock_records = get_stock_by_item(1)
    for record in stock_records:
        print(f"庫存查詢結果: {record}")

    # 調整庫存數量
    adjust_stock(stock_id=1, delta_quantity=-50)

    # 刪除測試庫存記錄
    delete_stock(1)
    print("已刪除測試庫存記錄")
