from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
                            QMessageBox, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt
from models.pricehistory_crud import get_price_history, delete_price_history
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication

class PriceHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 搜索欄
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入供應商或產品名稱搜索...")
        self.search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.search_input)
        
        # 刪除按鈕
        self.btn_delete = QPushButton("刪除記錄", self)
        self.btn_delete.clicked.connect(self.delete_history)
        search_layout.addWidget(self.btn_delete)
        
        main_layout.addLayout(search_layout)
        
        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "供應商", "產品", "價格", "生效日期", "最後更新"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.table)

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        history = get_price_history(search_text)
        for row, record in enumerate(history):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(record["PriceHistoryID"])))
            self.table.setItem(row, 1, QTableWidgetItem(record["SupplierName"]))
            self.table.setItem(row, 2, QTableWidgetItem(record["ItemName"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{record['Price']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(record["EffectiveDate"]))
            self.table.setItem(row, 5, QTableWidgetItem(record["LastUpdated"]))

    def search_history(self):
        self.load_data(self.search_input.text().strip())

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return None
        return int(self.table.item(selected_row, 0).text())

    def delete_history(self):
        history_id = self.get_selected_id()
        if not history_id:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的記錄")
            return

        confirm = QMessageBox.question(
            self, "確認刪除", "確定要刪除此價格記錄嗎？", QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            delete_price_history(history_id)
            self.load_data()
            QMessageBox.information(self, "成功", "記錄已刪除")

    def show_context_menu(self, pos):
        menu = QMenu()
        delete_action = menu.addAction("刪除")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == delete_action:
            self.delete_history()