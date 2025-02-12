from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, 
                            QDialogButtonBox, QMessageBox)
# 新增 Qt 核心模块导入
from PyQt5.QtCore import Qt

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_id=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        self.setWindowTitle("新增客戶" if not self.customer_id else "編輯客戶")
        layout = QFormLayout(self)
        
        self.customer_name = QLineEdit(self)
        self.tax_id = QLineEdit(self)
        self.contact_person = QLineEdit(self)
        self.phone = QLineEdit(self)
        self.address = QLineEdit(self)
        self.address2 = QLineEdit(self)
        self.email = QLineEdit(self)

        layout.addRow("客户名称*：", self.customer_name)
        layout.addRow("統一編號：", self.tax_id)
        layout.addRow("联系人：", self.contact_person)
        layout.addRow("电话：", self.phone)
        layout.addRow("地址：", self.address)
        layout.addRow("送貨地址：", self.address2)
        layout.addRow("Email：", self.email)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        # 样式建议：可设置字段星号颜色为红色
        # 布局建议：可设置字段最小宽度为300px
    
    def load_data(self):
        if self.customer_id:
            from models.customer_crud import get_customer_by_id
            customer = get_customer_by_id(self.customer_id)

            if customer:
                self.customer_name.setText(customer.get("CustomerName", ""))  # 修改這行
                self.contact_person.setText(customer.get("ContactPerson", ""))  # 修改這行
                self.phone.setText(customer.get("Phone", ""))  # 修改這行
                self.address.setText(customer.get("Address", ""))  # 修改這行
                self.address2.setText(customer.get("Address2", ""))  # 修改這行
                self.tax_id.setText(customer.get("TaxID", ""))  # 修改這行
                self.email.setText(customer.get("Email", ""))  # 修改這行
    
    def validate_and_submit(self):
        # 必填字段验证
        if not self.customer_name.text().strip():
            QMessageBox.warning(self, "错误", "客户名称不能为空")
            return
            
        self.save_data()
        self.accept()
    
    def save_data(self):
        data = {
            "customer_name": self.customer_name.text().strip(),
            "contact_person": self.contact_person.text().strip(),
            "phone": self.phone.text().strip(),
            "address": self.address.text().strip(),
            "address2": self.address2.text().strip(),
            "tax_id": self.tax_id.text().strip(),
            "email": self.email.text().strip()
        }
        
        if self.customer_id:
            from models.customer_crud import update_customer
            update_customer(self.customer_id, **data)
        else:
            from models.customer_crud import add_customer
            add_customer(**data)