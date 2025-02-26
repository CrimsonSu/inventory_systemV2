from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QHeaderView, QAbstractItemView, QMessageBox, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from models.salesorderheader_crud import get_sales_orders, delete_sales_order, get_sales_order_by_id
from ui.dialogs.salesorder_dialog import SalesOrderDialog
from ui.dialogs.salesorder_detail_dialog import SalesOrderDetailDialog

class SalesOrderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        tool_layout = QHBoxLayout()
        self.btn_add = QPushButton("新增訂單", self)
        self.btn_add.clicked.connect(self.add_order)
        tool_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("編輯訂單", self)
        self.btn_edit.clicked.connect(self.edit_order)
        tool_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("刪除訂單", self)
        self.btn_delete.clicked.connect(self.delete_order)
        tool_layout.addWidget(self.btn_delete)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入客戶名稱或訂單 ID 搜索...")
        self.search_input.textChanged.connect(self.search_orders)
        tool_layout.addWidget(self.search_input)

        main_layout.addLayout(tool_layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["訂單 ID", "客戶名稱", "日期", "成品與數量", "狀態"])  # 對調順序
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellClicked.connect(self.select_row)
        self.table.cellDoubleClicked.connect(self.show_detail)
        main_layout.addWidget(self.table)

    def select_row(self, row, column):
        self.table.selectRow(row)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            selected = self.table.selectedItems()
            if selected:
                QApplication.clipboard().setText(selected[0].text())

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        orders = get_sales_orders()
        
        if search_text:
            search_text = search_text.lower()
            orders = [o for o in orders if search_text in o["CustomerName"].lower() or search_text in str(o["OrderID"])]

        for row, order in enumerate(orders):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(order["OrderID"])))
            self.table.setItem(row, 1, QTableWidgetItem(order["CustomerName"]))
            self.table.setItem(row, 2, QTableWidgetItem(order["OrderDate"]))
            self.table.setItem(row, 3, QTableWidgetItem(order["Items"] or "無明細"))  # 成品與數量
            self.table.setItem(row, 4, QTableWidgetItem(order["Status"]))  # 狀態

    def search_orders(self):
        self.load_data(self.search_input.text().strip())

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return None
        item = self.table.item(selected_row, 0)
        return int(item.text()) if item else None

    def add_order(self):
        dialog = SalesOrderDialog(self)
        if dialog.exec_():
            self.load_data()
            order_id = dialog.order_id
            self.show_detail(order_id=order_id)

    def edit_order(self):
        order_id = self.get_selected_id()
        if not order_id:
            QMessageBox.warning(self, "警告", "請先選擇要編輯的訂單")
            return
        order = get_sales_order_by_id(order_id)
        if order["Status"] != "Pending":
            QMessageBox.warning(self, "警告", "僅能編輯待處理狀態的訂單")
            return
        dialog = SalesOrderDialog(self, order_id)
        if dialog.exec_():
            self.load_data()

    def delete_order(self):
        order_id = self.get_selected_id()
        if not order_id:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的訂單")
            return
        order = get_sales_order_by_id(order_id)
        if order["Status"] != "Pending":
            QMessageBox.warning(self, "警告", "僅能刪除待處理狀態的訂單")
            return
        confirm = QMessageBox.question(self, "確認刪除", "確定要刪除此訂單嗎？", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_sales_order(order_id)
            QMessageBox.information(self, "成功", "訂單已刪除")
            self.load_data()

    def show_detail(self, row=None, column=None, order_id=None):
        if order_id is None:
            order_id = self.get_selected_id()
        if not order_id:
            QMessageBox.warning(self, "警告", "請先選擇訂單")
            return
        dialog = SalesOrderDetailDialog(order_id, self)
        dialog.exec_()

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("編輯")
        delete_action = menu.addAction("刪除")
        detail_action = menu.addAction("查看詳情")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_order()
        elif action == delete_action:
            self.delete_order()
        elif action == detail_action:
            self.show_detail()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = SalesOrderPage()
    window.setWindowTitle("訂單管理頁面")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())