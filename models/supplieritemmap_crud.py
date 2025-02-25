import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging
from models.erp_database_schema import get_connection, create_tables
from models.supplier_crud import add_supplier
from models.pricehistory_crud import add_price_history_from_mapping  # 新增此行
from datetime import datetime  # 新增此行


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

# === CRUD Functions for SupplierItemMap ===

def add_supplier_item_mapping(supplier_id: int, item_id: int, moq: Optional[int] = None, price: Optional[float] = None, lead_time: Optional[int] = None, safety_stock_level: Optional[float] = 0.0):
    """新增供應商與項目關聯記錄，檢查外鍵是否存在"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 檢查 SupplierID 是否存在
        cursor.execute("SELECT 1 FROM Supplier WHERE SupplierID = ?", (supplier_id,))
        if not cursor.fetchone():
            raise ValueError(f"SupplierID {supplier_id} 不存在")

        # 檢查 ItemID 是否存在
        cursor.execute("SELECT 1 FROM ItemMaster WHERE ItemID = ?", (item_id,))
        if not cursor.fetchone():
            raise ValueError(f"ItemID {item_id} 不存在")

        # 插入記錄
        try:
            logging.info(f"正在插入記錄: SupplierID={supplier_id}, ItemID={item_id}, SafetyStockLevel={safety_stock_level}")
            cursor.execute('''
                INSERT INTO SupplierItemMap (SupplierID, ItemID, MOQ, Price, LeadTime, SafetyStockLevel)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (supplier_id, item_id, moq, price, lead_time, safety_stock_level))

            if price is not None:
                add_price_history_from_mapping(
                    supplier_id=supplier_id,
                    item_id=item_id,
                    price=price,
                    effective_date=datetime.now().strftime("%Y-%m-%d"),
                    conn=conn
                )
            conn.commit()
            logging.info("成功新增供應商項目映射記錄")
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE" in str(e):
                logging.error("唯一性約束失敗: %s", e)
                raise ValueError("同一 SupplierID 與 ItemID 的映射已存在") from e
            elif "FOREIGN KEY" in str(e):
                logging.error("外鍵約束失敗: %s", e)
                raise ValueError("外鍵約束失敗，請確認 SupplierID 和 ItemID 是否正確") from e
            else:
                raise

def get_supplier_item_mappings() -> List[Dict]:
    """取得所有供應商與項目關聯記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.MappingID, m.SupplierID, s.SupplierName, m.ItemID, i.ItemName, 
                   m.MOQ, m.Price, m.LeadTime, m.SafetyStockLevel
            FROM SupplierItemMap m
            JOIN Supplier s ON m.SupplierID = s.SupplierID
            JOIN ItemMaster i ON m.ItemID = i.ItemID
        ''')
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_supplier_item_mapping_by_id(mapping_id: int) -> Optional[Dict]:
    """依 MappingID 查詢單筆供應商與項目關聯記錄"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.MappingID, m.SupplierID, s.SupplierName, m.ItemID, i.ItemName, 
                   m.MOQ, m.Price, m.LeadTime, m.SafetyStockLevel
            FROM SupplierItemMap m
            JOIN Supplier s ON m.SupplierID = s.SupplierID
            JOIN ItemMaster i ON m.ItemID = i.ItemID
            WHERE m.MappingID = ?
        ''', (mapping_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

def update_supplier_item_mapping(mapping_id: int, **kwargs):
    """更新供應商與項目關聯記錄"""
    allowed_fields = {
        "supplier_id": "SupplierID",
        "item_id": "ItemID",
        "moq": "MOQ",
        "price": "Price",
        "lead_time": "LeadTime",
        "safety_stock_level": "SafetyStockLevel"
    }
    fields = []
    values = []

    for param, column in allowed_fields.items():
        if param in kwargs:
            fields.append(f"{column} = ?")
            values.append(kwargs[param])

    if not fields:
        return

    query = f"UPDATE SupplierItemMap SET {', '.join(fields)} WHERE MappingID = ?"
    values.append(mapping_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        logging.info(f"正在更新記錄: MappingID={mapping_id}, 更新欄位={fields}, 值={values[:-1]}")
        cursor.execute(query, tuple(values))

        if "price" in kwargs and kwargs["price"] is not None:
            cursor.execute("SELECT SupplierID, ItemID FROM SupplierItemMap WHERE MappingID = ?", (mapping_id,))
            mapping_data = cursor.fetchone()
            add_price_history_from_mapping(
                supplier_id=mapping_data[0],
                item_id=mapping_data[1],
                price=kwargs["price"],
                effective_date=datetime.now().strftime("%Y-%m-%d"),
                conn=conn
            )

        conn.commit()
        logging.info("成功更新供應商項目映射記錄: MappingID = %d", mapping_id)

def delete_supplier_item_mapping(mapping_id: int) -> bool:
    """刪除指定的供應商與項目關聯記錄，並返回是否成功"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SupplierItemMap WHERE MappingID = ?", (mapping_id,))
        if cursor.rowcount == 0:
            logging.warning("刪除失敗，映射記錄 ID 不存在: MappingID = %d", mapping_id)
            return False
        conn.commit()
        logging.info("已刪除供應商項目映射記錄: MappingID = %d", mapping_id)
        return True
    
def get_safety_stock_level(item_id: int, supplier_id: int) -> float:
    """取得某個 Item 和 Supplier 的安全水位"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SafetyStockLevel 
            FROM SupplierItemMap 
            WHERE ItemID = ? AND SupplierID = ?
        ''', (item_id, supplier_id))
        result = cursor.fetchone()
        return result[0] if result else 0.0
    
def get_latest_supplier_price(supplier_id: int, item_id: int):
    """
    取得指定供應商與品項最新的價格（以每 kg 記錄），若找不到則回傳 None。
    此函式從 SupplierItemMap 表中根據 MappingID 由大到小排序，取最新的一筆價格。
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT Price FROM SupplierItemMap
            WHERE SupplierID = ? AND ItemID = ?
            ORDER BY MappingID DESC
            LIMIT 1
            """,
            (supplier_id, item_id)
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None



# === 測試範例 ===
if __name__ == "__main__":
    # 初始化資料表
    create_tables()

   # 新增測試供應商記錄
    add_supplier(supplier_name="供應商A", address="地址1", contact_person="聯絡人A", phone="0912345678", email="supplierA@example.com")

    # 新增測試產品資料
    add_item(item_name="測試產品", item_type="產品", category="原材料", unit="箱")

    # 新增測試資料
    add_supplier_item_mapping(supplier_id=1, item_id=1, moq=100, price=50.0, lead_time=7)

    # 查詢所有供應商與項目關聯記錄
    mappings = get_supplier_item_mappings()
    for mapping in mappings:
        print(f"MappingID: {mapping['MappingID']}, SupplierName: {mapping['SupplierName']}, ItemName: {mapping['ItemName']}, MOQ: {mapping['MOQ']}, Price: {mapping['Price']}")

    # 更新測試資料
    update_supplier_item_mapping(1, price=55.0)

    # 查詢單筆資料
    mapping = get_supplier_item_mapping_by_id(1)
    print(f"單筆查詢結果: {mapping}")

    # 刪除測試資料
    delete_supplier_item_mapping(1)
    print("已刪除供應商項目映射記錄")
