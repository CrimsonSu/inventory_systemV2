import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

def create_purchase_order(supplier_id, remarks=None):
    """
    建立採購單主檔 (purchase_orders)；狀態先設為 'Draft' 或 'Ordered'
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Ordered"  # 你可以依公司流程設定：Draft/Ordered/Received...
    
    sql = """
    INSERT INTO purchase_orders (supplier_id, order_date, status, remarks, created_at)
    VALUES (?, ?, ?, ?, ?)
    """
    current_time = order_date  # 同樣也可用 datetime.now()
    cursor.execute(sql, (supplier_id, order_date, status, remarks, current_time))

    # 取得剛插入的 this_po_id (自動增量)
    po_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(f"成功建立採購單，PO ID = {po_id}")
    return po_id

def add_item_to_purchase_order(po_id, material_id, order_qty, unit_price):
    """
    新增採購單細項 (purchase_order_items)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    subtotal = order_qty * unit_price

    sql = """
    INSERT INTO purchase_order_items (po_id, material_id, order_qty, unit_price, subtotal)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (po_id, material_id, order_qty, unit_price, subtotal))

    conn.commit()
    conn.close()

    print(f"成功新增採購細項到 PO ID = {po_id}")

def receive_purchase_order(po_id):
    """
    模擬實際到貨，將採購單細項數量入庫 (更新 raw_materials.quantity_in_stock)
    並將 purchase_orders.status 改為 'Received'
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 取得該 PO 的細項
    cursor.execute("""
        SELECT material_id, order_qty
        FROM purchase_order_items
        WHERE po_id = ?
    """, (po_id,))
    items = cursor.fetchall()

    # 2. 對每個細項更新 raw_materials 的庫存
    for (material_id, qty) in items:
        cursor.execute("""
            UPDATE raw_materials
            SET quantity_in_stock = quantity_in_stock + ?
            WHERE material_id = ?
        """, (qty, material_id))

    # 3. 更新該 PO 的狀態為 'Received'
    cursor.execute("""
        UPDATE purchase_orders
        SET status = 'Received'
        WHERE po_id = ?
    """, (po_id,))

    conn.commit()
    conn.close()

    print(f"PO {po_id} 已更新為 Received，並將細項數量入庫。")

if __name__ == "__main__":
    # 1. 建立一張採購單 (假設 supplier_id=1)
    po_id = create_purchase_order(supplier_id=1, remarks="Test Order")

    # 2. 增加細項 (假設 material_id=1是雞肉，每箱單價2000，訂購10箱)
    add_item_to_purchase_order(po_id, material_id=1, order_qty=10, unit_price=2000)

    # 3. 到貨入庫 (receive)
    receive_purchase_order(po_id)

    # 4. 檢查 raw_materials 的庫存是否 +10
    #    (可在這裡或 db_test.py 裡查  SELECT * FROM raw_materials; )
