import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables
from models.productionorderheader_crud import add_production_order


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# Valid ItemType for production
VALID_ITEM_TYPE = "原料"

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


def add_production_order_detail(production_order_id: int, item_id: int, planned_qty: float, actual_qty: Optional[float] = None):
    """新增生產訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # 外鍵檢查
            cursor.execute("SELECT 1 FROM ProductionOrderHeader WHERE ProductionOrderID = ?", (production_order_id,))
            if not cursor.fetchone():
                raise ValueError(f"ProductionOrderID {production_order_id} 不存在")

            cursor.execute("SELECT ItemType FROM ItemMaster WHERE ItemID = ?", (item_id,))
            item_type = cursor.fetchone()
            if not item_type or item_type[0] != VALID_ITEM_TYPE:
                raise ValueError(f"ItemID {item_id} 不是原料類型")

            # 業務邏輯驗證
            if planned_qty <= 0:
                raise ValueError("計劃數量必須為正數")

            # 插入資料
            cursor.execute(
                '''INSERT INTO ProductionOrderDetail (ProductionOrderID, ItemID, PlannedQty, ActualQty)
                   VALUES (?, ?, ?, ?)''',
                (production_order_id, item_id, planned_qty, actual_qty)
            )
            conn.commit()
            logging.info("成功新增生產訂單明細: ProductionOrderID=%d, ItemID=%d", production_order_id, item_id)

        except sqlite3.IntegrityError as e:
            conn.rollback()
            error_msg = str(e)
            if "FOREIGN KEY" in error_msg:
                logging.error("外鍵約束失敗: %s", error_msg)
                raise ValueError("生產訂單或原料不存在") from e
            elif "UNIQUE" in error_msg:
                logging.error("唯一性約束失敗: 同一生產訂單中原料重複")
                raise ValueError("原料已存在於此生產訂單") from e
            else:
                raise

def update_production_order_detail(production_detail_id: int, **kwargs):
    """更新生產訂單明細"""
    allowed_fields = {
        "planned_qty": "PlannedQty",
        "actual_qty": "ActualQty"
    }
    fields, values = [], []
    
    for param, column in allowed_fields.items():
        if param in kwargs:
            if param == "actual_qty" and (kwargs[param] < 0):
                raise ValueError("實際產量不可為負數")
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return

    query = f"UPDATE ProductionOrderDetail SET {', '.join(fields)} WHERE ProductionDetailID = ?"
    values.append(production_detail_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        logging.info("成功更新生產訂單明細: ProductionDetailID=%d", production_detail_id)

def delete_production_order_detail(production_detail_id: int):
    """刪除指定的生產訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ProductionOrderDetail WHERE ProductionDetailID = ?", (production_detail_id,))
            conn.commit()
            logging.info("成功刪除生產訂單明細: ProductionDetailID = %d", production_detail_id)
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("刪除失敗: %s", e)
            raise ValueError("資料庫操作失敗") from e


def get_production_order_details(order_id: Optional[int] = None, page: int = 1, page_size: int = 100) -> List[Dict]:
    """取得生產訂單明細，支援分頁查詢"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT d.*, i.ItemName 
            FROM ProductionOrderDetail d
            JOIN ItemMaster i ON d.ItemID = i.ItemID
        '''
        params = []
        if order_id:
            query += " WHERE d.ProductionOrderID = ?"
            params.append(order_id)

        offset = (page - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])

        cursor.execute(query, tuple(params))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

if __name__ == "__main__":
    create_tables()

    # 新增測試資料
    add_item("測試原料", "原料", "原材料", "公斤")
    add_production_order(product_id=1, order_date="2025-02-10", status="Pending")

    # 測試新增、查詢、更新與刪除
    add_production_order_detail(production_order_id=1, item_id=1, planned_qty=100.0)
    details = get_production_order_details(order_id=1)
    print("新增後的生產訂單明細:", details)

    update_production_order_detail(1, actual_qty=95.0)
    details = get_production_order_details(order_id=1)
    print("更新後的生產訂單明細:", details)

    delete_production_order_detail(1)
    print("刪除後的生產訂單明細:", get_production_order_details(order_id=1))
