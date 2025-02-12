import sys
import os

# 設定專案根目錄
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 測試導入 models 模組
from models.erp_database_schema import create_tables

def test_create_tables():
    assert create_tables() is not None

from models.erp_database_schema import create_tables
from models.itemmaster_crud import add_item, get_items, update_item, get_item_by_id, delete_item
from models.customer_crud import add_customer, get_customers, get_customer_by_id, update_customer, delete_customer
from models.stock_crud import add_stock, get_stocks, update_stock, delete_stock
from models.supplier_crud import add_supplier, get_suppliers, update_supplier, delete_supplier
from models.stockmovement_crud import add_stock_movement, get_stock_movements, delete_stock_movement
from models.supplieritemmap_crud import add_supplier_item_mapping,get_supplier_item_mappings,get_supplier_item_mapping_by_id,update_supplier_item_mapping,delete_supplier_item_mapping
from models.bomheader_crud import add_bom_header,get_bom_headers,get_bom_header_by_id,update_bom_header,delete_bom_header
from models.bomdetail_crud import add_bom_detail,get_bom_details,update_bom_detail,delete_bom_detail
from models.salesorderheader_crud import add_sales_order,get_sales_orders,get_sales_order_by_id,update_sales_order,delete_sales_order
from models.salesorderdetail_crud import add_sales_order_detail,get_sales_order_details,get_stock_by_item,update_sales_order_detail,delete_sales_order_detail,ship_order_detail
from models.productionorderheader_crud import add_production_order,get_production_orders,get_production_order_by_id,update_production_order,delete_production_order
from models.productionorderdetail_crud import add_production_order_detail,get_production_order_details,update_production_order_detail,delete_production_order_detail
from models.purchaseorderheader_crud import add_purchase_order,get_purchase_orders,update_purchase_order,delete_purchase_order
from models.purchaseorderdetail_crud import add_purchase_order_detail,get_purchase_order_details,update_purchase_order_detail,delete_purchase_order_detail
from models.shipmentheader_crud import add_shipment,get_shipments,update_shipment,delete_shipment
from models.shipmentdetail_crud import add_shipment_detail,get_shipment_details,update_shipment_detail,delete_shipment_detail
from models.pricehistory_crud import add_price_history,get_price_history,update_price_history,delete_price_history

