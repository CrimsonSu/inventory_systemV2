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
def add_shipment_detail(shipment_id: int, item_id: int, quantity: float):
    """新增出貨明細"""
    if quantity <= 0:
        raise ValueError("數量必須大於零")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO ShipmentDetail (ShipmentID, ItemID, Quantity)
                VALUES (?, ?, ?)
            ''', (shipment_id, item_id, quantity))
            conn.commit()
            logging.info("成功新增出貨明細")
        except sqlite3.IntegrityError as e:
            logging.error("新增出貨明細失敗: %s", e)
            raise ValueError("出貨單或項目不存在") from e

def get_shipment_details(shipment_id: int) -> list:
    """取得指定出貨單的明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ShipmentDetail WHERE ShipmentID = ?", (shipment_id,))
        return cursor.fetchall()

def update_shipment_detail(shipment_detail_id: int, quantity: float):
    """更新出貨明細"""
    if quantity <= 0:
        raise ValueError("數量必須大於零")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE ShipmentDetail
            SET Quantity = ?
            WHERE ShipmentDetailID = ?
        ''', (quantity, shipment_detail_id))
        conn.commit()

def delete_shipment_detail(shipment_detail_id: int):
    """刪除出貨明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ShipmentDetail WHERE ShipmentDetailID = ?", (shipment_detail_id,))
        conn.commit()

# === 測試 ===
if __name__ == "__main__":
    add_shipment_detail(shipment_id=1, item_id=1, quantity=10.0)
    print("新增出貨明細:", get_shipment_details(shipment_id=1))
    update_shipment_detail(shipment_detail_id=1, quantity=5.0)
    print("更新後出貨明細:", get_shipment_details(shipment_id=1))
    delete_shipment_detail(shipment_detail_id=1)
    print("刪除後出貨明細:", get_shipment_details(shipment_id=1))
