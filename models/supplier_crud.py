import sqlite3
import re
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === CRUD Functions for Supplier ===

def add_supplier(supplier_name: str, address: Optional[str] = None, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None):
    """新增供應商記錄"""
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("無效的 Email 格式")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Supplier (SupplierName, Address, ContactPerson, Phone, Email)
                VALUES (?, ?, ?, ?, ?)
            ''', (supplier_name, address, contact_person, phone, email))
            conn.commit()
            logging.info("成功新增供應商: %s", supplier_name)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("唯一性約束失敗: %s", e)
            raise ValueError("供應商記錄插入失敗")
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("資料庫操作失敗: %s", e)
            raise RuntimeError("供應商記錄插入失敗")

def get_suppliers(offset: int = 0, limit: int = 100) -> List[Dict]:
    """取得所有供應商記錄，支援分頁，返回字典格式"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Supplier LIMIT ? OFFSET ?", (limit, offset))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_supplier_by_id(supplier_id: int) -> Optional[Dict]:
    """依 SupplierID 查詢供應商記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Supplier WHERE SupplierID = ?", (supplier_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        if row:
            return dict(zip(columns, row))
        else:
            logging.warning("查無供應商記錄: SupplierID = %d", supplier_id)
            return None

def update_supplier(supplier_id: int, **kwargs):
    """更新供應商記錄，允許安全更新"""
    allowed_fields = {
        "supplier_name": "SupplierName",
        "address": "Address",
        "contact_person": "ContactPerson",
        "phone": "Phone",
        "email": "Email"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        logging.warning("未提供任何可更新的欄位")
        return  # 無需更新

    query = f"UPDATE Supplier SET {', '.join(fields)} WHERE SupplierID = ?"
    values.append(supplier_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        if cursor.rowcount == 0:
            logging.warning("更新失敗，供應商 ID 不存在: SupplierID = %d", supplier_id)
        else:
            conn.commit()
            logging.info("成功更新供應商: SupplierID = %d", supplier_id)

def delete_supplier(supplier_id: int):
    """刪除指定的供應商記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Supplier WHERE SupplierID = ?", (supplier_id,))
        if cursor.rowcount == 0:
            logging.warning("刪除失敗，供應商 ID 不存在: SupplierID = %d", supplier_id)
        else:
            conn.commit()
            logging.info("已刪除供應商: SupplierID = %d", supplier_id)

# === 測試範例 ===
def test_supplier_crud():
    """測試供應商 CRUD 功能"""
    # 初始化資料表
    create_tables()

    # 新增測試供應商記錄
    add_supplier(supplier_name="供應商A", address="地址1", contact_person="聯絡人A", phone="0912345678", email="supplierA@example.com")

    # 查詢所有供應商記錄
    suppliers = get_suppliers()
    for supplier in suppliers:
        print(f"SupplierID: {supplier['SupplierID']}, SupplierName: {supplier['SupplierName']}")

    # 更新測試供應商記錄
    update_supplier(supplier_id=1, address="新地址", phone="0987654321")

    # 查詢單筆供應商記錄
    supplier_record = get_supplier_by_id(1)
    print(f"供應商查詢結果: {supplier_record}")

    # 刪除測試供應商記錄
    delete_supplier(1)
    print("已刪除測試供應商記錄")

# 執行測試
if __name__ == "__main__":
    test_supplier_crud()
