import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

def create_sales_order(customer_id, remarks=None):
    """
    建立銷售訂單 (sales_orders)，狀態先設為 'Draft' 或 'Confirmed'
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Confirmed"

    sql = """
    INSERT INTO sales_orders (customer_id, order_date, status, remarks, created_at)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (customer_id, order_date, status, remarks, order_date))

    so_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"成功建立銷售訂單，SO ID = {so_id}")
    return so_id

def add_item_to_sales_order(so_id, product_id, order_qty, unit_price):
    """
    新增銷售訂單細項 (sales_order_items)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    subtotal = order_qty * unit_price

    sql = """
    INSERT INTO sales_order_items (so_id, product_id, order_qty, unit_price, subtotal)
    VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (so_id, product_id, order_qty, unit_price, subtotal))

    conn.commit()
    conn.close()

    print(f"成功新增銷售細項到 SO ID = {so_id}")

def ship_sales_order(so_id):
    """
    模擬實際出貨，將銷售單細項數量扣減成品庫存，並將 sales_orders.status 改為 'Shipped'
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 取得該 SO 的細項
    cursor.execute("""
        SELECT product_id, order_qty
        FROM sales_order_items
        WHERE so_id = ?
    """, (so_id,))
    items = cursor.fetchall()

    # 2. 扣減 finished_products 的庫存
    for (product_id, qty) in items:
        cursor.execute("""
            UPDATE finished_products
            SET quantity_in_stock = quantity_in_stock - ?
            WHERE product_id = ?
        """, (qty, product_id))

    # 3. 更新 SO 的狀態為 'Shipped'
    cursor.execute("""
        UPDATE sales_orders
        SET status = 'Shipped'
        WHERE so_id = ?
    """, (so_id,))

    conn.commit()
    conn.close()

    print(f"SO {so_id} 已出貨，並扣減成品庫存。")


if __name__ == "__main__":
    # 1. 建立一張銷售訂單 (假設 customer_id=1)
    so_id = create_sales_order(customer_id=1, remarks="Test Sale")

    # 2. 新增細項 (假設 product_id=1是狗罐頭，一箱2000元，訂購5箱)
    add_item_to_sales_order(so_id, product_id=1, order_qty=5, unit_price=2000)

    # 3. 出貨
    ship_sales_order(so_id)

    # 4. 檢查 finished_products 的庫存是否 -5