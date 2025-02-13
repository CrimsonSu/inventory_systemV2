from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                            QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt

class ItemDialog(QDialog):
    def __init__(self, parent=None, item_id=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("新增物料" if not self.item_id else "編輯物料")
        layout = QFormLayout(self)
        
        # 字段定义
        self.item_name = QLineEdit(self)
        self.item_type = QComboBox(self)
        self.item_type.addItems(["原料", "成品", "半成品", "包材", "耗材", "其他"])
        self.category = QComboBox(self)
        self.category.addItems(["罐頭", "凍乾", "肉泥條","包裝", "其他"])
        self.unit = QComboBox(self)
        self.unit.addItems(["公斤", "公克", "箱", "件"])

        layout.addRow("物料名稱*：", self.item_name)
        layout.addRow("類型*：", self.item_type)
        layout.addRow("類別：", self.category)
        layout.addRow("單位：", self.unit)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def load_data(self):
        if self.item_id:
            from models.itemmaster_crud import get_item_by_id
            item = get_item_by_id(self.item_id)
            if item:
                self.item_name.setText(item.get("ItemName", ""))
                self.item_type.setCurrentText(item.get("ItemType", ""))
                self.category.setCurrentText(item.get("Category", ""))
                self.unit.setCurrentText(item.get("Unit", ""))

    def validate_and_submit(self):
        if not self.item_name.text().strip():
            QMessageBox.warning(self, "錯誤", "物料名稱不能為空")
            return
        self.save_data()
        self.accept()

    def save_data(self):
        data = {
            "new_name": self.item_name.text().strip(),
            "new_type": self.item_type.currentText().strip(),
            "new_category": self.category.currentText().strip(),  # ✅ 修正
            "new_unit": self.unit.currentText().strip()  # ✅ 修正
        }
        
        if self.item_id:
            from models.itemmaster_crud import update_item
            update_item(self.item_id, **data)
        else:
            from models.itemmaster_crud import add_item
            add_item(
                item_name=data["new_name"],
                item_type=data["new_type"],
                category=data["new_category"],
                unit=data["new_unit"]
            )