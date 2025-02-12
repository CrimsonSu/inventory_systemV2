import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
VALID_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}


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

# === CRUD Functions for ProductionOrderHeader ===

def add_production_order(product_id: int, order_date: str, status: str):
    """新增生產訂單"""
    if status not in VALID_STATUSES:
        raise ValueError(f"無效狀態: {status}, 合法值為 {VALID_STATUSES}")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM ItemMaster WHERE ItemID = ?", (product_id,))
        if not cursor.fetchone():
            raise ValueError(f"ProductID {product_id} 不存在")

        try:
            cursor.execute(
                '''
                INSERT INTO ProductionOrderHeader (ProductID, OrderDate, Status, IsDeleted)
                VALUES (?, ?, ?, 0)
                ''', (product_id, order_date, status)
            )
            conn.commit()
            logging.info("成功新增生產訂單: ProductID=%d, OrderDate=%s", product_id, order_date)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("插入失敗 (ProductID=%d): %s", product_id, e)
            raise

def get_production_orders(offset: int = 0, limit: int = 100) -> List[Dict]:
    """取得所有生產訂單，支援分頁"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT h.*, i.ItemName
            FROM ProductionOrderHeader h
            JOIN ItemMaster i ON h.ProductID = i.ItemID
            WHERE h.IsDeleted = 0
            LIMIT ? OFFSET ?
            ''', (limit, offset)
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_production_order_by_id(production_order_id: int) -> Optional[Dict]:
    """依 ProductionOrderID 查詢單筆生產訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, i.ItemName AS ProductName
            FROM ProductionOrderHeader h
            JOIN ItemMaster i ON h.ProductID = i.ItemID
            WHERE h.ProductionOrderID = ?
        ''', (production_order_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

def update_production_order(production_order_id: int, **kwargs):
    """更新生產訂單"""
    allowed_fields = {
        "product_id": "ProductID",
        "status": "Status",
        "order_date": "OrderDate"
    }

    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            if param == "status" and kwargs[param] not in VALID_STATUSES:
                raise ValueError(f"無效狀態: {kwargs[param]}, 合法值為 {VALID_STATUSES}")

            if param == "product_id":
                cursor = get_connection().cursor()
                cursor.execute("SELECT 1 FROM ItemMaster WHERE ItemID = ?", (kwargs[param],))
                if not cursor.fetchone():
                    raise ValueError(f"ProductID {kwargs[param]} 不存在")

            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return  # 無需更新

    query = f"UPDATE ProductionOrderHeader SET {', '.join(fields)} WHERE ProductionOrderID = ?"
    values.append(production_order_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, tuple(values))
            conn.commit()
            logging.info("成功更新生產訂單: ProductionOrderID=%d", production_order_id)
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("更新失敗: %s", e)
            raise

def delete_production_order(production_order_id: int):
    """軟刪除指定的生產訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE ProductionOrderHeader SET IsDeleted = 1 WHERE ProductionOrderID = ?",
                (production_order_id,)
            )
            conn.commit()
            logging.info("已刪除生產訂單: ProductionOrderID=%d", production_order_id)
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("刪除失敗: %s", e)
            raise

# === 測試代碼 ===
if __name__ == "__main__":
    # 初始化資料表
    create_tables()

    # 新增測試產品記錄（確保 ProductID 存在）
    add_item("測試產品", "成品", "食品", "箱")
    items = get_items()
    print("所有產品:", items)

    # 新增測試生產訂單
    add_production_order(product_id=1, order_date="2025-02-10", status="Pending")

    # 查詢生產訂單
    orders = get_production_orders()
    print("所有生產訂單:", orders)

    # 更新測試訂單
    update_production_order(1, status="In Progress")

    # 查詢單筆訂單
    order = get_production_order_by_id(1)
    print("更新後的訂單:", order)

    # 刪除測試訂單
    delete_production_order(1)
    print("已刪除測試訂單")
