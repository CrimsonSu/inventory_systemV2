import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

def add_supplier(supplier_name, phone, address):
    """
    新增一筆供應商資料到 suppliers 表。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        INSERT INTO suppliers (supplier_name, phone, address, created_at)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(sql, (supplier_name, phone, address, current_time))
    conn.commit()
    conn.close()
    print(f"成功新增供應商：{supplier_name}")

def list_suppliers():
    """
    列出所有供應商。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    sql = "SELECT supplier_id, supplier_name, phone, address, created_at FROM suppliers"
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("供應商列表：")
        for row in rows:
            print(row)
    else:
        print("目前尚無供應商資料。")

def update_supplier(supplier_id, new_phone=None, new_address=None):
    """
    更新指定 supplier_id 的供應商資料（電話或地址）。
    """
    if new_phone is None and new_address is None:
        print("未提供新電話或新地址，無更新。")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 動態組合 SQL 句，如果只有phone要改，或只有address要改
    fields_to_update = []
    params = []

    if new_phone is not None:
        fields_to_update.append("phone = ?")
        params.append(new_phone)
    if new_address is not None:
        fields_to_update.append("address = ?")
        params.append(new_address)

    fields_str = ", ".join(fields_to_update)
    sql = f"UPDATE suppliers SET {fields_str} WHERE supplier_id = ?"
    params.append(supplier_id)

    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    print(f"成功更新供應商ID {supplier_id} 的資料。")

def delete_supplier(supplier_id):
    """
    刪除指定的供應商。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    sql = "DELETE FROM suppliers WHERE supplier_id = ?"
    cursor.execute(sql, (supplier_id,))
    conn.commit()
    conn.close()

    print(f"成功刪除供應商ID {supplier_id}。")


if __name__ == "__main__":
    # 測試使用：連續呼叫函式
    print("=== 新增供應商 ===")
    add_supplier("XYZ Supplier", "03-45678901", "Kaohsiung City")

    print("=== 列出所有供應商 ===")
    list_suppliers()

    print("=== 更新供應商(假設更新ID=1的電話) ===")
    update_supplier(1, new_phone="02-22223333")

    print("=== 列出所有供應商(檢查更新後結果) ===")
    list_suppliers()

    print("=== 刪除供應商(假設刪除ID=2) ===")
    delete_supplier(2)

    print("=== 最後再列出供應商 ===")
    list_suppliers()
