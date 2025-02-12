import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables

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

# === CRUD Functions ===
def add_sales_order_detail(order_id: int, item_id: int, quantity: float, price: float, shipped_quantity: float = 0.0):
    """新增銷售訂單明細，並驗證業務邏輯"""
    if shipped_quantity > quantity:
        raise ValueError("已發貨數量不可超過訂購數量")
    if quantity <= 0:
        raise ValueError("數量必須為正數")
    if price <= 0:
        raise ValueError("價格必須為正數")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO SalesOrderDetail (OrderID, ItemID, Quantity, Price, ShippedQuantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, item_id, quantity, price, shipped_quantity))
            conn.commit()
            logging.info("成功新增訂單明細: OrderID=%d, ItemID=%d", order_id, item_id)
        except sqlite3.IntegrityError as e:
            handle_integrity_error(e)

def get_sales_order_details(order_id: Optional[int] = None, offset: int = 0, limit: int = 100) -> List[Dict]:
    """取得銷售訂單明細，支援分頁與篩選"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT d.*, i.ItemName 
            FROM SalesOrderDetail d
            JOIN ItemMaster i ON d.ItemID = i.ItemID
            WHERE d.IsDeleted = 0
        '''
        params = []
        if order_id:
            query += " AND d.OrderID = ?"
            params.append(order_id)
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def update_sales_order_detail(order_detail_id: int, **kwargs):
    """更新銷售訂單明細"""
    allowed_fields = {
        "quantity": "Quantity",
        "price": "Price",
        "shipped_quantity": "ShippedQuantity"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return  # 無需更新

    query = f"UPDATE SalesOrderDetail SET {', '.join(fields)} WHERE OrderDetailID = ? AND IsDeleted = 0"
    values.append(order_detail_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        logging.info("成功更新訂單明細: OrderDetailID=%d", order_detail_id)

def delete_sales_order_detail(order_detail_id: int):
    """軟刪除指定的訂單明細"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE SalesOrderDetail SET IsDeleted = 1 WHERE OrderDetailID = ?", (order_detail_id,))
        conn.commit()
        logging.info("已刪除訂單明細: OrderDetailID=%d", order_detail_id)

def ship_order_detail(order_detail_id: int, shipped_qty: float):
    """發貨並自動扣減庫存"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. 取得訂單明細與庫存信息
        cursor.execute('''
            SELECT d.ItemID, d.Quantity, d.ShippedQuantity, s.Quantity AS StockQuantity
            FROM SalesOrderDetail d
            JOIN Stock s ON d.ItemID = s.ItemID
            WHERE d.OrderDetailID = ? AND d.IsDeleted = 0
        ''', (order_detail_id,))
        row = cursor.fetchone()

        if not row:
            raise ValueError("訂單明細或庫存記錄不存在")

        item_id, order_qty, shipped_qty_current, stock_qty = row

        # 2. 驗證發貨數量
        if shipped_qty_current + shipped_qty > order_qty:
            raise ValueError("發貨數量超過訂購數量")
        if stock_qty < shipped_qty:
            raise ValueError("庫存不足")

        # 3. 更新已發貨數量與扣減庫存
        try:
            cursor.execute('''
                UPDATE SalesOrderDetail 
                SET ShippedQuantity = ShippedQuantity + ? 
                WHERE OrderDetailID = ?
            ''', (shipped_qty, order_detail_id))

            cursor.execute('''
                UPDATE Stock 
                SET Quantity = Quantity - ? 
                WHERE ItemID = ?
            ''', (shipped_qty, item_id))

            conn.commit()
            logging.info("成功發貨並扣減庫存: OrderDetailID=%d, ShippedQty=%.2f", order_detail_id, shipped_qty)
        except sqlite3.Error as e:
            conn.rollback()
            logging.error("發貨失敗: %s", e)
            raise RuntimeError("發貨操作失敗")

def get_stock_by_item(item_id: int) -> List[Dict]:
    """依據 ItemID 查詢庫存記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stock WHERE ItemID = ?", (item_id,))
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


# === Helper Function ===
def handle_integrity_error(e: sqlite3.IntegrityError):
    """處理 IntegrityError"""
    if "FOREIGN KEY" in str(e):
        logging.error("外鍵約束失敗: 訂單或商品不存在")
        raise ValueError("訂單或商品不存在") from e
    elif "UNIQUE" in str(e):
        logging.error("唯一性約束失敗: 同一訂單中商品重複")
        raise ValueError("商品已存在於此訂單") from e
    else:
        raise

# === 測試範例 ===
if __name__ == "__main__":
    create_tables()

    # 測試新增訂單明細
    try:
        add_sales_order_detail(order_id=1, item_id=1, quantity=10.0, price=100.0)
    except ValueError as e:
        logging.error("測試錯誤: %s", e)

    # 查詢訂單明細
    details = get_sales_order_details(order_id=1)
    print("訂單明細:", details)

    # 測試更新與刪除
    update_sales_order_detail(order_detail_id=1, quantity=12.0)
    delete_sales_order_detail(order_detail_id=1)
