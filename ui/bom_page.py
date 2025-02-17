import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHeaderView, QMessageBox, QMenu, QAbstractItemView,
    QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QTreeWidget, QTreeWidgetItem,
    QLabel, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QKeySequence

# 後端 CRUD 模組匯入（假設這些模組已實作）
from models.bomheader_crud import (
    get_bom_headers, add_bom_header, update_bom_header,
    delete_bom_header, get_bom_header_by_id
)
from models.bomdetail_crud import (
    get_bom_details, add_bom_detail, update_bom_detail, delete_bom_detail
)
from models.itemmaster_crud import get_items, get_item_by_id
from models.supplier_crud import get_suppliers
# 新增：假設此函式可以根據供應商與品項取得最新價格（單位 kg）
from models.supplieritemmap_crud import get_latest_supplier_price
from models.costhistory_crud import add_cost_history
# ===================== BOM 主檔管理頁面 =====================
class BOMPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 頂部工具列
        tool_layout = QHBoxLayout()
        self.btn_add = QPushButton("新增 BOM", self)
        self.btn_add.clicked.connect(self.add_bom)
        tool_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("編輯 BOM", self)
        self.btn_edit.clicked.connect(self.edit_bom)
        tool_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("刪除 BOM", self)
        self.btn_delete.clicked.connect(self.delete_bom)
        tool_layout.addWidget(self.btn_delete)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入產品名稱或版本搜索...")
        self.search_input.textChanged.connect(self.search_bom)
        tool_layout.addWidget(self.search_input)

        main_layout.addLayout(tool_layout)

        # 修改 1：更新表格欄位為「BOM ID」、「產品名稱」、「重量」、「價格」、「備註」
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["BOM ID", "產品名稱", "重量", "價格", "備註"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellClicked.connect(self.select_row)

        main_layout.addWidget(self.table)

    def select_row(self, row, column):
        self.table.selectRow(row)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            selected = self.table.selectedItems()
            if selected:
                QApplication.clipboard().setText(selected[0].text())

    def load_data(self, search_text=None):
        self.table.setRowCount(0)
        bom_headers = get_bom_headers()  # 取得 BOMHeader 列表，包含 BOMID、ProductID、Version、EffectiveDate、Remarks、ProductWeight 等欄位
        if search_text:
            search_text = search_text.lower()
            filtered_boms = []
            for bom in bom_headers:
                # 透過 ProductID 取得產品名稱
                product = get_item_by_id(bom["ProductID"])
                product_name = product["ItemName"] if product else ""
                # 如果搜尋文字存在於產品名稱、版本或備註中，就加入過濾結果中
                if (search_text in product_name.lower() or 
                    search_text in bom.get("Version", "").lower() or 
                    search_text in bom.get("Remarks", "").lower()):
                    filtered_boms.append(bom)
            bom_headers = filtered_boms

        for row, bom in enumerate(bom_headers):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(bom["BOMID"])))
            product = get_item_by_id(bom["ProductID"])
            product_name = product["ItemName"] if product else ""
            self.table.setItem(row, 1, QTableWidgetItem(product_name))
            product_weight = bom.get("ProductWeight") or 0.0
            self.table.setItem(row, 2, QTableWidgetItem(f"{product_weight:.2f} g"))

            # 計算總價格
            details = get_bom_details(bom_id=bom["BOMID"])
            total_price = 0.0
            for detail in details:
                percentage = detail["Quantity"]
                unit = detail.get("Unit", "%")
                if unit == "%":
                    actual_qty = product_weight * (percentage / 100.0)
                else:
                    actual_qty = percentage
                price = detail.get("Price", 0)
                total_price += actual_qty * price
            self.table.setItem(row, 3, QTableWidgetItem(f"{total_price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(bom.get("Remarks", "")))


    def search_bom(self):
        search_text = self.search_input.text().strip()
        self.load_data(search_text)

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            return None
        item = self.table.item(selected_row, 0)
        return int(item.text()) if item else None

    def add_bom(self):
        dialog = BOMDialog(self)
        if dialog.exec_():
            self.load_data()

    def edit_bom(self):
        bom_id = self.get_selected_id()
        if not bom_id:
            QMessageBox.warning(self, "警告", "請先選擇要編輯的 BOM")
            return
        dialog = BOMDialog(self, bom_id)
        if dialog.exec_():
            self.load_data()

    def delete_bom(self):
        bom_id = self.get_selected_id()
        if not bom_id:
            QMessageBox.warning(self, "警告", "請先選擇要刪除的 BOM")
            return
        confirm = QMessageBox.question(
            self, "確認刪除", "確定要刪除此 BOM 嗎？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            delete_bom_header(bom_id)
            QMessageBox.information(self, "成功", "BOM 已刪除")
            self.load_data()

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("編輯")
        delete_action = menu.addAction("刪除")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == edit_action:
            self.edit_bom()
        elif action == delete_action:
            self.delete_bom()


# ===================== BOM 編輯對話框 =====================
class BOMDialog(QDialog):
    def __init__(self, parent=None, bom_id=None):
        super().__init__(parent)
        self.bom_id = bom_id
        # BOM header 資料與明細列表
        self.bom_data = {}
        self.detail_list = []  # 每筆為字典，參考 BOMDetail 欄位
        self.setup_ui()
        if self.bom_id:
            self.load_bom_data()

    def setup_ui(self):
        self.setWindowTitle("新增 BOM" if not self.bom_id else "編輯 BOM")
        self.resize(900 , 650)
        main_layout = QVBoxLayout(self)

        # BOM header 基本資訊區
        form_layout = QFormLayout()
        
        # 產品選擇 (修改 3：預設加入空白選項)
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.addItem("", None)  # 預設空白
        self.products = get_items()  # 取得所有產品／原料
        for product in self.products:
            text = f"{product['ItemName']} (ID:{product['ItemID']})"
            self.product_combo.addItem(text, product['ItemID'])
        form_layout.addRow("產品*：", self.product_combo)

        # 產品重量 (g) - 新增部分
        self.product_weight_input = QDoubleSpinBox()
        self.product_weight_input.setMinimum(0.0)
        self.product_weight_input.setMaximum(100000.0)
        self.product_weight_input.setDecimals(2)
        self.product_weight_input.setSuffix(" g")
        form_layout.addRow("產品重量 (g)：", self.product_weight_input)

        # 版本輸入
        self.version_input = QLineEdit()
        form_layout.addRow("版本*：", self.version_input)

        # 生效日期 (修改 4：改用 QDateEdit)
        self.effective_date_input = QDateEdit()
        self.effective_date_input.setCalendarPopup(True)
        self.effective_date_input.setDisplayFormat("yyyy-MM-dd")
        self.effective_date_input.setDate(QDate.currentDate())
        form_layout.addRow("生效日期*：", self.effective_date_input)

        # 備註
        self.remarks_input = QLineEdit()
        form_layout.addRow("備註：", self.remarks_input)

        main_layout.addLayout(form_layout)

        # BOM 明細區：以樹狀結構呈現，增加「實際用量 (g)」欄位
        self.detail_tree = QTreeWidget()
        self.detail_tree.setHeaderLabels(["組件", "百分比(%)", "實際用量 (g)", "單位", "損耗率", "供應商", "單價 (每 g)", "小計"])
        main_layout.addWidget(self.detail_tree)

        # 明細操作工具列
        detail_btn_layout = QHBoxLayout()
        self.btn_add_detail = QPushButton("新增明細")
        self.btn_add_detail.clicked.connect(self.add_detail)
        detail_btn_layout.addWidget(self.btn_add_detail)

        self.btn_edit_detail = QPushButton("編輯明細")
        self.btn_edit_detail.clicked.connect(self.edit_detail)
        detail_btn_layout.addWidget(self.btn_edit_detail)

        self.btn_delete_detail = QPushButton("刪除明細")
        self.btn_delete_detail.clicked.connect(self.delete_detail)
        detail_btn_layout.addWidget(self.btn_delete_detail)
        main_layout.addLayout(detail_btn_layout)

                # [新增] 「一鍵自動抓取價格」按鈕
        self.btn_fetch_all_prices = QPushButton("一鍵自動抓取價格")
        self.btn_fetch_all_prices.clicked.connect(self.fetch_all_prices)
        detail_btn_layout.addWidget(self.btn_fetch_all_prices)
        
        main_layout.addLayout(detail_btn_layout)

        # 總成本顯示
        self.total_label = QLabel("總成本：0.00")
        main_layout.addWidget(self.total_label)

        # 對話框按鈕
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("確定")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def load_bom_data(self):
        # 從後端取得 BOM header 與明細資料
        self.bom_data = get_bom_header_by_id(self.bom_id)
        if not self.bom_data:
            QMessageBox.warning(self, "錯誤", "找不到該 BOM 資料")
            return
        # 設定 header 資料
        product_index = self.product_combo.findData(self.bom_data["ProductID"])
        if product_index >= 0:
            self.product_combo.setCurrentIndex(product_index)
        # 如果 ProductWeight 為 None，就預設為 0.0
        product_weight = self.bom_data.get("ProductWeight") or 0.0
        self.product_weight_input.setValue(product_weight)
        self.version_input.setText(self.bom_data["Version"])
        try:
            date = QDate.fromString(self.bom_data["EffectiveDate"], "yyyy-MM-dd")
            if date.isValid():
                self.effective_date_input.setDate(date)
        except Exception as e:
            pass
        self.remarks_input.setText(self.bom_data.get("Remarks", ""))
        # 取得 BOM 明細
        self.detail_list = get_bom_details(bom_id=self.bom_id)
        self.refresh_detail_tree()
        self.calculate_total_cost()

    def refresh_detail_tree(self):
        self.detail_tree.clear()
        product_weight = self.product_weight_input.value()  # 產品重量 (g)
        for detail in self.detail_list:
            item = QTreeWidgetItem()
            # 組件名稱
            comp = get_item_by_id(detail["ComponentItemID"])
            comp_name = comp["ItemName"] if comp else ""
            item.setText(0, comp_name)
            # 百分比（用量以百分比表示）
            percentage = detail["Quantity"]
            item.setText(1, f"{percentage:.2f}")
            # 實際用量：若單位為 "%"，則實際用量 = 產品重量 * (百分比 / 100)
            if detail.get("Unit", "%") == "%":
                actual_qty = product_weight * (percentage / 100.0)
            else:
                actual_qty = percentage
            item.setText(2, f"{actual_qty:.2f}")
            # 單位顯示
            item.setText(3, detail.get("Unit", "%"))
            item.setText(4, f"{detail.get('ScrapRate', 0):.2f}")
            # 供應商欄位：若有則顯示 ID
            supplier = f"ID:{detail['SupplierID']}" if detail.get("SupplierID") else ""
            item.setText(5, supplier)
            # 單價：這裡已換算為每 g 的價格（若原始記錄為每 kg，則需除以 1000）
            price = detail.get("Price", 0)
            item.setText(6, f"{price:.4f}")
            # 小計 = 實際用量 * 單價
            subtotal = actual_qty * price
            item.setText(7, f"{subtotal:.2f}")
            self.detail_tree.addTopLevelItem(item)

    def calculate_total_cost(self):
        total = 0.0
        product_weight = self.product_weight_input.value()
        for detail in self.detail_list:
            percentage = detail["Quantity"]
            if detail.get("Unit", "%") == "%":
                actual_qty = product_weight * (percentage / 100.0)
            else:
                actual_qty = percentage
            total += actual_qty * detail.get("Price", 0)
        self.total_label.setText(f"總成本：{total:.2f}")

    def add_detail(self):
        dialog = BOMDetailDialog(self)
        if dialog.exec_():
            new_detail = dialog.get_detail_data()
            # 修改 2：檢查是否重複，避免同一 BOM 中出現重複組件
            for detail in self.detail_list:
                if detail["ComponentItemID"] == new_detail["ComponentItemID"]:
                    QMessageBox.warning(self, "錯誤", "該組件已存在於 BOM 明細中")
                    return
            self.detail_list.append(new_detail)
            self.refresh_detail_tree()
            self.calculate_total_cost()

    def edit_detail(self):
        selected = self.detail_tree.currentIndex()
        row = selected.row()
        if row < 0 or row >= len(self.detail_list):
            QMessageBox.warning(self, "警告", "請先選擇要編輯的明細")
            return
        dialog = BOMDetailDialog(self, self.detail_list[row])
        if dialog.exec_():
            edited_detail = dialog.get_detail_data()
            for i, detail in enumerate(self.detail_list):
                if i != row and detail["ComponentItemID"] == edited_detail["ComponentItemID"]:
                    QMessageBox.warning(self, "錯誤", "該組件已存在於 BOM 明細中")
                    return
            self.detail_list[row] = edited_detail
            self.refresh_detail_tree()
            self.calculate_total_cost()

    def delete_detail(self):
        selected = self.detail_tree.currentIndex()
        row = selected.row()
        if row < 0 or row >= len(self.detail_list):
            QMessageBox.warning(self, "警告", "請先選擇要刪除的明細")
            return
        confirm = QMessageBox.question(
            self, "確認刪除", "確定要刪除此明細嗎？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.detail_list[row]
            self.refresh_detail_tree()
            self.calculate_total_cost()

     # [新增] 一鍵自動抓取價格
    def fetch_all_prices(self):
        """
        迭代目前 self.detail_list 的所有明細，依照 SupplierID + ComponentItemID
        取得最新價格，更新 Price，並將更新後的價格寫入 CostHistory。
        """
        # 注意：get_latest_supplier_price 回傳的是「每公斤」的價格，需要除以 1000 變成 每克 價格。
        updated_count = 0
        for detail in self.detail_list:
            supplier_id = detail.get("SupplierID")
            component_id = detail.get("ComponentItemID")

            # 若明細沒有指定 supplier_id，則略過
            if not supplier_id:
                continue

            latest_price_per_kg = get_latest_supplier_price(supplier_id, component_id)
            if latest_price_per_kg is not None:
                # 轉換成 每 g
                price_per_g = latest_price_per_kg / 1000.0
                detail["Price"] = price_per_g

                # 寫入 CostHistory
                # 取得組件名稱
                comp_item = get_item_by_id(component_id)
                product_name = comp_item["ItemName"] if comp_item else f"ItemID:{component_id}"
                add_cost_history(product_name, price_per_g)

                updated_count += 1

        # 重新整理畫面
        self.refresh_detail_tree()
        self.calculate_total_cost()

        QMessageBox.information(self, "完成", f"已自動抓取並更新 {updated_count} 筆明細的價格。")


    def accept(self):
        # 檢查必要欄位
        if self.product_combo.currentData() is None or not self.version_input.text():
            QMessageBox.warning(self, "錯誤", "請填寫所有必填欄位")
            return
        
        product_id = self.product_combo.currentData()
        product_weight = self.product_weight_input.value()  # 取得產品重量 (g)
        version = self.version_input.text().strip()
        effective_date = self.effective_date_input.date().toString("yyyy-MM-dd")
        remarks = self.remarks_input.text().strip()

        if self.bom_id:
            # 更新 BOM header
            update_bom_header(self.bom_id,
                              new_product_id=product_id,
                              new_version=version,
                              new_effective_date=effective_date,
                              new_product_weight=product_weight,
                              new_remarks=remarks)
            # 【修改重點】：先刪除現有 BOM 明細，避免重複新增
            existing_details = get_bom_details(bom_id=self.bom_id)
            for d in existing_details:
                delete_bom_detail(d["BOMDetailID"])
            
            # 【修改重點】：過濾 self.detail_list，避免重複同一組件的明細
            unique_details = {}
            for detail in self.detail_list:
                comp_id = detail["ComponentItemID"]
                if comp_id not in unique_details:
                    unique_details[comp_id] = detail
            for detail in unique_details.values():
                add_bom_detail(self.bom_id,
                               detail["ComponentItemID"],
                               detail["Quantity"],
                               detail.get("Unit", "%"),
                               detail.get("ScrapRate"),
                               detail.get("SupplierID"),    # 新增
                               detail.get("Price"))         # 新增
        else:
            # 新增模式：類似處理，先過濾重複明細
            add_bom_header(product_id, version, effective_date, product_weight, remarks=remarks)
            new_bom = get_bom_headers()[-1]
            new_bom_id = new_bom["BOMID"]
            unique_details = {}
            for detail in self.detail_list:
                comp_id = detail["ComponentItemID"]
                if comp_id not in unique_details:
                    unique_details[comp_id] = detail
            for detail in unique_details.values():
                add_bom_detail(new_bom_id,
                               detail["ComponentItemID"],
                               detail["Quantity"],
                               detail.get("Unit", "%"),
                               detail.get("ScrapRate"),
                               detail.get("SupplierID"),    # 新增
                               detail.get("Price"))         # 新增
        super().accept()



# ===================== BOM 明細編輯對話框 =====================
class BOMDetailDialog(QDialog):
    def __init__(self, parent=None, detail=None):
        super().__init__(parent)
        self.detail = detail  # 若 detail 非 None，表示編輯模式
        self.setup_ui()
        if self.detail:
            self.load_detail()

    def setup_ui(self):
        self.setWindowTitle("新增明細" if not self.detail else "編輯明細")
        form_layout = QFormLayout(self)

        # 組件選擇（從 itemmaster 取得）
        self.component_combo = QComboBox()
        self.component_combo.setEditable(True)
        self.components = get_items()
        for comp in self.components:
            text = f"{comp['ItemName']} (ID:{comp['ItemID']})"
            self.component_combo.addItem(text, comp['ItemID'])
        form_layout.addRow("組件*：", self.component_combo)

        # 用量輸入 (視為百分比)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMinimum(0.0)
        self.quantity_input.setMaximum(100.0)
        self.quantity_input.setDecimals(2)
        form_layout.addRow("百分比 (%)：", self.quantity_input)

        # 單位輸入，預設為 "%" (修改 1)
        self.unit_input = QLineEdit()
        self.unit_input.setText("%")
        form_layout.addRow("單位：", self.unit_input)

        # 損耗率輸入（0.0 ~ 1.0）
        self.scrap_rate_input = QDoubleSpinBox()
        self.scrap_rate_input.setMinimum(0.0)
        self.scrap_rate_input.setMaximum(1.0)
        self.scrap_rate_input.setDecimals(2)
        form_layout.addRow("損耗率：", self.scrap_rate_input)

        # 供應商選擇
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.suppliers = get_suppliers()
        for sup in self.suppliers:
            text = f"{sup['SupplierName']} (ID:{sup['SupplierID']})"
            self.supplier_combo.addItem(text, sup['SupplierID'])
        form_layout.addRow("供應商*：", self.supplier_combo)

        # 單價輸入 (記錄的是每 g 的價格；若從 supplier 抓取資料，原始價格為每 kg，需要除以1000)
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(1000000.0)
        self.price_input.setDecimals(2)
        form_layout.addRow("單價 (每 g)*：", self.price_input)

        # 新增按鈕：自動抓取價格 (修改 2：示範自動抓取 supplieritemmap 資料，並換算單位)
        self.fetch_price_btn = QPushButton("自動抓取價格")
        self.fetch_price_btn.clicked.connect(self.fetch_price)
        form_layout.addRow(" ", self.fetch_price_btn)

        # 對話框按鈕
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("確定")
        self.btn_ok.clicked.connect(self.validate_and_submit)
        btn_layout.addWidget(self.btn_ok)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        form_layout.addRow(btn_layout)

    def load_detail(self):
        comp_index = self.component_combo.findData(self.detail["ComponentItemID"])
        if comp_index >= 0:
            self.component_combo.setCurrentIndex(comp_index)
        self.quantity_input.setValue(self.detail["Quantity"])
        self.unit_input.setText(self.detail.get("Unit", "%"))
        self.scrap_rate_input.setValue(self.detail.get("ScrapRate", 0))
        sup_index = self.supplier_combo.findData(self.detail.get("SupplierID"))
        if sup_index >= 0:
            self.supplier_combo.setCurrentIndex(sup_index)
        if self.detail.get("Price") is not None:
            self.price_input.setValue(self.detail["Price"])

    def validate_and_submit(self):
        if self.component_combo.currentData() is None or self.supplier_combo.currentData() is None:
            QMessageBox.warning(self, "錯誤", "請選擇組件與供應商")
            return
        if self.quantity_input.value() <= 0 or self.price_input.value() <= 0:
            QMessageBox.warning(self, "錯誤", "百分比與單價必須大於 0")
            return
        self.accept()

    def get_detail_data(self):
        return {
            "ComponentItemID": self.component_combo.currentData(),
            "Quantity": self.quantity_input.value(),
            "Unit": self.unit_input.text().strip(),
            "ScrapRate": self.scrap_rate_input.value(),
            "SupplierID": self.supplier_combo.currentData(),
            "Price": self.price_input.value()
        }

    # 新增函式：自動抓取供應商最新價格，並換算成每 g 的價格
    def fetch_price(self):
        supplier_id = self.supplier_combo.currentData()
        component_id = self.component_combo.currentData()
        if supplier_id is None or component_id is None:
            QMessageBox.warning(self, "錯誤", "請先選擇供應商和組件")
            return
        # 呼叫 supplieritemmap 模組取得最新價格 (單位為 kg)
        supplier_price = get_latest_supplier_price(supplier_id, component_id)
        if supplier_price is None:
            QMessageBox.information(self, "資訊", "找不到對應的供應商價格資料")
            return
        # 換算成每 g 的價格
        price_per_g = supplier_price / 1000.0
        self.price_input.setValue(price_per_g)
        QMessageBox.information(self, "資訊", f"自動抓取價格成功：{price_per_g:.4f} (每 g)")

# ===================== 主程式進入點 =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BOMPage()
    window.setWindowTitle("BOM 管理頁面")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
