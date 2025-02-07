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
    
# === CRUD Functions for StockMovement ===

def add_stock_movement(item_id: int, movement_type: str, quantity: float, movement_date: str, batch_no: str):
    """新增庫存移動記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO StockMovement (ItemID, MovementType, Quantity, MovementDate, BatchNo)
                VALUES (?, ?, ?, ?, ?)
            ''', (item_id, movement_type, quantity, movement_date, batch_no))
            conn.commit()
            logging.info("成功新增庫存移動記錄")
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("唯一性約束失敗: %s", e)
            raise ValueError("庫存移動記錄插入失敗")

def get_stock_movements() -> List[Dict]:
    """取得所有庫存移動記錄，返回字典格式"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM StockMovement")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def delete_stock_movement(movement_id: int):
    """刪除指定的庫存移動記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM StockMovement WHERE MovementID = ?", (movement_id,))
        if cursor.rowcount == 0:
            logging.warning("刪除失敗，移動記錄 ID 不存在: MovementID = %d", movement_id)
        else:
            conn.commit()
            logging.info("已刪除庫存移動記錄: MovementID = %d", movement_id)

def check_sqlite_version(min_version: str = "3.30.0"):
    """檢查 SQLite 版本，確保符合最低版本要求"""
    current_version = sqlite3.sqlite_version
    logging.info("目前 SQLite 版本: %s", current_version)

    # 將版本字串轉換為數字元組進行比較
    def version_to_tuple(version: str):
        return tuple(map(int, version.split(".")))

    if version_to_tuple(current_version) < version_to_tuple(min_version):
        raise RuntimeError(f"SQLite 版本過低，請升級到至少 {min_version}")

# 測試範例
if __name__ == "__main__":
    # 初始化資料表
    create_tables()

    # 檢查 SQLite 版本
    check_sqlite_version()

    # 新增測試庫存移動記錄
    add_stock_movement(item_id=1, movement_type="IN", quantity=100, movement_date="2025-02-01", batch_no="B001")

    # 查詢所有庫存移動記錄
    movements = get_stock_movements()
    for movement in movements:
        print(f"MovementID: {movement['MovementID']}, ItemID: {movement['ItemID']}, MovementType: {movement['MovementType']}, Quantity: {movement['Quantity']}")
