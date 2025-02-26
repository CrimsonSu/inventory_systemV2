from PyQt5.QtWidgets import (QDialog, QFormLayout, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,QHeaderView,
                            QHBoxLayout, QPushButton, QVBoxLayout, QMessageBox)
from PyQt5.QtCore import QDate
from models.salesorderheader_crud import add_sales_order, update_sales_order, get_sales_order_by_id, get_sales_orders   # 添加 get_sales_order_by_id
from models.salesorderdetail_crud import add_sales_order_detail, update_sales_order_detail, get_sales_order_details
from models.customer_crud import get_customers
from models.itemmaster_crud import get_items
from models.supplieritemmap_crud import get_latest_supplier_price

class SalesOrderDialog(QDialog):
    def __init__(self, parent=None, order_id=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle("新增訂單" if not order_id else "編輯訂單")
        self.resize(800, 600)  # 放大視窗
        self.setup_ui()
        if order_id:
            self.load_order_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.customer_combo = QComboBox()
        customers = get_customers()
        for customer in customers:
            self.customer_combo.addItem(f"{customer['CustomerName']} (ID:{customer['CustomerID']})", customer["CustomerID"])
        form_layout.addRow("客戶*", self.customer_combo)

        self.order_date = QDateEdit()
        self.order_date.setCalendarPopup(True)
        self.order_date.setDate(QDate.currentDate())
        form_layout.addRow("訂單日期*", self.order_date)

        layout.addLayout(form_layout)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(3)
        self.detail_table.setHorizontalHeaderLabels(["成品", "數量", "價格"])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.detail_table)

        add_btn = QPushButton("添加明細")
        add_btn.clicked.connect(self.add_detail_row)
        layout.addWidget(add_btn)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("確定")
        self.btn_ok.clicked.connect(self.validate_and_submit)
        btn_layout.addWidget(self.btn_ok)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def add_detail_row(self):
        row = self.detail_table.rowCount()
        self.detail_table.insertRow(row)
        
        item_combo = QComboBox()
        items = [i for i in get_items() if i["ItemType"] == "成品"]
        for item in items:
            item_combo.addItem(f"{item['ItemName']} (ID:{item['ItemID']})", item["ItemID"])
        item_combo.currentIndexChanged.connect(lambda: self.update_price(row))
        self.detail_table.setCellWidget(row, 0, item_combo)

        self.detail_table.setItem(row, 1, QTableWidgetItem("0"))
        self.detail_table.setItem(row, 2, QTableWidgetItem("0.0"))
        self.update_price(row)  # 初始填充價格

    def update_price(self, row):
        item_combo = self.detail_table.cellWidget(row, 0)
        item_id = item_combo.currentData()
        if item_id:
            price = get_latest_supplier_price(1, item_id)  # 假設 SupplierID=1，需動態獲取
            if price is not None:
                self.detail_table.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
            else:
                self.detail_table.setItem(row, 2, QTableWidgetItem("0.0"))

    def load_order_data(self):
        order = get_sales_order_by_id(self.order_id)
        if not order:
            QMessageBox.warning(self, "錯誤", "訂單不存在")
            self.reject()
            return
        customer_index = self.customer_combo.findData(order["CustomerID"])
        if customer_index >= 0:
            self.customer_combo.setCurrentIndex(customer_index)
        self.order_date.setDate(QDate.fromString(order["OrderDate"], "yyyy-MM-dd"))

        details = get_sales_order_details(self.order_id)
        self.detail_table.setRowCount(0)
        for detail in details:
            row = self.detail_table.rowCount()
            self.detail_table.insertRow(row)
            item_combo = QComboBox()
            items = [i for i in get_items() if i["ItemType"] == "成品"]
            for item in items:
                item_combo.addItem(f"{item['ItemName']} (ID:{item['ItemID']})", item["ItemID"])
            item_index = item_combo.findData(detail["ItemID"])
            if item_index >= 0:
                item_combo.setCurrentIndex(item_index)
            item_combo.currentIndexChanged.connect(lambda: self.update_price(row))
            self.detail_table.setCellWidget(row, 0, item_combo)
            self.detail_table.setItem(row, 1, QTableWidgetItem(str(detail["Quantity"])))
            self.detail_table.setItem(row, 2, QTableWidgetItem(str(detail["Price"])))

    def validate_and_submit(self):
        if self.customer_combo.currentData() is None:
            QMessageBox.warning(self, "錯誤", "請選擇客戶")
            return
        if self.detail_table.rowCount() == 0:
            QMessageBox.warning(self, "錯誤", "請至少添加一筆明細")
            return

        customer_id = self.customer_combo.currentData()
        order_date = self.order_date.date().toString("yyyy-MM-dd")
        status = "Pending"

        if self.order_id:
            update_sales_order(self.order_id, customer_id=customer_id, order_date=order_date)
            details = get_sales_order_details(self.order_id)
            for detail in details:
                update_sales_order_detail(detail["OrderDetailID"], quantity=0)
        else:
            add_sales_order(customer_id, order_date, status)
            self.order_id = get_sales_orders()[-1]["OrderID"]

        for row in range(self.detail_table.rowCount()):
            item_combo = self.detail_table.cellWidget(row, 0)
            item_id = item_combo.currentData()
            quantity = float(self.detail_table.item(row, 1).text() or 0)
            price = float(self.detail_table.item(row, 2).text() or 0)
            if quantity <= 0 or price <= 0:
                QMessageBox.warning(self, "錯誤", "數量與價格必須為正數")
                return
            if self.order_id and row < len(get_sales_order_details(self.order_id)):
                update_sales_order_detail(get_sales_order_details(self.order_id)[row]["OrderDetailID"], 
                                         item_id=item_id, quantity=quantity, price=price)
            else:
                add_sales_order_detail(self.order_id, item_id, quantity, price)

        self.accept()