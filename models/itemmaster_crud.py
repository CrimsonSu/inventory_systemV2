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


# === Create ===
def add_item(item_name, item_type, category, unit):
    """新增原料或成品到 ItemMaster"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO ItemMaster (ItemName, ItemType, Category, Unit) VALUES (?, ?, ?, ?)",
                (item_name, item_type, category, unit)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"新增失敗：{e}")
            raise ValueError("新增原料或成品失敗，可能是唯一性約束衝突")

        
# === Read ===
def get_items(search: str = None, page: int = 1, page_size: int = 0) -> List[Dict]:
    """获取有效物料数据（支持分页和搜索）"""
    query = "SELECT * FROM ItemMaster WHERE Status = 'active'"
    params = []
    
    if search:
        query += " AND ItemName LIKE ?"
        params.append(f"%{search}%")
    
    if page_size > 0:
        offset = (page - 1) * page_size
        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

def get_item_by_id(item_id):
    """依 ItemID 查詢單筆原料或成品"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ItemMaster WHERE ItemID = ? AND Status = 'active'", (item_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

# === Update ===
def update_item(item_id, **kwargs):
    """更新指定的原料或成品資料，安全處理欄位更新"""
    allowed_fields = {
        "new_name": "ItemName",
        "new_type": "ItemType",
        "new_category": "Category",
        "new_unit": "Unit"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        value = kwargs.get(param)
        if value:
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        return  # 無需更新

    query = f"UPDATE ItemMaster SET {', '.join(fields)} WHERE ItemID = ?"
    values.append(item_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()

# === Delete ===
def delete_item(item_id, soft_delete=True):
    """刪除指定的原料或成品，支援軟刪除"""
    with get_connection() as conn:
        cursor = conn.cursor()

        if soft_delete:
            cursor.execute(
                "UPDATE ItemMaster SET Status = 'deleted' WHERE ItemID = ?",
                (item_id,)
            )
        else:
            # 檢查關聯資料
            cursor.execute("SELECT COUNT(*) FROM Stock WHERE ItemID = ?", (item_id,))
            if cursor.fetchone()[0] > 0:
                raise Exception("無法刪除：存在關聯庫存記錄")

            cursor.execute("DELETE FROM ItemMaster WHERE ItemID = ?", (item_id,))

        conn.commit()

# 測試範例（可以移除或放在 main.py 中）
if __name__ == "__main__":
    # 新增測試資料
    add_item("測試原料A", "原料", "營養添加物", "公斤")

    # 查詢所有原料或成品
    items = get_items()
    for item in items:
        print(f"ItemID: {item['ItemID']}, 名稱: {item['ItemName']}, 類型: {item['ItemType']}, 類別: {item['Category']}, 單位: {item['Unit']}")

    # 更新測試資料
    update_item(item_id=1, new_name="更新後的名稱")

    # 查詢單筆資料
    item = get_item_by_id(1)
    print(f"單筆查詢結果: {item}")

    # 刪除測試資料（軟刪除）
    delete_item(1)
    print("已刪除測試資料")
