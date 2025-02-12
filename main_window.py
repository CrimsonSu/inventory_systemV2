import sys
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.customer_page import CustomerPage
from models.erp_database_schema import initialize_database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP System")
        self.setGeometry(200, 100, 1024, 768)
        
        # 初始化分页
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 添加客户分页
        self.customer_page = CustomerPage()
        self.tabs.addTab(self.customer_page, "客戶管理")
        
        # 其他分页后续添加...

if __name__ == "__main__":
    initialize_database()
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())