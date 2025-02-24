from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QDateEdit, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QDate
from models.itemmaster_crud import get_items
from models.supplier_crud import get_suppliers

class StockMovementDialog(QDialog):
    def __init__(self, parent=None, movement=None):
        super().__init__(parent)
        self.movement = movement
        self.setWindowTitle("新增庫存移動" if not self.movement else "編輯庫存移動")
        self.setup_ui()
        if self.movement:
            self.load_movement_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        # 物品選擇（支援搜尋）
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        self.item_combo.setInsertPolicy(QComboBox.NoInsert)  # 禁止插入不存在的項目
        self.items = get_items()
        self.item_map = {f"{item['ItemName']} (ID:{item['ItemID']})": item['ItemID'] for item in self.items}
        self.item_combo.addItems(self.item_map.keys())
        self.item_combo.setCurrentText("")  # 預設空白
        layout.addRow("物品*", self.item_combo)

        # 供應商選擇（支援搜尋）
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.setInsertPolicy(QComboBox.NoInsert)  # 禁止插入不存在的項目
        self.suppliers = get_suppliers()
        self.supplier_map = {f"{sup['SupplierName']} (ID:{sup['SupplierID']})": sup['SupplierID'] for sup in self.suppliers}
        self.supplier_combo.addItems(self.supplier_map.keys())
        self.supplier_combo.setCurrentText("")  # 預設空白
        layout.addRow("供應商*", self.supplier_combo)

        # 移動類型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["IN", "OUT"])
        layout.addRow("移動類型*", self.type_combo)

        # 數量
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0.01)
        self.quantity_input.setMaximum(1000000.0)
        self.quantity_input.setDecimals(2)
        layout.addRow("數量*", self.quantity_input)

        # 移動日期
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        layout.addRow("移動日期*", self.date_input)

        # 批次號
        self.batch_no_input = QLineEdit()
        layout.addRow("批次號", self.batch_no_input)

        # 按鈕
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("確定")
        self.btn_ok.clicked.connect(self.validate_and_submit)
        btn_layout.addWidget(self.btn_ok)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

    def load_movement_data(self):
        if self.movement:
            # 載入物品
            item_key = next((k for k, v in self.item_map.items() if v == self.movement["ItemID"]), "")
            self.item_combo.setCurrentText(item_key)
            # 載入供應商
            supplier_key = next((k for k, v in self.supplier_map.items() if v == self.movement.get("SupplierID")), "")
            self.supplier_combo.setCurrentText(supplier_key)
            # 載入移動類型
            self.type_combo.setCurrentText(self.movement["MovementType"])
            # 載入數量
            self.quantity_input.setValue(self.movement["Quantity"])
            # 載入日期
            date = QDate.fromString(self.movement["MovementDate"], "yyyy-MM-dd")
            if date.isValid():
                self.date_input.setDate(date)
            # 載入批次號
            self.batch_no_input.setText(self.movement.get("BatchNo", ""))

    def validate_and_submit(self):
        item_text = self.item_combo.currentText()
        supplier_text = self.supplier_combo.currentText()

        # 驗證物品是否存在
        if item_text not in self.item_map:
            QMessageBox.warning(self, "錯誤", "請選擇有效的物品")
            return
        # 驗證供應商是否存在
        if supplier_text not in self.supplier_map:
            QMessageBox.warning(self, "錯誤", "請選擇有效的供應商")
            return
        # 驗證數量
        if self.quantity_input.value() <= 0:
            QMessageBox.warning(self, "錯誤", "數量必須大於 0")
            return

        self.accept()

    def get_movement_data(self):
        return {
            "item_id": self.item_map[self.item_combo.currentText()],
            "supplier_id": self.supplier_map[self.supplier_combo.currentText()],
            "movement_type": self.type_combo.currentText(),
            "quantity": self.quantity_input.value(),
            "movement_date": self.date_input.date().toString("yyyy-MM-dd"),
            "batch_no": self.batch_no_input.text().strip()
        }