import sqlite3
import re
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === CRUD Functions for Supplier ===

def add_supplier(supplier_name: str, address: Optional[str] = None, contact_person: Optional[str] = None, phone: Optional[str] = None, email: Optional[str] = None, website: Optional[str] = None, tax_id: Optional[str] = None):
    """新增供應商記錄，允許 Email 欄位為空白"""
    if email:  # 只有當 Email 不為空時才進行驗證
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            logging.warning("無效的 Email 格式: %s", email)
            return False  # Email 格式錯誤時 return False

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Supplier (SupplierName, Address, ContactPerson, Phone, Email, Website, TaxID)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (supplier_name, address, contact_person, phone, email, website, tax_id))
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
    
def get_suppliers(search_text: Optional[str] = None,) -> List[Dict]:
    query = "SELECT SupplierID, SupplierName, ContactPerson, Phone, Address,TaxID, Email ,Website FROM Supplier"
    params = []

    if search_text:
        query += " WHERE SupplierName LIKE ? OR Phone LIKE ?"
        search_pattern = f"%{search_text}%"
        params.extend([search_pattern, search_pattern])

    query += " ORDER BY SupplierID"

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"數據庫查詢錯誤: {e}")
            return []

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
        "email": "Email",
        "website": "Website",
        "tax_id": "TaxID"
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
    with get_connection() as conn:
        cursor = conn.cursor()

        # ✅ 修正表名，查詢 `PurchaseOrderHeader` 是否仍有該供應商的訂單
        cursor.execute("SELECT COUNT(*) FROM PurchaseOrderHeader WHERE SupplierID = ?", (supplier_id,))
        order_count = cursor.fetchone()[0]

        if order_count > 0:
            logging.warning("❌ 無法刪除，供應商仍有 %d 筆訂單", order_count)
            return f"❌ 刪除失敗：該供應商仍然有 {order_count} 筆訂單，請先刪除相關訂單！"

        try:
            cursor.execute("DELETE FROM Supplier WHERE SupplierID = ?", (supplier_id,))
            conn.commit()
            logging.info("✅ 成功刪除供應商: SupplierID = %d", supplier_id)
            return "✅ 供應商已成功刪除！"
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("❌ 刪除失敗（外鍵約束）: %s", e)
            return "❌ 刪除失敗：該供應商仍然有關聯資料！"
        except Exception as e:
            conn.rollback()
            logging.error("❌ 刪除時發生未知錯誤: %s", e)
            return f"❌ 刪除失敗：{str(e)}"
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
