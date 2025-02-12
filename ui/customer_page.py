from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
                            QMessageBox, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt
from models.customer_crud import get_customers, delete_customer
from ui.dialogs.customer_dialog import CustomerDialog
from PyQt5.QtWidgets import QInputDialog, QLineEdit
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication

class CustomerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()
        


    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 顶部工具栏
        tool_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("新增客戶", self)
        self.btn_add.clicked.connect(self.add_customer)
        tool_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("編輯客戶", self)
        self.btn_edit.clicked.connect(self.edit_customer)
        tool_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("刪除客戶", self)
        self.btn_delete.clicked.connect(self.delete_customer)
        tool_layout.addWidget(self.btn_delete)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("输入姓名或电话搜索...")
        self.search_input.textChanged.connect(self.search_customers)
        tool_layout.addWidget(self.search_input)
        
        main_layout.addLayout(tool_layout)
        
        # 客户表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "客戶名稱", "統一編號", "聯絡人", "電話", "地址", "送貨地址"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 讓表格變成唯讀模式
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止直接編輯
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)  # 允許點選單個儲存格
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)  # 允許點選儲存格內容

        main_layout.addWidget(self.table)

        # 样式微调建议（可在代码中直接修改）
        # 1. 表格行高：self.table.verticalHeader().setDefaultSectionSize(30)
        # 2. 按钮图标：可使用QIcon添加图标
        # 3. 搜索框样式：可设置圆角边框

    def keyPressEvent(self, event):
        """ 允許 Ctrl+C / Command+C 複製選取的儲存格內容 """
        if event.matches(QKeySequence.Copy):
            selected = self.table.selectedItems()
            if selected:
                clipboard = QApplication.clipboard()
                clipboard.setText(selected[0].text())  # 複製選取儲存格的內容
    
    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        customers = get_customers(search_text)
        
        for row, customer in enumerate(customers):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(customer.get("CustomerID", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(customer.get("CustomerName", "")))
            self.table.setItem(row, 2, QTableWidgetItem(customer.get("TaxID", "")))
            self.table.setItem(row, 3, QTableWidgetItem(customer.get("ContactPerson", "")))
            self.table.setItem(row, 4, QTableWidgetItem(customer.get("Phone", "")))
            self.table.setItem(row, 5, QTableWidgetItem(customer.get("Address", "")))
            self.table.setItem(row, 6, QTableWidgetItem(customer.get("Address2", "")))
    
    def search_customers(self):
        search_text = self.search_input.text().strip()
        self.load_data(search_text)
    
    def get_selected_id(self):
        selected = self.table.selectedItems()
        return int(selected[0].text()) if selected else None
    
    def add_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec_():
            self.load_data()
            
    def edit_customer(self):
        customer_id = self.get_selected_id()
        if not customer_id:
            QMessageBox.warning(self, "警告", "请先选择要编辑的客户")
            return
        
        # 🔐 讓使用者輸入密碼來編輯
        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入編輯密碼：", QLineEdit.Password)
        if not ok or password != "9007":  # 這裡的密碼可以換成從資料庫或設定檔讀取
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法編輯客戶")
            return
    
            
        dialog = CustomerDialog(self, customer_id)
        if dialog.exec_():
            self.load_data()
    
    def delete_customer(self):
        customer_id = self.get_selected_id()
        if not customer_id:
            QMessageBox.warning(self, "警告", "请先选择要删除的客户")
            return
        
            # 輸入密碼確認刪除
        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入管理員密碼：", QLineEdit.Password)
        if not ok or password != "0988773302":  # 這裡密碼可以改成從設定檔或資料庫讀取
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法刪除客戶")
            return

        confirm = QMessageBox.question(
            self, "确认删除", 
            "确定要删除该客户吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            delete_customer(customer_id)
            self.load_data()
    
    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_customer()
        elif action == delete_action:
            self.delete_customer()