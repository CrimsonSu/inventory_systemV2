from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QAbstractItemView
from models.erp_database_schema import get_connection
from models.itemmaster_crud import get_items
from models.supplier_crud import get_suppliers

class StockPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 搜尋工具列
        tool_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜尋物品名稱或供應商...")
        self.search_input.textChanged.connect(self.search_stock)
        tool_layout.addWidget(self.search_input)

        main_layout.addLayout(tool_layout)

        # 庫存表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["物品名稱", "供應商", "庫存量"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.table)

    def calculate_stock(self):
        """計算每個 Item 和 Supplier 的庫存量"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ItemID, SupplierID,
                       SUM(CASE WHEN MovementType = 'IN' THEN Quantity ELSE 0 END) -
                       SUM(CASE WHEN MovementType = 'OUT' THEN Quantity ELSE 0 END) AS StockQuantity
                FROM StockMovement
                GROUP BY ItemID, SupplierID
                HAVING StockQuantity IS NOT NULL
            ''')
            return [dict(zip(["ItemID", "SupplierID", "StockQuantity"], row)) for row in cursor.fetchall()]

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        stock_data = self.calculate_stock()
        items = {item["ItemID"]: item["ItemName"] for item in get_items()}
        suppliers = {sup["SupplierID"]: sup["SupplierName"] for sup in get_suppliers()}

        if search_text:
            search_text = search_text.lower()
            stock_data = [s for s in stock_data if 
                          search_text in items.get(s["ItemID"], "").lower() or 
                          search_text in suppliers.get(s["SupplierID"], "").lower()]

        for row, stock in enumerate(stock_data):
            self.table.insertRow(row)
            item_name = items.get(stock["ItemID"], "未知物品")
            supplier_name = suppliers.get(stock["SupplierID"], "未知供應商")
            self.table.setItem(row, 0, QTableWidgetItem(item_name))
            self.table.setItem(row, 1, QTableWidgetItem(supplier_name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{stock['StockQuantity']:.2f}"))

    def search_stock(self):
        self.load_data(self.search_input.text().strip())

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = StockPage()
    window.setWindowTitle("庫存管理頁面")
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())