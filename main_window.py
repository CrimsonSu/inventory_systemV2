import sys
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.customer_page import CustomerPage
from ui.supplier_page import SupplierPage
from models.erp_database_schema import initialize_database


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

if __name__ == "__main__":
    initialize_database()
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())