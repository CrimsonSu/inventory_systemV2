import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

def list_all_materials():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    sql = """
    SELECT material_id, material_name, unit, quantity_in_stock, safety_stock
    FROM raw_materials
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    print("=== 原料庫存清單 ===")
    for r in rows:
        print(r)  # (material_id, material_name, unit, qty_in_stock, safety_stock)

def list_all_finished_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    sql = """
    SELECT product_id, product_name, package_info, unit, quantity_in_stock, safety_stock
    FROM finished_products
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    print("=== 成品庫存清單 ===")
    for r in rows:
        print(r)  # (product_id, product_name, pack, unit, qty_in_stock, safety_stock)

def adjust_material_stock(material_id, adjust_qty, reason="manual_adjust"):
    """
    正值=增加庫存, 負值=減少庫存。
    自動寫入 stock_log。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT quantity_in_stock FROM raw_materials WHERE material_id=?", (material_id,))
    row = cursor.fetchone()
    if not row:
        print(f"[adjust_material_stock] 找不到 material_id={material_id}")
        conn.close()
        return

    old_stock = row[0]
    new_stock = old_stock + adjust_qty

    # 更新庫存
    cursor.execute("""
        UPDATE raw_materials
        SET quantity_in_stock=?
        WHERE material_id=?
    """, (new_stock, material_id))

    # 寫入 stock_log
    change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    change_type = "manual_adjust"
    cursor.execute("""
        INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
        VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
    """, (change_date, material_id, adjust_qty, old_stock, new_stock, change_type, reason))

    conn.commit()
    conn.close()
    print(f"[adjust_material_stock] material_id={material_id}, 庫存由{old_stock}改為{new_stock}, 原因={reason}")

def adjust_finished_stock(product_id, adjust_qty, reason="manual_adjust"):
    """
    手動調整成品庫存 (同上, 只是改操作 finished_products)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT quantity_in_stock FROM finished_products WHERE product_id=?", (product_id,))
    row = cursor.fetchone()
    if not row:
        print(f"[adjust_finished_stock] 找不到 product_id={product_id}")
        conn.close()
        return

    old_stock = row[0]
    new_stock = old_stock + adjust_qty

    # 更新庫存
    cursor.execute("""
        UPDATE finished_products
        SET quantity_in_stock=?
        WHERE product_id=?
    """, (new_stock, product_id))

    # 寫入 stock_log
    change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    change_type = "manual_adjust"
    cursor.execute("""
        INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
        VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
    """, (change_date, product_id, adjust_qty, old_stock, new_stock, change_type, reason))

    conn.commit()
    conn.close()
    print(f"[adjust_finished_stock] product_id={product_id}, 庫存由{old_stock}改為{new_stock}, 原因={reason}")

if __name__ == "__main__":
    # 測試看看
    list_all_materials()
    list_all_finished_products()

    # 假設material_id=1, 我想手動增加10庫存
    adjust_material_stock(1, 10, reason="盤點入庫")

    # 假設product_id=1, 我想手動減少5庫存(報廢)
    adjust_finished_stock(1, -5, reason="報廢")
