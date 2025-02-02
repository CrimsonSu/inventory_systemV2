import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

def create_production_order(product_id, planned_qty, remarks=""):
    """
    在 production_orders 建立一筆生產工單, 狀態預設為 'Planned'
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Planned"
    sql = """
    INSERT INTO production_orders (product_id, planned_qty, actual_qty, start_date, status, remarks)
    VALUES (?, ?, 0, ?, ?, ?)
    """
    cursor.execute(sql, (product_id, planned_qty, start_date, status, remarks))
    production_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(f"[create_production_order] 已建立生產工單ID={production_id} (成品ID={product_id}, 計畫量={planned_qty})")
    return production_id

def plan_production_materials(production_id):
    """
    根據 BOM, 幫這個 production_order 自動填入理論用料 (插入 production_materials)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 先查詢此工單對應的 product_id, planned_qty
    cursor.execute("SELECT product_id, planned_qty FROM production_orders WHERE production_id=?", (production_id,))
    row = cursor.fetchone()
    if not row:
        print("[plan_production_materials] 找不到 production_id=", production_id)
        conn.close()
        return
    product_id, planned_qty = row

    # 再查詢 BOM: 這個 product_id 需要哪些原料
    cursor.execute("SELECT raw_material_id, quantity_needed FROM bom WHERE finished_product_id=?", (product_id,))
    bom_rows = cursor.fetchall()
    if not bom_rows:
        print("[plan_production_materials] BOM中沒有成品ID=", product_id, "的配方。")
        conn.close()
        return

    # 依照 BOM, 以及計畫數量, 計算理論用量
    for (material_id, needed_per_unit) in bom_rows:
        planned_usage = needed_per_unit * planned_qty
        # 插入 production_materials (planned_qty=計畫用量, actual_qty=0 先放著)
        cursor.execute("""
            INSERT INTO production_materials (production_id, material_id, planned_qty, actual_qty)
            VALUES (?, ?, ?, 0)
        """, (production_id, material_id, planned_usage))

    conn.commit()
    conn.close()
    print(f"[plan_production_materials] 已依BOM, 建立此工單ID={production_id}的用料清單。")

def produce(production_id, actual_qty):
    """
    實際執行生產:
      1. 依BOM (或前面插入的planned_qty) 扣除原料庫存
      2. 增加成品庫存
      3. 更新 production_orders 的 actual_qty, end_date, status='Completed'
      4. 同時更新 production_materials 的 actual_qty (讓其跟理論用量可能有差異)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 查 production_orders
    cursor.execute("SELECT product_id, planned_qty FROM production_orders WHERE production_id=?", (production_id,))
    po_row = cursor.fetchone()
    if not po_row:
        print("[produce] 找不到 production_id=", production_id)
        conn.close()
        return
    product_id, planned_qty = po_row

    # 先算出「理論用料占比」 (actual_qty / planned_qty)
    # 若 actual_qty < planned_qty, 代表生產損耗
    # 這是一種簡單推算方式，也可更複雜設計
    ratio = 0
    if planned_qty != 0:
        ratio = actual_qty / planned_qty

    # 取得此工單下所有 production_materials (planned_qty)
    cursor.execute("""
        SELECT pm_id, material_id, planned_qty, actual_qty
        FROM production_materials
        WHERE production_id=?
    """, (production_id,))
    pm_rows = cursor.fetchall()

    # 對每個原料, 依照 ratio 來計算實際用量, 扣庫存
    for (pm_id, material_id, planned_usage, old_actual) in pm_rows:
        real_usage = planned_usage * ratio  # 這是簡單做法
        # 更新 production_materials.actual_qty
        cursor.execute("""
            UPDATE production_materials
            SET actual_qty = ?
            WHERE pm_id = ?
        """, (real_usage, pm_id))

        # 扣掉原料庫存
        # 先查原來庫存
        cursor.execute("SELECT quantity_in_stock FROM raw_materials WHERE material_id=?", (material_id,))
        mat_row = cursor.fetchone()
        if mat_row:
            old_stock = mat_row[0]
            new_stock = old_stock - real_usage

            cursor.execute("""
                UPDATE raw_materials
                SET quantity_in_stock = ?
                WHERE material_id=?
            """, (new_stock, material_id))

            # === 寫入 stock_log (扣原料) ===
            change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            change_type = "production"
            reason = f"生產工單ID={production_id}"
            cursor.execute("""
                INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
            """, (change_date, material_id, -real_usage, old_stock, new_stock, change_type, reason))

    # 增加成品庫存
    cursor.execute("SELECT quantity_in_stock FROM finished_products WHERE product_id=?", (product_id,))
    prod_row = cursor.fetchone()
    if prod_row:
        old_prod_stock = prod_row[0]
        new_prod_stock = old_prod_stock + actual_qty
        cursor.execute("""
            UPDATE finished_products
            SET quantity_in_stock = ?
            WHERE product_id=?
        """, (new_prod_stock, product_id))

        # === 寫入 stock_log (加成品) ===
        change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        change_type = "production"
        reason = f"生產工單ID={production_id}"
        cursor.execute("""
            INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
        """, (change_date, product_id, actual_qty, old_prod_stock, new_prod_stock, change_type, reason))

    # 更新 production_orders (actual_qty, end_date, status)
    end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE production_orders
        SET actual_qty = ?, end_date = ?, status='Completed'
        WHERE production_id=?
    """, (actual_qty, end_date, production_id))

    conn.commit()
    conn.close()
    print(f"[produce] 生產工單ID={production_id} 完工, 實際產量={actual_qty}.")

# 測試用
if __name__ == "__main__":
    # 舉例:
    # 1) 建立一個生產工單( product_id=1, planned_qty=100 )
    p_id = create_production_order(1, 100, remarks="測試生產100箱狗罐頭")

    # 2) 依 BOM 自動幫這個工單插入用料( production_materials )
    plan_production_materials(p_id)

    # 3) 最終實際生產只有 90 箱, produce => 扣原料, 加成品, 更新狀態
    produce(p_id, 90)
