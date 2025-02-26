from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QDoubleSpinBox, QPushButton, QLabel, QMessageBox, QHeaderView, QWidget
from PyQt5.QtGui import QColor
from models.salesorderheader_crud import get_sales_order_by_id
from models.salesorderdetail_crud import get_sales_order_details
from models.bomheader_crud import get_bom_headers
from models.bomdetail_crud import get_bom_details
from models.stock_crud import get_stock_by_item
from models.itemmaster_crud import get_item_by_id

class SalesOrderDetailDialog(QDialog):
    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle(f"訂單詳情 - ID: {order_id}")
        self.resize(800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["項目", "需求量", "庫存量", "狀態"])
        self.tree.header().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("關閉")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def load_data(self):
        order = get_sales_order_by_id(self.order_id)
        if not order:
            QMessageBox.warning(self, "錯誤", "訂單不存在")
            self.close()
            return
        self.info_label.setText(f"訂單 ID: {order['OrderID']} | 客戶: {order['CustomerName']} | 日期: {order['OrderDate']}")

        details = get_sales_order_details(self.order_id)
        semi_demand = {}

        for detail in details:
            finished_item = get_item_by_id(detail["ItemID"])
            finished_node = QTreeWidgetItem(self.tree, [
                f"{finished_item['ItemName']} ({detail['ItemID']})",
                f"{detail['Quantity']} {finished_item['Unit']}",
                "", ""
            ])
            
            bom = next((b for b in get_bom_headers() if b["ProductID"] == detail["ItemID"]), None)
            if not bom:
                finished_node.setText(3, "無 BOM 定義")
                continue

            bom_details = get_bom_details(bom["BOMID"])
            for bom_detail in bom_details:
                semi_item = get_item_by_id(bom_detail["ComponentItemID"])
                if semi_item["ItemType"] != "半成品":
                    continue
                semi_qty = bom_detail["Quantity"] * detail["Quantity"]
                semi_demand[semi_item["ItemID"]] = semi_demand.get(semi_item["ItemID"], 0) + semi_qty

        for semi_id, total_demand in semi_demand.items():
            semi_item = get_item_by_id(semi_id)
            stock = get_stock_by_item(semi_id)
            stock_qty = sum(s["Quantity"] for s in stock) if stock else 0
            shortage = total_demand - stock_qty

            semi_node = QTreeWidgetItem(self.tree, [
                f"{semi_item['ItemName']} ({semi_id})",
                f"{total_demand:.2f} {semi_item['Unit']}",
                f"{stock_qty:.2f} {semi_item['Unit']}",
                "足夠" if shortage <= 0 else f"缺 {shortage:.2f}"
            ])
            if shortage > 0:
                semi_node.setForeground(3, QColor("red"))

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dialog = SalesOrderDetailDialog(1)
    dialog.show()
    sys.exit(app.exec_())