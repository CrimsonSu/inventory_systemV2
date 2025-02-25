from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
                            QMessageBox, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt
from models.supplieritemmap_crud import (get_supplier_item_mappings, delete_supplier_item_mapping,
                                        get_supplier_item_mapping_by_id, get_connection)
from ui.dialogs.supplieritemmap_dialog import SupplierItemMapDialog
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication

class SupplierItemMapPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 顶部工具栏
        tool_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("新增关联", self)
        self.btn_add.clicked.connect(self.add_mapping)
        tool_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("编辑关联", self)
        self.btn_edit.clicked.connect(self.edit_mapping)
        tool_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("删除关联", self)
        self.btn_delete.clicked.connect(self.delete_mapping)
        tool_layout.addWidget(self.btn_delete)
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("输入供应商或产品搜索...")
        self.search_input.textChanged.connect(self.search_mappings)
        tool_layout.addWidget(self.search_input)
        
        main_layout.addLayout(tool_layout)
        
# 關聯表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)  # 新增安全水位欄位
        self.table.setHorizontalHeaderLabels(["ID", "供應商名稱", "產品名稱", "MOQ", "價格", "交期", "安全水位"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
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
        
        # 更新查詢以包含 SafetyStockLevel
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.MappingID, m.SupplierID, s.SupplierName, m.ItemID, i.ItemName, 
                    m.MOQ, m.Price, m.LeadTime, m.SafetyStockLevel
                FROM SupplierItemMap m
                JOIN Supplier s ON m.SupplierID = s.SupplierID
                JOIN ItemMaster i ON m.ItemID = i.ItemID
            ''')
            columns = [col[0] for col in cursor.description]
            mappings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if search_text:
            search = search_text.lower()
            mappings = [m for m in mappings if 
                        search in m["SupplierName"].lower() or 
                        search in m["ItemName"].lower()]

        for row, mapping in enumerate(mappings):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(mapping["MappingID"])))
            self.table.setItem(row, 1, QTableWidgetItem(mapping["SupplierName"]))
            self.table.setItem(row, 2, QTableWidgetItem(mapping["ItemName"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(mapping["MOQ"] or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(mapping["Price"] or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(mapping["LeadTime"] or "")))
            self.table.setItem(row, 6, QTableWidgetItem(f"{mapping['SafetyStockLevel']:.2f}"))  # 顯示安全水位

    def search_mappings(self):
        search_text = self.search_input.text().strip()
        self.load_data(search_text)

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return None
        item = self.table.item(selected_row, 0)
        return int(item.text()) if item else None

    def add_mapping(self):
        dialog = SupplierItemMapDialog(self)
        if dialog.exec_():
            self.load_data()

    def edit_mapping(self):
        mapping_id = self.get_selected_id()
        if not mapping_id:
            QMessageBox.warning(self, "警告", "请先选择要编辑的关联")
            return

        dialog = SupplierItemMapDialog(self, mapping_id)
        if dialog.exec_():
            self.load_data()

    def delete_mapping(self):
        mapping_id = self.get_selected_id()
        if not mapping_id:
            QMessageBox.warning(self, "警告", "请先选择要删除的关联")
            return

        confirm = QMessageBox.question(
            self, "确认删除",
            "确定要删除此关联吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success = delete_supplier_item_mapping(mapping_id)
            if success:
                QMessageBox.information(self, "成功", "关联已删除")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", "删除失败")

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_mapping()
        elif action == delete_action:
            self.delete_mapping()