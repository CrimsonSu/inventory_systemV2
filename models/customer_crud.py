import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Create ===
def validate_email(email: Optional[str]) -> bool:
    """檢查 Email 格式"""
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True

def add_customer(customer_name: str, address: Optional[str] = None, address2: Optional[str] = None,contact_person: Optional[str] = None,
                 phone: Optional[str] = None, email: Optional[str] = None, tax_id: Optional[str] = None):
    """新增客戶資料，並驗證輸入"""
    if not customer_name:
        raise ValueError("客戶名稱不能為空")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Customer (CustomerName, Address, Address2, ContactPerson, Phone, Email, TaxID)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_name, address, address2, contact_person, phone, email, tax_id))
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
from typing import List, Dict, Optional

def get_customers(search_term: Optional[str] = None) -> List[Dict]:
    query = "SELECT CustomerID, CustomerName, ContactPerson, Phone, Address, Address2 ,TaxID, Email FROM Customer"
    params = []

    if search_term:
        query += " WHERE CustomerName LIKE ? OR Phone LIKE ?"
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern])

    query += " ORDER BY CustomerID"

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"數據庫查詢錯誤: {e}")
            return []

        
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
        "address2": "Address2",
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
    with get_connection() as conn:
        cursor = conn.cursor()

        # ✅ 修正表名，查詢 `SalesOrderHeader` 是否仍有該客戶的訂單
        cursor.execute("SELECT COUNT(*) FROM SalesOrderHeader WHERE CustomerID = ?", (customer_id,))
        order_count = cursor.fetchone()[0]

        if order_count > 0:
            logging.warning("❌ 無法刪除，客戶仍有 %d 筆訂單", order_count)
            return f"❌ 刪除失敗：該客戶仍然有 {order_count} 筆訂單，請先刪除相關訂單！"

        try:
            cursor.execute("DELETE FROM Customer WHERE CustomerID = ?", (customer_id,))
            conn.commit()
            logging.info("✅ 成功刪除客戶: CustomerID = %d", customer_id)
            return "✅ 客戶已成功刪除！"
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error("❌ 刪除失敗（外鍵約束）: %s", e)
            return "❌ 刪除失敗：該客戶仍然有關聯資料！"
        except Exception as e:
            conn.rollback()
            logging.error("❌ 刪除時發生未知錯誤: %s", e)
            return f"❌ 刪除失敗：{str(e)}"




# === 測試代碼 ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 測試 Customer CRUD 功能
    logging.info("\n--- 測試 Customer CRUD ---")

    # 新增測試客戶資料
    add_customer(
        customer_name="測試客戶A",
        address="台北市測試路100號",
        address2="台北市測試路999號",
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
