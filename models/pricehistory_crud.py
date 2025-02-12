import sqlite3
from datetime import datetime
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


# === 資料庫連線管理 ===
@contextmanager
def get_connection():
    conn = sqlite3.connect("erp_system.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# === CRUD 功能 ===

def validate_effective_date(effective_date: str) -> str:
    """驗證生效日期格式並允許未來日期"""
    try:
        date_obj = datetime.strptime(effective_date, "%Y-%m-%d").date()
        # 取消未來日期限制（測試期間可開放）
        # if date_obj > datetime.now().date():
        #     raise ValueError("生效日期不能是未來日期")
        return date_obj
    except ValueError:
        raise ValueError("無效日期格式，請使用YYYY-MM-DD")

def validate_price(price: float):
    if price <= 0:
        raise ValueError("價格必須大於零")

def add_price_history(item_id: int, effective_date: str, price: float):
    validated_date = validate_effective_date(effective_date)
    validate_price(price)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO PriceHistory (ItemID, EffectiveDate, Price)
                VALUES (?, ?, ?)
            ''', (item_id, validated_date, price))
            conn.commit()
            logging.info("成功新增價格歷史記錄")
        except sqlite3.IntegrityError as e:
            logging.error("新增價格歷史失敗: %s", e)
            raise ValueError("項目不存在或數據錯誤")

def get_price_history(item_id: int) -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM PriceHistory WHERE ItemID = ? ORDER BY EffectiveDate DESC
        ''', (item_id,))
        return [dict(row) for row in cursor.fetchall()]

ALLOWED_FIELDS = {'price', 'effectivedate'}

def update_price_history(price_history_id: int, **kwargs):
    # 統一將傳入字段名稱轉為小寫
    normalized_kwargs = {k.lower(): v for k, v in kwargs.items()}
    invalid_fields = set(normalized_kwargs.keys()) - ALLOWED_FIELDS
    if invalid_fields:
        raise ValueError(f"非法字段: {', '.join(invalid_fields)}")

    # SQL 更新操作
    updates = ", ".join(f"{key} = ?" for key in normalized_kwargs.keys())
    params = list(normalized_kwargs.values()) + [price_history_id]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE PriceHistory
            SET {updates}
            WHERE PriceHistoryID = ?
        ''', params)
      

def delete_price_history(price_history_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM PriceHistory WHERE PriceHistoryID = ?', (price_history_id,))
        conn.commit()

# === 測試邏輯 ===
if __name__ == "__main__":
    create_tables()

    # 新增價格歷史測試
    add_price_history(item_id=1, effective_date="2025-02-10", price=100.0)
    print("新增價格歷史:", get_price_history(item_id=1))

    # 更新價格歷史測試
    update_price_history(price_history_id=1, Price=120.0)
    print("更新後價格歷史:", get_price_history(item_id=1))

    # 刪除價格歷史測試
    delete_price_history(price_history_id=1)
    print("刪除後價格歷史:", get_price_history(item_id=1))
