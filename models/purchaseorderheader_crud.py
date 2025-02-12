import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

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


# === CRUD Functions ===
def add_purchase_order(supplier_id: int, order_date: str, status: str) -> int:
    """新增採購訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO PurchaseOrderHeader (SupplierID, OrderDate, Status)
                VALUES (?, ?, ?)
            ''', (supplier_id, order_date, status))
            poid = cursor.lastrowid
            conn.commit()
            logging.info("成功新增採購訂單: %d", poid)
            return poid
        except sqlite3.IntegrityError as e:
            logging.error("新增訂單失敗: %s", e)
            raise ValueError("供應商不存在或訂單狀態不正確")

def update_purchase_order(poid: int, status: str):
    """更新採購訂單狀態"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Status FROM PurchaseOrderHeader WHERE POID = ?", (poid,))
        old_status = cursor.fetchone()[0]
        if status == "Open":
            raise ValueError("無法回轉到 Open 狀態")
        cursor.execute("UPDATE PurchaseOrderHeader SET Status = ? WHERE POID = ?", (status, poid))
        conn.commit()
        logging.info("成功更新訂單狀態: POID=%d, Status=%s", poid, status)

def get_purchase_orders() -> List[Dict]:
    """查詢所有訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.POID, h.OrderDate, h.Status, s.SupplierName 
            FROM PurchaseOrderHeader h
            JOIN Supplier s ON h.SupplierID = s.SupplierID
        ''')
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def delete_purchase_order(poid: int):
    """刪除採購訂單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PurchaseOrderHeader WHERE POID = ?", (poid,))
        conn.commit()
        logging.info("成功刪除訂單: %d", poid)
