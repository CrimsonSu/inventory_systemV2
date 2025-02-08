import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from erp_database_schema import get_connection, create_tables
import re

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
def validate_email(email: Optional[str]) -> bool:
    """檢查 Email 格式"""
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True

def add_customer(customer_name: str, address: Optional[str] = None, contact_person: Optional[str] = None,
                 phone: Optional[str] = None, email: Optional[str] = None, tax_id: Optional[str] = None):
    """新增客戶資料，並驗證輸入"""
    if not customer_name:
        raise ValueError("客戶名稱不能為空")
    if email and not validate_email(email):
        raise ValueError("無效的 Email 格式")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Customer (CustomerName, Address, ContactPerson, Phone, Email, TaxID)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_name, address, contact_person, phone, email, tax_id))
            conn.commit()
            logging.info("成功新增客戶: %s", customer_name)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE" in str(e):
                logging.error("唯一性約束失敗: 客戶名稱重複")
                raise ValueError("客戶名稱已存在") from e
            else:
                logging.error("資料庫完整性錯誤: %s", e)
                raise ValueError("資料庫操作失敗") from e

# === Read ===
def get_customers(offset: int = 0, limit: int = 100) -> List[Dict]:
    """取得所有客戶記錄，支援分頁"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customer LIMIT ? OFFSET ?", (limit, offset))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """依 CustomerID 查詢單筆客戶記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customer WHERE CustomerID = ?", (customer_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

# === Update ===
def update_customer(customer_id: int, **kwargs):
    """更新客戶記錄"""
    allowed_fields = {
        "customer_name": "CustomerName",
        "address": "Address",
        "tax_id": "TaxID",
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
        return  # 無需更新

    query = f"UPDATE Customer SET {', '.join(fields)} WHERE CustomerID = ?"
    values.append(customer_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        logging.info("成功更新客戶: CustomerID = %d", customer_id)

# === Delete ===
def delete_customer(customer_id: int):
    """刪除指定的客戶記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Customer WHERE CustomerID = ?", (customer_id,))
        conn.commit()
        logging.info("已刪除客戶: CustomerID = %d", customer_id)


# === 測試代碼 ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 測試 Customer CRUD 功能
    logging.info("\n--- 測試 Customer CRUD ---")

    # 新增測試客戶資料
    add_customer(
        customer_name="測試客戶A",
        address="台北市測試路100號",
        tax_id="12345678",
        contact_person="張三",
        phone="0912345678",
        email="test_customer@example.com"
    )

    # 取得所有客戶資料
    customers = get_customers()
    logging.info("所有客戶資料: %s", customers)

    # 查詢單筆客戶資料
    customer = get_customer_by_id(1)
    if customer:
        logging.info("查詢單筆客戶資料: %s", customer)
    else:
        logging.warning("查詢失敗，CustomerID 不存在")

    # 更新測試客戶資料
    update_customer(1, address="新台北市測試路200號", phone="0987654321")
    updated_customer = get_customer_by_id(1)
    logging.info("更新後的客戶資料: %s", updated_customer)

    # 刪除測試客戶資料
    delete_customer(1)
    deleted_customer = get_customer_by_id(1)
    if deleted_customer is None:
        logging.info("客戶刪除成功")
    else:
        logging.warning("刪除失敗")
