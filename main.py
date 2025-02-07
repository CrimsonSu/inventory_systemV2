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
from bomheader_crud import (
    add_bom_header,
    get_bom_headers,
    get_bom_header_by_id,
    update_bom_header,
    delete_bom_header
)
from bomdetail_crud import (
    add_bom_detail,
    get_bom_details,
    update_bom_detail,
    delete_bom_detail
)

def test_erp_system():
    """測試 ERP 系統的整合功能"""
    # 初始化資料表
    create_tables()

    # === 測試1 ItemMaster ===
    print("\n--- 測試 ItemMaster ---")
    add_item("測試原料", "原料", "食品添加物", "公斤")
    items = get_items()
    print("所有項目:", items)
    update_item(1, new_name="更新後的原料")
    print("單筆項目:", get_item_by_id(1))

    # === 測試2 Supplier ===
    print("\n--- 測試 Supplier ---")
    add_supplier(supplier_name="供應商A", address="地址1", contact_person="聯絡人A", phone="0912345678", email="supplierA@example.com")
    print("所有供應商:", get_suppliers())
    update_supplier(1, address="新地址")
    print("更新後供應商:", get_suppliers())

    # === 測試3 Stock ===
    print("\n--- 測試 Stock ---")
    add_stock(item_id=1, warehouse_id=1, quantity=100, batch_no="B001", expire_date="2025-12-31")
    print("所有庫存:", get_stocks())
    update_stock(stock_id=1, new_quantity=150)
    print("更新後庫存:", get_stocks())

    # === 測試4 StockMovement ===
    print("\n--- 測試 StockMovement ---")
    try:
        # 使用動態獲取的 ItemID（確保存在）
        item_id = get_item_by_id(1)["ItemID"]
        add_stock_movement(
            item_id=item_id,
            movement_type="IN",
            quantity=100,
            movement_date="2025-02-01",
            batch_no="B001"
        )
        print("成功插入庫存移動記錄")
    except Exception as e:
        print(f"插入庫存移動記錄失敗: {e}")

    # 查詢所有庫存移動記錄
    try:
        movements = get_stock_movements() or []
        if movements:
            print("庫存移動記錄:", movements)
        else:
            print("沒有庫存移動記錄")
    except Exception as e:
        print(f"查詢庫存移動記錄失敗: {e}")

    # === 測試5 SupplierItemMap ===
    print("\n--- 測試 SupplierItemMap ---")
    # 插入前建立供應商與項目
    add_supplier(supplier_name="供應商B", address="地址2", contact_person="聯絡人B", phone="0922222222", email="supplierB@example.com")
    add_item("測試產品B", "產品", "原材料", "箱")

    # 獲取動態生成的 ID
    supplier_id = get_suppliers()[-1]["SupplierID"]  # 最新插入的供應商
    item_id = get_items()[-1]["ItemID"]              # 最新插入的項目

    # 測試插入供應商項目映射
    try:
        add_supplier_item_mapping(supplier_id=supplier_id, item_id=item_id, moq=200, price=70.0, lead_time=10)
        print("成功插入供應商項目映射")
    except Exception as e:
        print(f"插入映射失敗: {e}")

    # 查詢所有供應商項目映射
    mappings = get_supplier_item_mappings()
    print("所有供應商與項目映射記錄:", mappings)

    # === 測試6 BOMHeader ===
    print("\n--- 測試 BOMHeader ---")
    add_item("測試產品", "產品", "原材料", "箱")  # 先新增產品到 ItemMaster
    add_bom_header(product_id=1, version="V1.0", effective_date="2025-02-01", remarks="初始版本")
    
    headers = get_bom_headers()
    print("所有 BOM 頭檔記錄:", headers)

    update_bom_header(1, remarks="更新版本說明")
    updated_header = get_bom_header_by_id(1)
    print("更新後 BOMHeader:", updated_header)

    # === 測試7 BOMDetail ===   
    print("\n--- 測試 BOMDetail ---")
    # 插入前先建立 BOMHeader 和 ItemMaster 記錄
    add_item("測試零件", "零件", "結構材料", "個")
    add_bom_header(product_id=1, version="V1.0", effective_date="2025-02-01", remarks="BOM 測試版本")

    # 新增 BOMDetail
    add_bom_detail(bom_id=1, component_item_id=1, quantity=5.0, unit="個", scrap_rate=0.02)
    bom_details = get_bom_details()
    print("所有 BOM 明細:", bom_details)

    # 更新 BOMDetail
    update_bom_detail(bom_detail_id=1, quantity=10.0, scrap_rate=0.05)
    print("更新後的 BOM 明細:", get_bom_details(bom_id=1))


    # === 清理測試資料（可選） ===
    print("\n--- 清理測試資料 ---")
    # 注意：若需保留測試資料供後續使用，可跳過此步驟
    delete_item(1)
    delete_supplier(1)
    delete_stock(1)
    delete_supplier_item_mapping(1)
    delete_bom_detail(1)
    delete_bom_header(1)

if __name__ == "__main__":
    test_erp_system()
