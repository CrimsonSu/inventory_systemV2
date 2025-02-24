from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QAbstractItemView, QHeaderView, QMessageBox
from models.stockmovement_crud import add_stock_movement, get_stock_movements, update_stock_movement, delete_stock_movement
from models.itemmaster_crud import get_items
from models.supplier_crud import get_suppliers
from ui.dialogs.stockmovement_dialog import StockMovementDialog

class StockMovementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 工具列
        tool_layout = QHBoxLayout()
        self.btn_add = QPushButton("新增移動", self)
        self.btn_add.clicked.connect(self.add_movement)
        tool_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("編輯移動", self)
        self.btn_edit.clicked.connect(self.edit_movement)
        tool_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("刪除移動", self)
        self.btn_delete.clicked.connect(self.delete_movement)
        tool_layout.addWidget(self.btn_delete)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜尋物品名稱...")
        self.search_input.textChanged.connect(self.search_movement)
        tool_layout.addWidget(self.search_input)

        main_layout.addLayout(tool_layout)

        # 表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["移動ID", "物品名稱", "供應商", "類型", "數量", "日期", "批次號"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        main_layout.addWidget(self.table)

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        movements = get_stock_movements()
        items = {item["ItemID"]: item["ItemName"] for item in get_items()}
        suppliers = {sup["SupplierID"]: sup["SupplierName"] for sup in get_suppliers()}

        if search_text:
            search_text = search_text.lower()
            movements = [m for m in movements if search_text in items.get(m["ItemID"], "").lower()]

        for row, movement in enumerate(movements):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(movement["MovementID"])))
            item_name = items.get(movement["ItemID"], "未知物品")
            supplier_name = suppliers.get(movement.get("SupplierID"), "未知供應商")
            self.table.setItem(row, 1, QTableWidgetItem(item_name))
            self.table.setItem(row, 2, QTableWidgetItem(supplier_name))
            self.table.setItem(row, 3, QTableWidgetItem(movement["MovementType"]))
            self.table.setItem(row, 4, QTableWidgetItem(f"{movement['Quantity']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(movement["MovementDate"]))
            self.table.setItem(row, 6, QTableWidgetItem(movement.get("BatchNo", "")))

    def search_movement(self):
        self.load_data(self.search_input.text().strip())

    def add_movement(self):
        dialog = StockMovementDialog(self)
        if dialog.exec_():
            movement_data = dialog.get_movement_data()
            add_stock_movement(
                item_id=movement_data["item_id"],
                supplier_id=movement_data["supplier_id"],
                movement_type=movement_data["movement_type"],
                quantity=movement_data["quantity"],
                movement_date=movement_data["movement_date"],
                batch_no=movement_data["batch_no"]
            )
            self.load_data()

    def edit_movement(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "請先選擇要編輯的移動記錄")
            return
        movement_id = int(self.table.item(selected_row, 0).text())
        movement = next((m for m in get_stock_movements() if m["MovementID"] == movement_id), None)
        if not movement:
            QMessageBox.warning(self, "錯誤", "找不到該移動記錄")
            return
        dialog = StockMovementDialog(self, movement)
        if dialog.exec_():
            updated_data = dialog.get_movement_data()
            update_stock_movement(movement_id, **updated_data)
            self.load_data()

    def delete_movement(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的移動記錄")
            return
        movement_id = int(self.table.item(selected_row, 0).text())
        confirm = QMessageBox.question(self, "確認刪除", "確定要刪除此移動記錄嗎？", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            delete_stock_movement(movement_id)
            self.load_data()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = StockMovementPage()
    window.setWindowTitle("庫存移動管理")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())