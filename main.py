from erp_database_schema import create_tables
from itemmaster_crud import add_item, get_items, update_item, get_item_by_id, delete_item
from stock_crud import add_stock, get_stocks, update_stock, delete_stock
from supplier_crud import add_supplier, get_suppliers, update_supplier, delete_supplier
from stockmovement_crud import add_stock_movement, get_stock_movements, delete_stock_movement
from supplieritemmap_crud import (
    add_supplier_item_mapping,
    get_supplier_item_mappings,
    get_supplier_item_mapping_by_id,
    update_supplier_item_mapping,
    delete_supplier_item_mapping
)

def test_erp_system():
    """測試 ERP 系統的整合功能"""

    # 1. 初始化資料表
    create_tables()

    # 2. 測試 ItemMaster
    print("\n--- 測試 ItemMaster ---")
    add_item("測試原料", "原料", "食品添加物", "公斤")
    items = get_items()
    print("所有項目:", items)
    update_item(1, new_name="更新後的原料")
    print("單筆項目:", get_item_by_id(1))
    delete_item(1)
    print("刪除後項目:", get_items())

    # 3. 測試 Supplier
    print("\n--- 測試 Supplier ---")
    add_supplier(supplier_name="供應商A", address="地址1", contact_person="聯絡人A", phone="0912345678", email="supplierA@example.com")
    print("所有供應商:", get_suppliers())
    update_supplier(1, address="新地址")
    print("更新後供應商:", get_suppliers())
    delete_supplier(1)
    print("刪除後供應商:", get_suppliers())

    # 4. 測試 Stock
    print("\n--- 測試 Stock ---")
    add_stock(item_id=1, warehouse_id=1, quantity=100, batch_no="B001", expire_date="2025-12-31")
    print("所有庫存:", get_stocks())
    update_stock(stock_id=1, new_quantity=150)
    print("更新後庫存:", get_stocks())
    delete_stock(1)
    print("刪除後庫存:", get_stocks())


    # 5. 測試 StockMovement
def test_stock_movement():
    """測試庫存移動的 CRUD 操作"""
    print("\n--- 測試 StockMovement ---")

    # 插入測試庫存移動記錄
    try:
        add_stock_movement(item_id=1, movement_type="IN", quantity=100, movement_date="2025-02-01", batch_no="B001")
        print("成功插入庫存移動記錄")
    except Exception as e:
        print(f"插入庫存移動記錄失敗: {e}")

    # 查詢所有庫存移動記錄
    try:
        movements = get_stock_movements() or []  # 防止 None 或未賦值錯誤
        if movements:
            print("庫存移動記錄:", movements)
        else:
            print("沒有庫存移動記錄")
    except Exception as e:
        print(f"查詢庫存移動記錄失敗: {e}")



    # 6. 測試 SupplierItemMap
    """測試 SupplierItemMap CRUD"""
    print("\n--- 測試 SupplierItemMap ---")

    # 插入前建立供應商與項目
    add_supplier(supplier_name="供應商B", address="地址2", contact_person="聯絡人B", phone="0922222222", email="supplierB@example.com")
    add_item("測試產品B", "產品", "原材料", "箱")

    # 測試插入供應商項目映射
    add_supplier_item_mapping(supplier_id=2, item_id=2, moq=200, price=70.0, lead_time=10)

    # 查詢所有供應商項目映射
    mappings = get_supplier_item_mappings()
    print("所有供應商與項目映射記錄:", mappings)

    # 測試更新映射
    update_supplier_item_mapping(mapping_id=1, price=75.0)
    print("更新後的供應商與項目映射記錄:", get_supplier_item_mapping_by_id(1))

    # 測試刪除映射
    if delete_supplier_item_mapping(1):
        print("成功刪除映射記錄")
    else:
        print("刪除映射記錄失敗")

    print("刪除後的供應商與項目映射記錄:", get_supplier_item_mappings())

if __name__ == "__main__":
    test_erp_system()
