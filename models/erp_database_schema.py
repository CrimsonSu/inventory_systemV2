from contextlib import contextmanager
import sqlite3

DB_NAME = "erp_system.db"

@contextmanager
def get_connection():
    """取得資料庫連接並啟用外鍵約束"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def create_tables():
    """建立必要的資料表"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Create ItemMaster table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ItemMaster (
                ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemName TEXT NOT NULL,
                ItemType TEXT NOT NULL,       -- 繼續使用文字欄位而不拆分表格
                Category TEXT,               -- 繼續使用文字欄位而不拆分表格
                Unit TEXT,
                Status TEXT DEFAULT 'active',
                UNIQUE(ItemName, ItemType)
             );
        ''')

        # Create Customer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Customer (
                CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerName TEXT NOT NULL,
                Address TEXT,
                Address2 TEXT,
                TaxID TEXT , 
                ContactPerson TEXT,
                Phone TEXT,
                Email TEXT,
                UNIQUE(CustomerName, TaxID)  -- 防止相同名稱與稅號的客戶重複
             );
        ''')

        # Create Stock table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Stock (
                StockID INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemID INTEGER NOT NULL,
                WarehouseID INTEGER,
                Quantity REAL NOT NULL CHECK(Quantity >= 0),
                BatchNo TEXT,
                ExpireDate DATE,
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID),
                UNIQUE(ItemID, BatchNo, WarehouseID)
             );
        ''')

        # Create StockMovement table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS StockMovement (
                MovementID INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemID INTEGER NOT NULL,
                MovementType TEXT NOT NULL,
                Quantity REAL NOT NULL,
                MovementDate DATE NOT NULL,
                RefDocType TEXT,
                RefDocID INTEGER,
                BatchNo TEXT,
                SupplierID INTEGER,  -- 新增欄位
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
                FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
            );
        ''')

        # Create Supplier table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Supplier (
                SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
                SupplierName TEXT NOT NULL,
                Address TEXT,
                ContactPerson TEXT,
                Phone TEXT,
                Email TEXT,
                Website TEXT,
                TaxID TEXT
                
            );
        ''')

        # Create SupplierItemMap table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SupplierItemMap (
                MappingID INTEGER PRIMARY KEY AUTOINCREMENT,
                SupplierID INTEGER NOT NULL,
                ItemID INTEGER NOT NULL,
                MOQ INTEGER,
                Price REAL,
                LeadTime INTEGER,
                SafetyStockLevel REAL DEFAULT 0.0,  -- 新增安全水位欄位，預設為 0
                FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID),
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
                UNIQUE(SupplierID, ItemID)  -- 添加唯一性約束
            );
        ''')

        # Create BOMHeader table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BOMHeader (
                BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductID INTEGER NOT NULL,
                Version TEXT NOT NULL,
                EffectiveDate DATE NOT NULL,
                ProductWeight REAL,   -- 新增的欄位       
                ExpireDate DATE,
                Remarks TEXT,
                FOREIGN KEY (ProductID) REFERENCES ItemMaster(ItemID)
            );
        ''')

        # Create BOMDetail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BOMDetail (
                BOMDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                BOMID INTEGER NOT NULL,
                ComponentItemID INTEGER NOT NULL,
                Quantity REAL NOT NULL CHECK(Quantity > 0),
                Unit TEXT,
                ScrapRate REAL CHECK(ScrapRate BETWEEN 0.0 AND 1.0),
                SupplierID INTEGER,    -- 新增欄位
                Price REAL,            -- 新增欄位 (存每公克價格)
                FOREIGN KEY (BOMID) REFERENCES BOMHeader(BOMID),
                FOREIGN KEY (ComponentItemID) REFERENCES ItemMaster(ItemID),
                UNIQUE(BOMID, ComponentItemID)
            );
        ''')


        # Create SalesOrderHeader table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SalesOrderHeader (
                OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID INTEGER NOT NULL,
                OrderDate DATE NOT NULL,
                Status TEXT NOT NULL,
                FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
            );
        ''')

        # Create SalesOrderDetail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SalesOrderDetail (
                OrderDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                OrderID INTEGER NOT NULL,
                ItemID INTEGER NOT NULL,
                Quantity REAL NOT NULL,
                Price REAL NOT NULL,
                ShippedQuantity REAL DEFAULT 0.0,
                IsDeleted BOOLEAN DEFAULT 0,
                FOREIGN KEY (OrderID) REFERENCES SalesOrderHeader(OrderID),
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID),
                UNIQUE(OrderID, ItemID)  -- 新增約束防止重複商品
            );
        ''')

        # Create ProductionOrderHeader table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProductionOrderHeader (
                ProductionOrderID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductID INTEGER NOT NULL,
                OrderDate DATE NOT NULL,
                Status TEXT NOT NULL,
                IsDeleted BOOLEAN DEFAULT 0,
                FOREIGN KEY (ProductID) REFERENCES ItemMaster(ItemID)
            );
        ''')

        # Create ProductionOrderDetail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProductionOrderDetail (
                ProductionDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductionOrderID INTEGER NOT NULL,
                ItemID INTEGER NOT NULL,
                PlannedQty REAL NOT NULL,
                ActualQty REAL,
                FOREIGN KEY (ProductionOrderID) REFERENCES ProductionOrderHeader(ProductionOrderID),
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
            );
        ''')

        # Create PurchaseOrderHeader table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PurchaseOrderHeader (
                POID INTEGER PRIMARY KEY AUTOINCREMENT,
                SupplierID INTEGER NOT NULL,
                OrderDate DATE NOT NULL,
                ExpectedDeliveryDate DATE,
                Status TEXT NOT NULL,
                FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
            );
        ''')

        # Create PurchaseOrderDetail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PurchaseOrderDetail (
                PODetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                POID INTEGER NOT NULL,
                ItemID INTEGER NOT NULL,
                OrderedQty REAL NOT NULL,
                ReceivedQty REAL,
                Price REAL NOT NULL,
                BatchNo TEXT,
                ProductionDate DATE,
                ExpiryDate DATE,
                FOREIGN KEY (POID) REFERENCES PurchaseOrderHeader(POID),
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
            );
        ''')


        # Create ShipmentHeader table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ShipmentHeader (
                ShipmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                OrderID INTEGER NOT NULL,
                ShipmentDate DATE NOT NULL,
                Status TEXT NOT NULL,
                FOREIGN KEY (OrderID) REFERENCES SalesOrderHeader(OrderID)
            );
        ''')

        # Create ShipmentDetail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ShipmentDetail (
                ShipmentDetailID INTEGER PRIMARY KEY AUTOINCREMENT,
                ShipmentID INTEGER NOT NULL,
                ItemID INTEGER NOT NULL,
                Quantity REAL NOT NULL,
                FOREIGN KEY (ShipmentID) REFERENCES ShipmentHeader(ShipmentID),
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
            );
        ''')

        # Create PriceHistory table (optional)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PriceHistory (
                PriceHistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                ItemID INTEGER NOT NULL,
                EffectiveDate DATE NOT NULL,
                Price REAL NOT NULL CHECK(Price > 0),
                LastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 新增此欄位
                FOREIGN KEY (ItemID) REFERENCES ItemMaster(ItemID)
            );
        ''')

        # [新增] 建立 CostHistory 資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CostHistory (
                CostHistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductName TEXT NOT NULL,
                Price REAL NOT NULL,
                UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # 添加索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_item_map_supplier ON SupplierItemMap(SupplierID)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_item_map_item ON SupplierItemMap(ItemID)")

        conn.commit()
  
def initialize_database():
    """初始化資料庫（集中建立資料表）"""
    create_tables()
    print("資料表已初始化完成")

if __name__ == "__main__":
    # 主程式執行初始化
    initialize_database()