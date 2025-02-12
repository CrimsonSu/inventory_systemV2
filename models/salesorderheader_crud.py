import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables
from models.customer_crud import add_customer

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


# === CRUD Functions for SalesOrderHeader ===

VALID_STATUSES = {"Pending", "Shipped", "Cancelled", "Delivered"}

def add_sales_order(customer_id: int, order_date: str, status: str):
    """新增銷售訂單記錄"""
    if status not in VALID_STATUSES:
        raise ValueError(f"無效狀態: {status}, 合法值為 {VALID_STATUSES}")

    with get_connection() as conn:
        cursor = conn.cursor()
        # 新增外鍵檢查
        cursor.execute("SELECT 1 FROM Customer WHERE CustomerID = ?", (customer_id,))
        if not cursor.fetchone():
            raise ValueError(f"CustomerID {customer_id} 不存在")

        try:
            cursor.execute('''
                INSERT INTO SalesOrderHeader (CustomerID, OrderDate, Status)
                VALUES (?, ?, ?)
            ''', (customer_id, order_date, status))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("新增訂單失敗: %s", e)
            raise ValueError("資料庫操作失敗") from e



def get_sales_orders() -> List[Dict]:
    """取得所有銷售訂單記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SalesOrderHeader")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_sales_order_by_id(order_id: int) -> Optional[Dict]:
    """依 OrderID 查詢銷售訂單記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SalesOrderHeader WHERE OrderID = ?", (order_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

def update_sales_order(order_id: int, **kwargs):
    """更新銷售訂單記錄，允許安全更新"""
    allowed_fields = {
        "customer_id": "CustomerID",
        "order_date": "OrderDate",
        "status": "Status"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return  # 無需更新

    query = f"UPDATE SalesOrderHeader SET {', '.join(fields)} WHERE OrderID = ?"
    values.append(order_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, tuple(values))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("更新訂單失敗: %s", e)
            raise ValueError("資料庫操作失敗") from e


def delete_sales_order(order_id: int):
    """刪除指定的銷售訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # 自動刪除關聯明細
            cursor.execute("DELETE FROM SalesOrderDetail WHERE OrderID = ?", (order_id,))
            cursor.execute("DELETE FROM SalesOrderHeader WHERE OrderID = ?", (order_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("刪除訂單失敗: %s", e)
            raise ValueError("資料庫操作失敗") from e




# === 測試代碼 ===
if __name__ == "__main__":
    # 初始化資料表
    create_tables()

    # 新增測試客戶
    add_customer(customer_name="測試客戶", address="地址", contact_person="聯絡人", phone="0912345678", email="test@example.com")

    # 新增訂單
    add_sales_order(customer_id=1, order_date="2025-02-09", status="Pending")

    # 查詢訂單
    orders = get_sales_orders()
    print("所有訂單:", orders)