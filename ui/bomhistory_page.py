from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QHeaderView, QAbstractItemView
from models.costhistory_crud import get_cost_history  # 這裡改為 costhistory_crud

class CostHistoryPage(QWidget):  # 修改名稱，因為我們不再顯示 BOM，而是成本歷史
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """ 設定 UI 介面 """
        main_layout = QVBoxLayout(self)

        # 🔹 搜尋欄
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入產品名稱搜尋歷史價格...")
        self.search_input.textChanged.connect(self.search_cost)
        search_layout.addWidget(self.search_input)

        self.btn_search = QPushButton("搜尋", self)
        self.btn_search.clicked.connect(self.search_cost)
        search_layout.addWidget(self.btn_search)

        main_layout.addLayout(search_layout)

        # 🔹 表格顯示歷史價格
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["產品名稱", "價格", "變更時間"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.table)

    def load_data(self, search_text=None):
        """ 讀取歷史價格數據 """
        self.table.setRowCount(0)
        cost_history = get_cost_history()

        if search_text:
            search_text = search_text.lower()
            cost_history = [c for c in cost_history if search_text in c["ProductName"].lower()]

        for row, record in enumerate(cost_history):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(record["ProductName"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"${record['Price']}"))
            self.table.setItem(row, 2, QTableWidgetItem(record["UpdateTime"]))

    def search_cost(self):
        """ 搜尋產品名稱 """
        search_text = self.search_input.text().strip()
        self.load_data(search_text)
