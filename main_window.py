import sys
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.customer_page import CustomerPage
from ui.supplier_page import SupplierPage
from ui.itemmaster_page import ItemMasterPage
from models.erp_database_schema import initialize_database
from ui.SupplierItemMapPage import SupplierItemMapPage
from ui.pricehistorypage import PriceHistoryPage
from ui.bom_page import BOMPage
from ui.bomhistory_page import CostHistoryPage
from ui.stockmovement_page import StockMovementPage
from ui.stock_page import StockPage
from ui.salesorder_page import SalesOrderPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP System")
        self.setGeometry(200, 100, 1024, 768)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 客戶分頁
        self.customer_page = CustomerPage()
        self.tabs.addTab(self.customer_page, "客戶管理")
        
        # 供應商分頁
        self.supplier_page = SupplierPage()
        self.tabs.addTab(self.supplier_page, "供應商管理")

        # 物料分頁
        self.item_page = ItemMasterPage()
        self.tabs.addTab(self.item_page, "物料管理")

        # 供應商-物料關聯分頁
        self.supplier_item_map_page = SupplierItemMapPage()
        self.tabs.addTab(self.supplier_item_map_page, "供應商-物料關聯")

        # 價格歷史分頁
        self.price_history_page = PriceHistoryPage()
        self.tabs.addTab(self.price_history_page, "價格歷史")

        # BOM分頁
        self.bom_page = BOMPage()
        self.tabs.addTab(self.bom_page, "BOM管理")

        self.bomhistory_page = CostHistoryPage()
        self.tabs.addTab(self.bomhistory_page, "BOM歷史頁面")

        self.stockmovement_page = StockMovementPage()
        self.tabs.addTab(self.stockmovement_page, "進出庫存管理")

        self.stock_page = StockPage()
        self.tabs.addTab(self.stock_page, "庫存管理")   

        self.salesorder_page = SalesOrderPage()
        self.tabs.addTab(self.salesorder_page, "訂單管理")

if __name__ == "__main__":
    initialize_database()
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())