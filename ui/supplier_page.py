from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,QLabel,
                            QMessageBox, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt
from models.supplier_crud import get_suppliers, delete_supplier
from ui.dialogs.supplier_dialog import SupplierDialog
from PyQt5.QtWidgets import QInputDialog, QLineEdit
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication

class SupplierPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 顶部工具栏
        tool_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("新增供應商", self)
        self.btn_add.clicked.connect(self.add_supplier)
        tool_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("編輯供應商", self)
        self.btn_edit.clicked.connect(self.edit_supplier)
        tool_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("刪除供應商", self)
        self.btn_delete.clicked.connect(self.delete_supplier)
        tool_layout.addWidget(self.btn_delete)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入名稱或電話搜索...")
        self.search_input.textChanged.connect(self.search_suppliers)
        tool_layout.addWidget(self.search_input)
        
        main_layout.addLayout(tool_layout)
        
        # 供應商表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "供應商名稱", "統一編號", "聯絡人", "電話", "網站"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        
        # 表格配置
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellClicked.connect(self.select_row)

        main_layout.addWidget(self.table)

    def select_row(self, row, column):
        self.table.selectRow(row)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            selected = self.table.selectedItems()
            if selected:
                clipboard = QApplication.clipboard()
                clipboard.setText(selected[0].text())

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        suppliers = get_suppliers(search_text) or [] # ✅ [修改] 傳入 search_text 以啟用搜尋功能

        if not suppliers:  # ✅ 如果沒有找到供應商，顯示提示，不讓程式崩潰
            QMessageBox.information(self, "搜尋結果", "沒有找到符合條件的供應商！")
            return  # ✅ 防止後續程式繼續執行，導致錯誤
        
        for row, supplier in enumerate(suppliers):
            if supplier is None:  # ✅ 確保 supplier 不是 None
                continue

            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(supplier.get("SupplierID", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(supplier.get("SupplierName", "")))
            self.table.setItem(row, 2, QTableWidgetItem(supplier.get("TaxID", "")))
            self.table.setItem(row, 3, QTableWidgetItem(supplier.get("ContactPerson", "")))
            self.table.setItem(row, 4, QTableWidgetItem(supplier.get("Phone", "")))

       # ✅ 設定超連結網址
            website_url = (supplier.get("Website") or "").strip()
        if website_url:
            website_label = QLabel()
            website_label.setText(f'<a href="{website_url}">{website_url}</a>')  # 確保網址是 HTML 格式
            website_label.setOpenExternalLinks(True)  # ✅ 允許點擊直接開啟外部網站
            website_label.setTextInteractionFlags(Qt.TextBrowserInteraction)  # 允許點擊
            website_label.setStyleSheet("color: blue; text-decoration: underline;")  # 設定藍色連結
            self.table.setCellWidget(row, 5, website_label)  # ✅ 將 QLabel 放入表格
        
        self.table.viewport().update()  # 確保 UI 立即刷新  

    def search_suppliers(self):
        search_text = self.search_input.text().strip()
        self.load_data(search_text)

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return None
        item = self.table.item(selected_row, 0)
        return int(item.text()) if item else None

    def add_supplier(self):
        dialog = SupplierDialog(self)
        if dialog.exec_():
            self.load_data()
            
    def edit_supplier(self):
        supplier_id = self.get_selected_id()
        if not supplier_id:
            QMessageBox.warning(self, "警告", "請先選擇要編輯的供應商")
            return

        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入編輯密碼：", QLineEdit.Password)
        if not ok or password != "":
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法編輯供應商")
            return

        dialog = SupplierDialog(self, supplier_id)
        if dialog.exec_():
            self.load_data()

    def delete_supplier(self):
        supplier_id = self.get_selected_id()
        if not supplier_id:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的供應商")
            return

        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入密碼：", QLineEdit.Password)
        if not ok or password != "":
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法刪除供應商")
            return

        confirm = QMessageBox.question(
            self, "確認刪除",
            "確定要刪除此供應商嗎？此操作不可恢復！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            result = delete_supplier(supplier_id)

            if "失敗" in result:
                QMessageBox.warning(self, "刪除失敗", result)
            else:
                QMessageBox.information(self, "刪除成功", result)
                self.load_data()
 

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("編輯")
        delete_action = menu.addAction("刪除")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_supplier()
        elif action == delete_action:
            self.delete_supplier()