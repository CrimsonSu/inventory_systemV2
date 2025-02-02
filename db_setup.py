import sqlite3
from datetime import datetime

def create_tables():
    create_tables_sql = """
    -- 1. 供應商
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TEXT
    );

    -- 2. 客戶
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TEXT
    );

    -- 3. 原料 (raw_materials)
    CREATE TABLE IF NOT EXISTS raw_materials (
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_name TEXT NOT NULL,
        unit TEXT,
        quantity_in_stock REAL DEFAULT 0,
        safety_stock REAL DEFAULT 0,
        created_at TEXT
    );

    -- 4. 成品 (finished_products)
    CREATE TABLE IF NOT EXISTS finished_products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        package_info TEXT,
        unit TEXT,
        quantity_in_stock REAL DEFAULT 0,
        safety_stock REAL DEFAULT 0,
        created_at TEXT
    );

    -- 5. 採購單主檔 (purchase_orders)
    CREATE TABLE IF NOT EXISTS purchase_orders (
        po_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL,
        order_date TEXT,
        status TEXT,
        remarks TEXT,
        created_at TEXT,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    );

    -- 6. 採購單細項 (purchase_order_items)
    CREATE TABLE IF NOT EXISTS purchase_order_items (
        poi_id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        order_qty REAL,
        unit_price REAL,
        subtotal REAL,
        FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
        FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
    );

    -- 7. 銷售訂單主檔 (sales_orders)
    CREATE TABLE IF NOT EXISTS sales_orders (
        so_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TEXT,
        status TEXT,
        remarks TEXT,
        created_at TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    -- 8. 銷售訂單細項 (sales_order_items)
    CREATE TABLE IF NOT EXISTS sales_order_items (
        soi_id INTEGER PRIMARY KEY AUTOINCREMENT,
        so_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        order_qty REAL,
        unit_price REAL,
        subtotal REAL,
        FOREIGN KEY (so_id) REFERENCES sales_orders(so_id),
        FOREIGN KEY (product_id) REFERENCES finished_products(product_id)
    );

    -- 9. 生產工單 (production_orders)
    CREATE TABLE IF NOT EXISTS production_orders (
        production_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        planned_qty REAL,
        actual_qty REAL,
        start_date TEXT,
        end_date TEXT,
        status TEXT,
        remarks TEXT,
        FOREIGN KEY (product_id) REFERENCES finished_products(product_id)
    );

    -- 10. BOM (Bill of Materials) 配方表
    CREATE TABLE IF NOT EXISTS bom (
        bom_id INTEGER PRIMARY KEY AUTOINCREMENT,
        finished_product_id INTEGER NOT NULL,
        raw_material_id INTEGER NOT NULL,
        quantity_needed REAL,
        FOREIGN KEY (finished_product_id) REFERENCES finished_products(product_id),
        FOREIGN KEY (raw_material_id) REFERENCES raw_materials(material_id)
    );

    -- 11. production_materials：生產實際用料紀錄 (可選，若要細分每次領料)
    CREATE TABLE IF NOT EXISTS production_materials (
        pm_id INTEGER PRIMARY KEY AUTOINCREMENT,
        production_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        planned_qty REAL,  -- 理論需求
        actual_qty REAL,   -- 實際使用
        FOREIGN KEY (production_id) REFERENCES production_orders(production_id),
        FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
    );

    -- 12. stock_log：庫存異動日誌 (手動調整、報廢、盤點等紀錄)
    CREATE TABLE IF NOT EXISTS stock_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_date TEXT,
        material_id INTEGER,
        product_id INTEGER,
        change_qty REAL,        -- 本次異動量(+/-)
        old_qty REAL,           -- 異動前庫存
        new_qty REAL,           -- 異動後庫存
        change_type TEXT,       -- 'manual_adjust', 'purchase', 'sale', 'production' 等
        reason TEXT,            -- 自由敘述，ex: '報廢', '盤點差異'
        FOREIGN KEY (material_id) REFERENCES raw_materials(material_id),
        FOREIGN KEY (product_id) REFERENCES finished_products(product_id)
    );
    """
    return create_tables_sql

def main():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    sql_script = create_tables()
    cursor.executescript(sql_script)

    # 以下只是測試插入1筆供應商資料
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO suppliers (supplier_name, phone, address, created_at)
        VALUES (?, ?, ?, ?)
    """, ("ABC Supplier", "02-12345678", "Taipei City", current_time))

    conn.commit()
    conn.close()
    print("資料表建立(或已存在)，並插入測試資料完成！")

if __name__ == "__main__":
    main()
