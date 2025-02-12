import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
from models.erp_database_schema import get_connection, create_tables
import logging
from datetime import datetime
        
# === 改進 1：新增前置外鍵檢查 ===
def check_product_exists(product_id: int) -> bool:
    """檢查 ProductID 是否存在於 ItemMaster 表中"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM ItemMaster WHERE ItemID = ?", (product_id,))
        return cursor.fetchone() is not None

# === 改進 2：日期有效性檢查 ===
def validate_dates(effective_date: str, expire_date: Optional[str]):
    """驗證日期有效性，確保 ExpireDate 不早於 EffectiveDate"""
    effective = datetime.strptime(effective_date, "%Y-%m-%d")
    if expire_date:
        expire = datetime.strptime(expire_date, "%Y-%m-%d")
        if expire < effective:
            raise ValueError("失效日期不可早於生效日期")

# === 增強的 CRUD 函數 ===

# === Create ===
def add_bom_header(product_id: int, version: str, effective_date: str, expire_date: Optional[str] = None, remarks: Optional[str] = None):
    """新增 BOMHeader 記錄"""
    if not check_product_exists(product_id):
        raise ValueError(f"ProductID {product_id} 不存在於 ItemMaster 表中")

    validate_dates(effective_date, expire_date)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                INSERT INTO BOMHeader (ProductID, Version, EffectiveDate, ExpireDate, Remarks)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (product_id, version, effective_date, expire_date, remarks)
            )
            conn.commit()
            logging.info("成功新增 BOMHeader: ProductID = %d, Version = %s", product_id, version)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "FOREIGN KEY" in str(e):
                raise ValueError("ProductID 無效") from e
            elif "UNIQUE" in str(e):
                raise ValueError("同一產品的版本已存在") from e
            else:
                raise

# === Read ===
def get_bom_headers() -> List[Dict]:
    """取得所有 BOMHeader 記錄，返回字典格式"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM BOMHeader")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_bom_header_by_id(bom_id: int) -> Optional[Dict]:
    """依 BOMID 查詢 BOMHeader 記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM BOMHeader WHERE BOMID = ?", (bom_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

# === Update ===
def update_bom_header(bom_id: int, **kwargs):
    """更新 BOMHeader 記錄，支援多欄位更新並驗證日期"""
    allowed_fields = {
        "new_product_id": "ProductID",
        "new_version": "Version",
        "new_effective_date": "EffectiveDate",
        "new_expire_date": "ExpireDate",
        "new_remarks": "Remarks"
    }

    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            value = kwargs[param]
            if column in ["EffectiveDate", "ExpireDate"]:
                # 驗證日期有效性
                validate_dates(kwargs.get("new_effective_date", ""), kwargs.get("new_expire_date"))
            fields.append(f"{column} = ?")
            values.append(value)

    if not fields:
        return  # 無需更新

    query = f"UPDATE BOMHeader SET {', '.join(fields)} WHERE BOMID = ?"
    values.append(bom_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        logging.info("成功更新 BOMHeader: BOMID = %d", bom_id)

# === Delete ===
def delete_bom_header(bom_id: int):
    """刪除指定的 BOMHeader 記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM BOMHeader WHERE BOMID = ?", (bom_id,))
        conn.commit()
        logging.info("已刪除 BOMHeader: BOMID = %d", bom_id)

# === 測試範例（Main.py 可用） ===
if __name__ == "__main__":
    # 測試 BOMHeader CRUD 操作
    add_bom_header(product_id=1, version="V1.0", effective_date="2025-01-01", expire_date="2025-12-31")
    print("所有 BOMHeader:", get_bom_headers())

    update_bom_header(bom_id=1, new_remarks="更新備註", new_version="V1.1")
    print("更新後的 BOMHeader:", get_bom_header_by_id(1))

    delete_bom_header(1)
    print("刪除後的 BOMHeader:", get_bom_headers())
