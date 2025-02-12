from contextlib import contextmanager
from typing import Optional, List, Dict
from models.erp_database_schema import get_connection, create_tables
import sqlite3
import logging
from models.itemmaster_crud import add_item
from models.bomheader_crud import add_bom_header

logging.basicConfig(level=logging.INFO)

        
# === CRUD Functions for BOMDetail ===
def add_bom_detail(bom_id: int, component_item_id: int, quantity: float, unit: str, scrap_rate: Optional[float] = None):
    """新增 BOM 明細"""
    if quantity <= 0:
        raise ValueError("Quantity 必須為正數")
    if scrap_rate is not None and not (0.0 <= scrap_rate <= 1.0):
        raise ValueError("ScrapRate 必須在 0.0 到 1.0 之間")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO BOMDetail (BOMID, ComponentItemID, Quantity, Unit, ScrapRate)
                VALUES (?, ?, ?, ?, ?)
            ''', (bom_id, component_item_id, quantity, unit, scrap_rate))
            conn.commit()
            logging.info("成功新增 BOMDetail")
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY" in str(e):
                logging.error("外鍵約束失敗: BOMID 或 ComponentItemID 不存在")
                raise ValueError("BOM 或組件不存在") from e
            elif "UNIQUE" in str(e):
                logging.error("唯一性約束失敗: 同一 BOM 中組件重複")
                raise ValueError("組件已存在於此 BOM") from e
            else:
                raise

def get_bom_details(bom_id: Optional[int] = None, component_item_id: Optional[int] = None) -> List[Dict]:
    """取得 BOMDetail 記錄，支援條件篩選"""
    query = '''
        SELECT d.BOMDetailID, d.BOMID, d.ComponentItemID, d.Quantity, d.Unit, d.ScrapRate,
               i.ItemName AS ComponentName
        FROM BOMDetail d
        JOIN ItemMaster i ON d.ComponentItemID = i.ItemID
        WHERE 1=1
    '''
    params = []
    if bom_id is not None:
        query += " AND d.BOMID = ?"
        params.append(bom_id)
    if component_item_id is not None:
        query += " AND d.ComponentItemID = ?"
        params.append(component_item_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def update_bom_detail(bom_detail_id: int, **kwargs):
    """更新 BOM 明細"""
    allowed_fields = {
        "bom_id": "BOMID",
        "component_item_id": "ComponentItemID",
        "quantity": "Quantity",
        "unit": "Unit",
        "scrap_rate": "ScrapRate"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            value = kwargs[param]
            if param == "quantity" and value <= 0:
                raise ValueError("Quantity 必須為正數")
            if param == "scrap_rate" and not (0.0 <= value <= 1.0):
                raise ValueError("ScrapRate 必須在 0.0 到 1.0 之間")
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        return  # 無需更新

    query = f"UPDATE BOMDetail SET {', '.join(fields)} WHERE BOMDetailID = ?"
    values.append(bom_detail_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, tuple(values))
            conn.commit()
            logging.info("成功更新 BOMDetail")
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY" in str(e):
                logging.error("外鍵約束失敗: BOMID 或 ComponentItemID 不存在")
                raise ValueError("BOM 或組件不存在") from e
            elif "UNIQUE" in str(e):
                logging.error("唯一性約束失敗: 同一 BOM 中組件重複")
                raise ValueError("組件已存在於此 BOM") from e
            else:
                raise

def delete_bom_detail(bom_detail_id: int):
    """刪除 BOM 明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM BOMDetail WHERE BOMDetailID = ?", (bom_detail_id,))
        conn.commit()
        logging.info("已刪除 BOMDetail: BOMDetailID = %d", bom_detail_id)

# === 測試範例 ===
if __name__ == "__main__":
    create_tables()

    print("\n--- 測試 BOMDetail ---")

    # 先新增 ItemMaster 和 BOMHeader
    add_item("元件A", "原料", "零件", "個")
    add_bom_header(product_id=1, version="V1.0", effective_date="2025-02-01", remarks="測試版本")

    # 新增 BOMDetail 記錄
    add_bom_detail(bom_id=1, component_item_id=1, quantity=5.0, unit="個", scrap_rate=0.05)

    # 查詢並顯示 BOMDetail 記錄
    details = get_bom_details()
    print("所有 BOMDetail 記錄:", details)

    # 嘗試插入重複組件，預期錯誤
    try:
        add_bom_detail(bom_id=1, component_item_id=1, quantity=3.0, unit="個")
    except ValueError as e:
        print("預期錯誤:", e)

    # 更新 BOMDetail
    update_bom_detail(1, quantity=10.0)
    print("更新後的 BOMDetail 記錄:", get_bom_details())

    # 刪除 BOMDetail
    delete_bom_detail(1)
    print("刪除後的 BOMDetail 記錄:", get_bom_details())