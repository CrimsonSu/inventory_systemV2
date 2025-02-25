from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QColor
from models.erp_database_schema import get_connection
from models.itemmaster_crud import get_items
from models.supplier_crud import get_suppliers
from models.supplieritemmap_crud import get_safety_stock_level

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
        self.table.setColumnCount(4)  # 新增安全水位欄位
        self.table.setHorizontalHeaderLabels(["物品名稱", "供應商", "庫存量", "安全水位"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.table)

    def calculate_stock(self):
        """計算每個 Item 和 Supplier 的庫存量，並加入安全水位"""
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
            stock_data = [dict(zip(["ItemID", "SupplierID", "StockQuantity"], row)) for row in cursor.fetchall()]
            
            # 加入安全水位
            for stock in stock_data:
                stock["SafetyStockLevel"] = get_safety_stock_level(stock["ItemID"], stock["SupplierID"])
            return stock_data

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        stock_data = self.calculate_stock()
        items = {item["ItemID"]: item["ItemName"] for item in get_items()}
        suppliers = {sup["SupplierID"]: sup["SupplierName"] for sup in get_suppliers()}

        # 過濾搜尋結果
        if search_text:
            search_text = search_text.lower()
            stock_data = [s for s in stock_data if 
                          search_text in items.get(s["ItemID"], "").lower() or 
                          search_text in suppliers.get(s["SupplierID"], "").lower()]

        # 按庫存量與安全水位比較進行排序，低於安全水位的優先
        stock_data.sort(key=lambda x: x["StockQuantity"] < x["SafetyStockLevel"], reverse=True)

        for row, stock in enumerate(stock_data):
            self.table.insertRow(row)
            item_name = items.get(stock["ItemID"], "未知物品")
            supplier_name = suppliers.get(stock["SupplierID"], "未知供應商")
            stock_qty = stock["StockQuantity"]
            safety_level = stock["SafetyStockLevel"]

            self.table.setItem(row, 0, QTableWidgetItem(item_name))
            self.table.setItem(row, 1, QTableWidgetItem(supplier_name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{stock_qty:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{safety_level:.2f}"))

            # 如果庫存低於安全水位，設為紅色背景
            if stock_qty < safety_level:
                for col in range(4):
                    self.table.item(row, col).setBackground(QColor(255, 0, 0, 100))  # 半透明紅色

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