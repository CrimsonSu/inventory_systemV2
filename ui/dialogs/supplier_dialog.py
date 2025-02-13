from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, 
                            QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt

class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_id=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        self.setWindowTitle("新增供應商" if not self.supplier_id else "編輯供應商")
        layout = QFormLayout(self)
        
        self.supplier_name = QLineEdit(self)
        self.tax_id = QLineEdit(self)
        self.contact_person = QLineEdit(self)
        self.phone = QLineEdit(self)
        self.address = QLineEdit(self)
        self.email = QLineEdit(self)
        self.website = QLineEdit(self)

        layout.addRow("供應商名稱*：", self.supplier_name)
        layout.addRow("統一編號：", self.tax_id)
        layout.addRow("聯絡人：", self.contact_person)
        layout.addRow("電話：", self.phone)
        layout.addRow("地址：", self.address)
        layout.addRow("Email：", self.email)
        layout.addRow("網站：", self.website)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def load_data(self):
        if self.supplier_id:
            from models.supplier_crud import get_supplier_by_id
            supplier = get_supplier_by_id(self.supplier_id)
            if supplier:
                self.supplier_name.setText(supplier.get("SupplierName", ""))
                self.tax_id.setText(supplier.get("TaxID", ""))
                self.contact_person.setText(supplier.get("ContactPerson", ""))
                self.phone.setText(supplier.get("Phone", ""))
                self.address.setText(supplier.get("Address", ""))
                self.email.setText(supplier.get("Email", ""))
                self.website.setText(supplier.get("Website", ""))
    
    def validate_and_submit(self):
        if not self.supplier_name.text().strip():
            QMessageBox.warning(self, "錯誤", "供應商名稱不能為空")
            return
            
        self.save_data()
        self.accept()
    
    def save_data(self):
        data = {
            "supplier_name": self.supplier_name.text().strip(),
            "tax_id": self.tax_id.text().strip(),
            "contact_person": self.contact_person.text().strip(),
            "phone": self.phone.text().strip(),
            "address": self.address.text().strip(),
            "email": self.email.text().strip(),
            "website": self.website.text().strip()
        }
        
        if self.supplier_id:
            from models.supplier_crud import update_supplier
            update_supplier(self.supplier_id, **data)
        else:
            from models.supplier_crud import add_supplier
            add_supplier(**data)