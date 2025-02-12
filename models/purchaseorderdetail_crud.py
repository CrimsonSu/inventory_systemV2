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
def add_purchase_order_detail(poid: int, item_id: int, ordered_qty: float, price: float):
    """新增採購訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO PurchaseOrderDetail (POID, ItemID, OrderedQty, Price)
            VALUES (?, ?, ?, ?)
        ''', (poid, item_id, ordered_qty, price))
        conn.commit()
        logging.info("成功新增訂單明細: POID=%d, ItemID=%d", poid, item_id)

def update_purchase_order_detail(podetail_id: int, received_qty: float):
    """更新訂單明細的收貨量"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE PurchaseOrderDetail SET ReceivedQty = ? WHERE PODetailID = ?", (received_qty, podetail_id))
        conn.commit()
        logging.info("成功更新訂單明細: PODetailID=%d", podetail_id)

def get_purchase_order_details(poid: int) -> List[Dict]:
    """查詢訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.PODetailID, d.OrderedQty, d.ReceivedQty, i.ItemName 
            FROM PurchaseOrderDetail d
            JOIN ItemMaster i ON d.ItemID = i.ItemID
            WHERE d.POID = ?
        ''', (poid,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def delete_purchase_order_detail(podetail_id: int):
    """刪除訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PurchaseOrderDetail WHERE PODetailID = ?", (podetail_id,))
        conn.commit()
        logging.info("成功刪除訂單明細: %d", podetail_id)

