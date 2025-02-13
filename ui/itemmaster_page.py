from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
                            QMessageBox, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt
from models.itemmaster_crud import get_items, delete_item
from ui.dialogs.itemmaster_dialog import ItemDialog
from PyQt5.QtWidgets import QInputDialog, QLineEdit
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication

class ItemMasterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        tool_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("新增物料", self)
        self.btn_add.clicked.connect(self.add_item)
        tool_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("編輯物料", self)
        self.btn_edit.clicked.connect(self.edit_item)
        tool_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("刪除物料", self)
        self.btn_delete.clicked.connect(self.delete_item)
        tool_layout.addWidget(self.btn_delete)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入物料名稱或類型搜索...")
        self.search_input.textChanged.connect(self.search_items)
        tool_layout.addWidget(self.search_input)
        
        main_layout.addLayout(tool_layout)
        
        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "物料名稱", "類型", "類別", "單位"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 表格配置
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
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
        items = get_items()
        
        # 前端搜索过滤
        if search_text:
            search_text = search_text.lower()
            items = [item for item in items 
                    if search_text in item.get("ItemName", "").lower() 
                    or search_text in item.get("ItemType", "").lower()]
        
        for row, item in enumerate(items):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("ItemID", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("ItemName", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("ItemType", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("Category", "")))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("Unit", "")))

    def search_items(self):
        search_text = self.search_input.text().strip()
        self.load_data(search_text)

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "錯誤", "請先選擇要刪除的物料")
            return None
        item = self.table.item(selected_row, 0)
        if not item:
            return None
        return int(item.text())

    def add_item(self):
        dialog = ItemDialog(self)
        if dialog.exec_():
            self.load_data()

    def edit_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "警告", "請先選擇要編輯的物料")
            return
        
        # 密码验证（仿照客户逻辑）
        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入編輯密碼：", QLineEdit.Password)
        if not ok or password != "":
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法編輯物料")
            return

        dialog = ItemDialog(self, item_id)
        if dialog.exec_():
            self.load_data()

    def delete_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的物料")
            return
        
        # 密码验证
        password, ok = QInputDialog.getText(self, "密碼驗證", "請輸入密碼：", QLineEdit.Password)
        if not ok or password != "":
            QMessageBox.warning(self, "錯誤", "密碼錯誤，無法刪除物料")
            return

        confirm = QMessageBox.question(
            self, "確認刪除", "確定要刪除此物料嗎？", QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                delete_item(item_id, soft_delete=True)
                self.load_data()
                QMessageBox.information(self, "成功", "物料已刪除")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"刪除失敗: {str(e)}")

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_item()
        elif action == delete_action:
            self.delete_item()