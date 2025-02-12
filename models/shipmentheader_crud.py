import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

VALID_SHIPMENT_STATUSES = {"pending", "shipped", "canceled"}
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
def add_shipment(order_id: int, shipment_date: str, status: str):
    """新增出貨單"""
    # 日期格式驗證
    try:
        datetime.strptime(shipment_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("無效的日期格式，應為 YYYY-MM-DD")

    # 狀態驗證
    if status not in VALID_SHIPMENT_STATUSES:
        raise ValueError(f"無效的狀態: {status}")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO ShipmentHeader (OrderID, ShipmentDate, Status)
                VALUES (?, ?, ?)
            ''', (order_id, shipment_date, status))
            conn.commit()
            logging.info("成功新增出貨單")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logging.error("新增出貨單失敗: %s", e)
            raise ValueError("訂單不存在或數據格式錯誤") from e

def get_shipments() -> list:
    """取得所有出貨單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ShipmentHeader")
        return cursor.fetchall()

ALLOWED_HEADER_FIELDS = {'ShipmentDate', 'Status', 'TrackingNumber'}

def update_shipment(shipment_id: int, **kwargs):
    invalid_fields = set(kwargs.keys()) - ALLOWED_HEADER_FIELDS
    if invalid_fields:
        raise ValueError(f"非法字段: {', '.join(invalid_fields)}")
    
    # SQL 語句執行更新
    updates = ", ".join(f"{key} = ?" for key in kwargs.keys())
    params = list(kwargs.values()) + [shipment_id]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE ShipmentHeader
            SET {updates}
            WHERE ShipmentID = ?
        ''', params)
        conn.commit()

def delete_shipment(shipment_id: int):
    """刪除出貨單"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ShipmentHeader WHERE ShipmentID = ?", (shipment_id,))
        conn.commit()

# === 測試 ===
if __name__ == "__main__":
    create_tables()
    shipment_id = add_shipment(order_id=1, shipment_date="2025-02-11", status="pending")
    print("新增出貨單:", get_shipments())
    update_shipment(shipment_id, status="shipped")
    print("更新後出貨單:", get_shipments())
    delete_shipment(shipment_id)
    print("刪除後出貨單:", get_shipments())
