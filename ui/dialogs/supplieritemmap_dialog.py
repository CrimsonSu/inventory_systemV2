from PyQt5.QtWidgets import (QDialog, QFormLayout, QComboBox, QLineEdit, 
                            QDialogButtonBox, QMessageBox, QDoubleSpinBox, QSpinBox, QCompleter)
from PyQt5.QtCore import Qt
from models.supplieritemmap_crud import (add_supplier_item_mapping, update_supplier_item_mapping,
                                        get_supplier_item_mapping_by_id)
from models.supplier_crud import get_suppliers
from models.itemmaster_crud import get_items

class SupplierItemMapDialog(QDialog):
    def __init__(self, parent=None, mapping_id=None):
        super().__init__(parent)
        self.mapping_id = mapping_id
        self.suppliers = get_suppliers()
        self.items = get_items()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("新增供應商-產品關聯" if not self.mapping_id else "編輯關聯")
        layout = QFormLayout(self)

        # 供應商選擇（啟用編輯和搜尋）
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        for supplier in self.suppliers:
            text = f"{supplier['SupplierName']} (ID:{supplier['SupplierID']})"
            self.supplier_combo.addItem(text, supplier['SupplierID'])
        supplier_completer = QCompleter(
            [f"{supplier['SupplierName']} (ID:{supplier['SupplierID']})" for supplier in self.suppliers]
        )
        supplier_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.supplier_combo.setCompleter(supplier_completer)
        layout.addRow("供應商*：", self.supplier_combo)

        # 產品選擇（啟用編輯和搜尋）
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        for item in self.items:
            text = f"{item['ItemName']} (ID:{item['ItemID']})"
            self.item_combo.addItem(text, item['ItemID'])
        item_completer = QCompleter(
            [f"{item['ItemName']} (ID:{item['ItemID']})" for item in self.items]
        )
        item_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.item_combo.setCompleter(item_completer)
        layout.addRow("產品*：", self.item_combo)

        # MOQ 輸入（整數）
        self.moq_input = QSpinBox()
        self.moq_input.setMinimum(0)
        self.moq_input.setMaximum(1000000)
        self.moq_input.setSpecialValueText("")
        layout.addRow("MOQ：", self.moq_input)

        # 價格輸入（浮點數）
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(1000000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSpecialValueText("")
        layout.addRow("價格：", self.price_input)

        # 交期輸入（整數天數）
        self.lead_time_input = QSpinBox()
        self.lead_time_input.setMinimum(0)
        self.lead_time_input.setMaximum(3650)
        self.lead_time_input.setSpecialValueText("")
        layout.addRow("交期：", self.lead_time_input)

        # 安全水位
        self.safety_stock_input = QDoubleSpinBox()
        self.safety_stock_input.setMinimum(0.0)
        self.safety_stock_input.setMaximum(1000000.0)
        self.safety_stock_input.setDecimals(2)
        layout.addRow("安全水位*：", self.safety_stock_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def load_data(self):
        if self.mapping_id:
            mapping = get_supplier_item_mapping_by_id(self.mapping_id)
            if mapping:
                # 設置供應商
                supplier_index = self.supplier_combo.findData(mapping['SupplierID'])
                if supplier_index >= 0:
                    self.supplier_combo.setCurrentIndex(supplier_index)
                
                # 設置產品
                item_index = self.item_combo.findData(mapping['ItemID'])
                if item_index >= 0:
                    self.item_combo.setCurrentIndex(item_index)
                
                # 設置其他字段
                self.moq_input.setValue(mapping['MOQ'] or 0)
                self.price_input.setValue(float(mapping['Price'] or 0))
                self.lead_time_input.setValue(mapping['LeadTime'] or 0)
                self.safety_stock_input.setValue(mapping.get('SafetyStockLevel', 0.0))  # 載入安全水位

    def validate_and_submit(self):
        if self.supplier_combo.currentData() is None:
            QMessageBox.warning(self, "錯誤", "必須選擇供應商")
            return
        if self.item_combo.currentData() is None:
            QMessageBox.warning(self, "錯誤", "必須選擇產品")
            return

        self.save_data()
        self.accept()

    def save_data(self):
        # 如果數值為 0（且顯示為空），則視為未輸入（即 None）
        moq = self.moq_input.value() if self.moq_input.value() != 0 else None
        price = self.price_input.value() if self.price_input.value() != 0.0 else None
        lead_time = self.lead_time_input.value() if self.lead_time_input.value() != 0 else None
        safety_stock_level = self.safety_stock_input.value()  # 安全水位不設為 None，即使為 0 也保留

        data = {
            "supplier_id": self.supplier_combo.currentData(),
            "item_id": self.item_combo.currentData(),
            "moq": moq,
            "price": price,
            "lead_time": lead_time,
            "safety_stock_level": safety_stock_level  # 新增安全水位
        }

        if self.mapping_id:
            update_supplier_item_mapping(self.mapping_id, **data)
        else:
            try:
                add_supplier_item_mapping(**data)
            except ValueError as e:
                QMessageBox.warning(self, "錯誤", str(e))
                return