def test_erp_system():
    """測試 ERP 系統的整合功能"""
    # 初始化資料表
    create_tables()

    # === 測試1 ItemMaster ===
    print("\n--- 測試1 ItemMaster ---")
    add_item("測試原料", "原料", "食品添加物", "公斤")
    items = get_items()
    print("所有項目:", items)
    update_item(1, new_name="更新後的原料")
    print("單筆項目:", get_item_by_id(1))

    # === 測試2 Customer ===
    print("\n--- 測試2 Customer ---")
    add_customer(customer_name="測試客戶", address="台北市測試路100號", tax_id="12345678", contact_person="張三", phone="0912345678", email="test_customer@example.com")
    print("所有客戶:", get_customers())
    update_customer(1, address="新地址")

    # === 測試3 Supplier ===
    print("\n--- 測試3 Supplier ---")
    add_supplier(supplier_name="供應商A", address="地址1", contact_person="聯絡人A", phone="0912345678", email="supplierA@example.com")
    print("所有供應商:", get_suppliers())
    update_supplier(1, address="新地址")
    print("更新後供應商:", get_suppliers())

    # === 測試4 Stock ===
    print("\n--- 測試4 Stock ---")
    add_stock(item_id=1, warehouse_id=1, quantity=100, batch_no="B001", expire_date="2025-12-31")
    print("所有庫存:", get_stocks())
    update_stock(stock_id=1, new_quantity=150)
    print("更新後庫存:", get_stocks())

    # === 測試5 StockMovement ===
    print("\n--- 測試5 StockMovement ---")
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

    # === 測試6 SupplierItemMap ===
    print("\n--- 測試6 SupplierItemMap ---")
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

    # === 測試7 BOMHeader ===
    print("\n--- 測試7 BOMHeader ---")
    add_item("測試產品", "產品", "原材料", "箱")  # 先新增產品到 ItemMaster
    add_bom_header(product_id=1, version="V1.0", effective_date="2025-02-01", remarks="初始版本")
    
    headers = get_bom_headers()
    print("所有 BOM 頭檔記錄:", headers)

    update_bom_header(1, remarks="更新版本說明")
    updated_header = get_bom_header_by_id(1)
    print("更新後 BOMHeader:", updated_header)

    # === 測試8 BOMDetail ===   
    print("\n--- 測試8 BOMDetail ---")
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

    # === 測試9 SalesOrderHeader ===
    print("\n--- 測試9 SalesOrderHeader ---")
    add_sales_order(customer_id=1, order_date="2025-02-09", status="Pending")
    print("所有銷售訂單:", get_sales_orders())
    update_sales_order(1, status="Shipped")
    print("更新後銷售訂單:", get_sales_order_by_id(1))  

    # === 測試9 SalesOrderDetail ===
    print("\n--- 測試10 SalesOrderDetail ---")

    # 1. 新增銷售訂單明細
    add_sales_order_detail(order_id=1, item_id=1, quantity=10.0, price=100.0)
    print("新增訂單明細後:", get_sales_order_details(order_id=1))

    # 2. 測試邊界條件 - 重複商品插入
    try:
        add_sales_order_detail(order_id=1, item_id=1, quantity=5.0, price=90.0)
    except ValueError as e:
        print("預期錯誤: 重複商品插入:", e)

    # 3. 更新訂單明細
    update_sales_order_detail(order_detail_id=1, quantity=8.0, price=95.0)
    print("更新後的訂單明細:", get_sales_order_details(order_id=1))

    # 4. 測試邊界條件 - 超量發貨
    try:
        add_sales_order_detail(order_id=2, item_id=2, quantity=10.0, price=100.0, shipped_quantity=12.0)
    except ValueError as e:
        print("預期錯誤: 超量發貨:", e)

    # 5. 測試庫存自動扣減
    try:
        ship_order_detail(order_detail_id=1, shipped_qty=4.0)
        print("發貨後的訂單明細:", get_sales_order_details(order_id=1))
        print("庫存扣減後:", get_stock_by_item(item_id=1))
    except ValueError as e:
        print("發貨失敗:", e)

    # 6. 刪除訂單明細

    # === 測試11 ProductionOrderHeader ===
    print("\n--- 測試11 ProductionOrderHeader ---")
    add_production_order(product_id=1, order_date="2025-02-10", status="Pending")
    print("所有生產訂單:", get_production_orders())
    update_production_order(1, status="In Progress")
    print("更新後生產訂單:", get_production_order_by_id(1))

    # === 測試12 ProductionOrderDetail 模組 ===
    add_production_order_detail(production_order_id=1, item_id=1, planned_qty=100.0)
    print("生產訂單明細:", get_production_order_details(order_id=1))
    update_production_order_detail(production_detail_id=1, actual_qty=90.0)
    print("更新後的生產訂單明細:", get_production_order_details(order_id=1))

    # === 測試13 PurchaseOrder ===
    print("\n--- 測試13 PurchaseOrder ---")
    # 新增採購訂單
    poid = add_purchase_order(supplier_id=1, order_date="2025-02-10", status="Open")
    print("新增採購訂單:", poid)

    # 新增訂單明細
    add_purchase_order_detail(poid=poid, item_id=1, ordered_qty=100.0, price=50.0)
    print("新增後的訂單明細:", get_purchase_order_details(poid=poid))

    # 更新訂單明細
    update_purchase_order_detail(podetail_id=1, received_qty=80.0)
    print("更新後的訂單明細:", get_purchase_order_details(poid=poid))

    # 更新訂單狀態
    update_purchase_order(poid=poid, status="Partial")
    print("更新後訂單:", get_purchase_orders())

    # 刪除訂單明細
    delete_purchase_order_detail(podetail_id=1)
    print("刪除後的訂單明細:", get_purchase_order_details(poid=poid))

    # 刪除訂單
    delete_purchase_order(poid=poid)
    print("成功刪除採購訂單")

    # === 測試14 ShipmentHeader ===
    print("\n--- 測試14 ShipmentHeader ---")

    # 測試出貨單操作
    shipment_id = add_shipment(order_id=1, shipment_date="2025-02-11", status="pending")
    print("新增出貨單:", shipment_id)

    # 測試更新狀態
    try:
        update_shipment(shipment_id, status="shipped")
        print("更新後的出貨單:", get_shipments())
    except ValueError as e:
        print("更新出貨單失敗:", e)

    # 測試出貨明細操作
    add_shipment_detail(shipment_id=shipment_id, item_id=1, quantity=10.0)
    print("新增出貨明細:", get_shipment_details(shipment_id=shipment_id))

    update_shipment_detail(shipment_detail_id=1, quantity=8.0)
    print("更新後出貨明細:", get_shipment_details(shipment_id=shipment_id))

    delete_shipment_detail(shipment_detail_id=1)
    print("刪除後出貨明細:", get_shipment_details(shipment_id=shipment_id))

    # 刪除出貨單
    delete_shipment(shipment_id)
    print("刪除後出貨單:", get_shipments())


    # === 測試15 PriceHistory ===
    print("\n--- 測試15 PriceHistory ---")
    # **1. 新增 Item 以供測試**（避免外鍵錯誤）
    add_item(item_name="測試產品", item_type="原料", category="食品添加物", unit="公斤")
    items = get_items()
    print("所有項目:", items)

    # **2. 新增價格歷史紀錄**
    item_id = items[0]["ItemID"]  # 取得新增的 ItemID
    add_price_history(item_id=item_id, effective_date="2025-02-09", price=100.0)
    print("新增後的價格歷史紀錄:", get_price_history(item_id=item_id))

    # **3. 更新價格歷史紀錄**
    price_history = get_price_history(item_id=item_id)
    if price_history:
        price_history_id = price_history[0]["PriceHistoryID"]
        update_price_history(price_history_id=price_history_id, price=120.0)
        print("更新後的價格歷史紀錄:", get_price_history(item_id=item_id))

    # **4. 刪除價格歷史紀錄**
    delete_price_history(price_history_id=price_history_id)
    print("刪除後的價格歷史紀錄:", get_price_history(item_id=item_id))

    # === 清理測試資料（可選） ===
    print("\n--- 清理測試資料 ---")
    # 注意：若需保留測試資料供後續使用，可跳過此步驟
    delete_production_order_detail(production_detail_id=1)
    delete_sales_order_detail(1)
    delete_bom_detail(1)
    delete_supplier_item_mapping(1)
    delete_stock(1)
    delete_bom_header(1)
    delete_sales_order(1)
    delete_item(1)
    delete_supplier(1)
    delete_customer(1)
    delete_production_order(1)
 
if __name__ == "__main__":
    test_erp_system()

