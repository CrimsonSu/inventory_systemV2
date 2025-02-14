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
        self.setWindowTitle("新增供应商-产品关联" if not self.mapping_id else "编辑关联")
        layout = QFormLayout(self)

        # 供应商选择（启用编辑和搜索）
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
        layout.addRow("供应商*：", self.supplier_combo)

        # 产品选择（启用编辑和搜索）
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
        layout.addRow("产品*：", self.item_combo)

        # 数值输入：使用 QSpinBox 和 QDoubleSpinBox 避免非法文本输入

        # MOQ 输入（整数）
        self.moq_input = QSpinBox()
        self.moq_input.setMinimum(0)
        self.moq_input.setMaximum(1000000)  # 根据实际需求调整最大值
        self.moq_input.setSpecialValueText("")  # 当值为 0 时显示为空
        layout.addRow("MOQ：", self.moq_input)

        # 价格输入（浮点数）
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(1000000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSpecialValueText("")
        layout.addRow("价格：", self.price_input)

        # 交期输入（整数天数）
        self.lead_time_input = QSpinBox()
        self.lead_time_input.setMinimum(0)
        self.lead_time_input.setMaximum(3650)  # 可根据实际情况调整（例如最多10年）
        self.lead_time_input.setSpecialValueText("")
        layout.addRow("交期：", self.lead_time_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


    def load_data(self):  # ✅ 正确缩进
        if self.mapping_id:
            mapping = get_supplier_item_mapping_by_id(self.mapping_id)
            if mapping:
                # 设置供应商
                supplier_index = self.supplier_combo.findData(mapping['SupplierID'])
                if supplier_index >= 0:
                    self.supplier_combo.setCurrentIndex(supplier_index)
                
                # 设置产品
                item_index = self.item_combo.findData(mapping['ItemID'])
                if item_index >= 0:
                    self.item_combo.setCurrentIndex(item_index)
                
                # 设置其他字段
                if mapping.get('MOQ') is not None:
                    self.moq_input.setValue(mapping['MOQ'])
                else:
                    self.moq_input.setValue(0)
                if mapping.get('Price') is not None:
                    self.price_input.setValue(float(mapping['Price']))
                else:
                    self.price_input.setValue(0.0)
                if mapping.get('LeadTime') is not None:
                    self.lead_time_input.setValue(mapping['LeadTime'])
                else:
                    self.lead_time_input.setValue(0)

    def validate_and_submit(self):  # ✅ 正确缩进
        # 必填字段验证
        if self.supplier_combo.currentData() is None:
            QMessageBox.warning(self, "错误", "必须选择供应商")
            return
        if self.item_combo.currentData() is None:
            QMessageBox.warning(self, "错误", "必须选择产品")
            return

        self.save_data()
        self.accept()

    def save_data(self):  # ✅ 正确缩进
        # 如果数值为 0（且显示为空），则视为未输入（即 None）
        moq = self.moq_input.value() if self.moq_input.value() != 0 else None
        price = self.price_input.value() if self.price_input.value() != 0.0 else None
        lead_time = self.lead_time_input.value() if self.lead_time_input.value() != 0 else None

        data = {
            "supplier_id": self.supplier_combo.currentData(),
            "item_id": self.item_combo.currentData(),
            "moq": moq,
            "price": price,
            "lead_time": lead_time
        }

        if self.mapping_id:
            update_supplier_item_mapping(self.mapping_id, **data)
        else:
            try:
                add_supplier_item_mapping(**data)
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))
                return