import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "inventory.db"

###############################################################################
# 1. 資料庫函式：初始化 + 取得 cursor
###############################################################################
def init_db():
    """
    初始化資料庫：如果表格不存在，則自動建立。
    包含：raw_materials, finished_products, production_orders, bom, production_materials, stock_log。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    create_tables_sql = """
    -- 原料表
    CREATE TABLE IF NOT EXISTS raw_materials (
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_name TEXT NOT NULL,
        unit TEXT,
        quantity_in_stock REAL DEFAULT 0,
        safety_stock REAL DEFAULT 0,
        created_at TEXT
    );

    -- 成品表
    CREATE TABLE IF NOT EXISTS finished_products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        package_info TEXT,
        unit TEXT,
        quantity_in_stock REAL DEFAULT 0,
        safety_stock REAL DEFAULT 0,
        created_at TEXT
    );

    -- BOM (Bill of Materials)
    CREATE TABLE IF NOT EXISTS bom (
        bom_id INTEGER PRIMARY KEY AUTOINCREMENT,
        finished_product_id INTEGER NOT NULL,
        raw_material_id INTEGER NOT NULL,
        quantity_needed REAL,
        FOREIGN KEY (finished_product_id) REFERENCES finished_products(product_id),
        FOREIGN KEY (raw_material_id) REFERENCES raw_materials(material_id)
    );

    -- 生產工單
    CREATE TABLE IF NOT EXISTS production_orders (
        production_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        planned_qty REAL,
        actual_qty REAL,
        start_date TEXT,
        end_date TEXT,
        status TEXT,
        remarks TEXT,
        FOREIGN KEY (product_id) REFERENCES finished_products(product_id)
    );

    -- 生產用料
    CREATE TABLE IF NOT EXISTS production_materials (
        pm_id INTEGER PRIMARY KEY AUTOINCREMENT,
        production_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        planned_qty REAL,
        actual_qty REAL,
        FOREIGN KEY (production_id) REFERENCES production_orders(production_id),
        FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
    );

    -- 庫存異動記錄
    CREATE TABLE IF NOT EXISTS stock_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_date TEXT,
        material_id INTEGER,
        product_id INTEGER,
        change_qty REAL,
        old_qty REAL,
        new_qty REAL,
        change_type TEXT,
        reason TEXT,
        FOREIGN KEY (material_id) REFERENCES raw_materials(material_id),
        FOREIGN KEY (product_id) REFERENCES finished_products(product_id)
    );
    """
    cursor.executescript(create_tables_sql)
    conn.commit()
    conn.close()
    messagebox.showinfo("訊息", "資料庫初始化完成（或已存在）")


def get_db_cursor():
    """
    取得資料庫連線與 cursor。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    return conn, cursor


###############################################################################
# 2. 主應用程式：多頁面 (Frame) 架構
###############################################################################
class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("進銷存 + 生產管理 Demo")
        self.geometry("900x700")

        # 先自動初始化資料庫（避免沒有表格時出錯）
        init_db()

        # 建立一個容器，用來放所有 Frame
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        # 將我們想要的頁面都在這裡註冊
        for F in (MainMenuFrame,
                  AddMaterialFrame, ListMaterialFrame,
                  AddProductFrame, ListProductFrame,
                  AdjustMaterialStockFrame, AdjustProductStockFrame,
                  CreateProductionOrderFrame, PlanProductionMaterialsFrame,
                  FinishProductionFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            # 讓所有頁面重疊於同個 grid
            frame.grid(row=0, column=0, sticky="nsew")

        # 一開始顯示主選單頁面
        self.show_frame(MainMenuFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()


###############################################################################
# 3. 各個頁面 Frame 的實作
###############################################################################

# -- (A) 主選單頁面 ------------------------------------------------------------
class MainMenuFrame(tk.Frame):
    """
    主選單：列出主要功能入口。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="主選單", font=("Arial", 20))
        label.pack(pady=20)

        # 資料庫初始化
        btn_init_db = tk.Button(self, text="初始化資料庫", command=init_db)
        btn_init_db.pack(pady=5)

        # 原料
        btn_add_mat = tk.Button(self, text="新增原料", command=lambda: controller.show_frame(AddMaterialFrame))
        btn_add_mat.pack(pady=5)

        btn_list_mat = tk.Button(self, text="查詢原料", command=lambda: controller.show_frame(ListMaterialFrame))
        btn_list_mat.pack(pady=5)

        btn_adj_mat = tk.Button(self, text="調整【原料】庫存", command=lambda: controller.show_frame(AdjustMaterialStockFrame))
        btn_adj_mat.pack(pady=5)

        # 成品
        btn_add_prod = tk.Button(self, text="新增成品", command=lambda: controller.show_frame(AddProductFrame))
        btn_add_prod.pack(pady=5)

        btn_list_prod = tk.Button(self, text="查詢成品", command=lambda: controller.show_frame(ListProductFrame))
        btn_list_prod.pack(pady=5)

        btn_adj_prod = tk.Button(self, text="調整【成品】庫存", command=lambda: controller.show_frame(AdjustProductStockFrame))
        btn_adj_prod.pack(pady=5)

        # 生產管理
        btn_create_po = tk.Button(self, text="建立生產工單", command=lambda: controller.show_frame(CreateProductionOrderFrame))
        btn_create_po.pack(pady=5)

        btn_plan_bom = tk.Button(self, text="BOM套用(理論用料)", command=lambda: controller.show_frame(PlanProductionMaterialsFrame))
        btn_plan_bom.pack(pady=5)

        btn_finish_prod = tk.Button(self, text="完工 (扣原料+加成品)", command=lambda: controller.show_frame(FinishProductionFrame))
        btn_finish_prod.pack(pady=5)

        # 退出程式
        btn_quit = tk.Button(self, text="退出", command=self.quit)
        btn_quit.pack(pady=20)


# -- (B) 新增「原料」 -----------------------------------------------------------
class AddMaterialFrame(tk.Frame):
    """
    新增原料：僅需輸入 (名稱, 單位)。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="新增原料", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="原料名稱:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_name = tk.Entry(form_frame)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="單位 (如 kg, 箱):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_unit = tk.Entry(form_frame)
        self.entry_unit.grid(row=1, column=1, padx=5, pady=5)

        btn_add = tk.Button(self, text="新增", command=self.add_material)
        btn_add.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

    def add_material(self):
        name = self.entry_name.get().strip()
        unit = self.entry_unit.get().strip()
        if not name:
            messagebox.showerror("錯誤", "原料名稱不能空白！")
            return
        if not unit:
            unit = ""

        conn, cursor = get_db_cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO raw_materials (material_name, unit, quantity_in_stock, safety_stock, created_at)
        VALUES (?, ?, 0, 0, ?)
        """
        cursor.execute(sql, (name, unit, created_at))
        conn.commit()
        conn.close()

        messagebox.showinfo("成功", f"已新增原料：{name}")
        self.entry_name.delete(0, tk.END)
        self.entry_unit.delete(0, tk.END)


# -- (C) 查詢「原料」 ----------------------------------------------------------
class ListMaterialFrame(tk.Frame):
    """
    查詢原料，使用 Treeview 類似 Excel 表格。
    顯示名稱加總後的庫存：GROUP BY material_name, unit
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="原料清單 (名稱加總)", font=("Arial", 16))
        label.pack(pady=10)

        # Treeview
        columns = ("material_name", "unit", "quantity_in_stock", "safety_stock")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        self.tree.heading("material_name", text="原料名稱")
        self.tree.heading("unit", text="單位")
        self.tree.heading("quantity_in_stock", text="庫存(加總)")
        self.tree.heading("safety_stock", text="安全庫存")

        self.tree.column("material_name", width=200)
        self.tree.column("unit", width=80)
        self.tree.column("quantity_in_stock", width=100)
        self.tree.column("safety_stock", width=100)
        self.tree.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        btn_refresh = tk.Button(btn_frame, text="刷新", command=self.refresh_data)
        btn_refresh.grid(row=0, column=0, padx=5)

        btn_back = tk.Button(btn_frame, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.grid(row=0, column=1, padx=5)

        self.refresh_data()

    def refresh_data(self):
        # 清空 Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn, cursor = get_db_cursor()
        # GROUP BY 名稱,單位，庫存量加總，安全庫存用 MAX 或 MIN 皆可
        sql = """
        SELECT material_name, unit, SUM(quantity_in_stock), MAX(safety_stock)
        FROM raw_materials
        GROUP BY material_name, unit
        ORDER BY material_name
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            mat_name, unit, total_stock, safety_stock = r
            self.tree.insert("", tk.END, values=(mat_name, unit, total_stock, safety_stock))


# -- (D) 新增「成品」 ----------------------------------------------------------
class AddProductFrame(tk.Frame):
    """
    新增成品：輸入 (名稱, 包裝, 單位)，安全庫存省略。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="新增成品", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="成品名稱:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_name = tk.Entry(form_frame)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="包裝資訊:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_pack = tk.Entry(form_frame)
        self.entry_pack.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="單位(如 箱, 罐):").grid(row=2, column=0, padx=5, pady=5)
        self.entry_unit = tk.Entry(form_frame)
        self.entry_unit.grid(row=2, column=1, padx=5, pady=5)

        btn_add = tk.Button(self, text="新增", command=self.add_product)
        btn_add.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

    def add_product(self):
        p_name = self.entry_name.get().strip()
        p_pack = self.entry_pack.get().strip()
        p_unit = self.entry_unit.get().strip()

        if not p_name:
            messagebox.showerror("錯誤", "成品名稱不能空白！")
            return
        if not p_pack:
            p_pack = ""
        if not p_unit:
            p_unit = ""

        conn, cursor = get_db_cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO finished_products (product_name, package_info, unit, quantity_in_stock, safety_stock, created_at)
        VALUES (?, ?, ?, 0, 0, ?)
        """
        cursor.execute(sql, (p_name, p_pack, p_unit, created_at))
        conn.commit()
        conn.close()

        messagebox.showinfo("成功", f"已新增成品：{p_name}")
        self.entry_name.delete(0, tk.END)
        self.entry_pack.delete(0, tk.END)
        self.entry_unit.delete(0, tk.END)


# -- (E) 查詢「成品」 ----------------------------------------------------------
class ListProductFrame(tk.Frame):
    """
    查詢成品，使用 Treeview 類似 Excel 表格。
    依成品名稱+包裝做加總。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="成品清單 (名稱加總)", font=("Arial", 16))
        label.pack(pady=10)

        columns = ("product_name", "package_info", "unit", "quantity_in_stock", "safety_stock")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        self.tree.heading("product_name", text="成品名稱")
        self.tree.heading("package_info", text="包裝")
        self.tree.heading("unit", text="單位")
        self.tree.heading("quantity_in_stock", text="庫存(加總)")
        self.tree.heading("safety_stock", text="安全庫存")

        self.tree.column("product_name", width=200)
        self.tree.column("package_info", width=100)
        self.tree.column("unit", width=80)
        self.tree.column("quantity_in_stock", width=100)
        self.tree.column("safety_stock", width=100)
        self.tree.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        btn_refresh = tk.Button(btn_frame, text="刷新", command=self.refresh_data)
        btn_refresh.grid(row=0, column=0, padx=5)

        btn_back = tk.Button(btn_frame, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.grid(row=0, column=1, padx=5)

        self.refresh_data()

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn, cursor = get_db_cursor()
        sql = """
        SELECT product_name, package_info, unit,
               SUM(quantity_in_stock), MAX(safety_stock)
        FROM finished_products
        GROUP BY product_name, package_info, unit
        ORDER BY product_name
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            name, pack, unit, total_stock, safety_stock = r
            self.tree.insert("", tk.END, values=(name, pack, unit, total_stock, safety_stock))


# -- (F) 手動「調整【原料】庫存」 -----------------------------------------------
class AdjustMaterialStockFrame(tk.Frame):
    """
    調整原料庫存（正加/負減），並寫入 stock_log。
    下拉選單只顯示資料庫既有的原料名稱，避免輸入錯誤。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="調整【原料】庫存", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        # 原料名稱下拉框
        tk.Label(form_frame, text="選擇原料:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_material = ttk.Combobox(form_frame, state="readonly")
        self.combo_material.grid(row=0, column=1, padx=5, pady=5)

        # 調整數量
        tk.Label(form_frame, text="調整數量 (+/-):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_qty = tk.Entry(form_frame)
        self.entry_qty.grid(row=1, column=1, padx=5, pady=5)

        # 原因
        tk.Label(form_frame, text="原因(可留空):").grid(row=2, column=0, padx=5, pady=5)
        self.entry_reason = tk.Entry(form_frame)
        self.entry_reason.grid(row=2, column=1, padx=5, pady=5)

        btn_adjust = tk.Button(self, text="確定調整", command=self.adjust_stock)
        btn_adjust.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

        # 初始化下拉選單
        self.refresh_material_list()

    def refresh_material_list(self):
        """
        抓取所有 raw_materials，填入 Combobox。
        這裡用名稱來辨識，但實務上最好以 ID 區分(可顯示 'ID-Name')。
        """
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT material_id, material_name FROM raw_materials ORDER BY material_id")
        rows = cursor.fetchall()
        conn.close()

        # 以 dict 保存 {名稱: material_id}，後續存/查皆可。
        self.name_to_id = {}
        mat_list = []
        for r in rows:
            mid, mname = r
            mat_list.append(mname)
            self.name_to_id[mname] = mid

        self.combo_material['values'] = mat_list
        if mat_list:
            self.combo_material.current(0)  # 預設選第一筆

    def adjust_stock(self):
        mat_name = self.combo_material.get()
        if not mat_name:
            messagebox.showerror("錯誤", "尚無原料可調整")
            return
        try:
            qty = float(self.entry_qty.get())
        except ValueError:
            messagebox.showerror("錯誤", "調整數量須為數字")
            return

        reason = self.entry_reason.get().strip()
        mat_id = self.name_to_id[mat_name]

        conn, cursor = get_db_cursor()
        cursor.execute("SELECT quantity_in_stock FROM raw_materials WHERE material_id=?", (mat_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("錯誤", "原料不存在")
            return

        old_stock = row[0]
        new_stock = old_stock + qty

        # 更新庫存
        cursor.execute("UPDATE raw_materials SET quantity_in_stock=? WHERE material_id=?", (new_stock, mat_id))

        # 寫 stock_log
        change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
        """, (change_date, mat_id, qty, old_stock, new_stock, "manual_adjust", reason))

        conn.commit()
        conn.close()

        messagebox.showinfo("完成", f"原料【{mat_name}】由 {old_stock} 改為 {new_stock}")
        # 清空
        self.entry_qty.delete(0, tk.END)
        self.entry_reason.delete(0, tk.END)


# -- (G) 手動「調整【成品】庫存」 -----------------------------------------------
class AdjustProductStockFrame(tk.Frame):
    """
    調整成品庫存（正加/負減），並寫入 stock_log。
    下拉選單只顯示既有成品名稱。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="調整【成品】庫存", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        # 成品名稱下拉
        tk.Label(form_frame, text="選擇成品:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_product = ttk.Combobox(form_frame, state="readonly")
        self.combo_product.grid(row=0, column=1, padx=5, pady=5)

        # 調整數量
        tk.Label(form_frame, text="調整數量(+/-):").grid(row=1, column=0, padx=5, pady=5)
        self.entry_qty = tk.Entry(form_frame)
        self.entry_qty.grid(row=1, column=1, padx=5, pady=5)

        # 原因
        tk.Label(form_frame, text="原因(可留空):").grid(row=2, column=0, padx=5, pady=5)
        self.entry_reason = tk.Entry(form_frame)
        self.entry_reason.grid(row=2, column=1, padx=5, pady=5)

        btn_adjust = tk.Button(self, text="確定調整", command=self.adjust_stock)
        btn_adjust.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

        self.refresh_product_list()

    def refresh_product_list(self):
        """
        查詢 finished_products，填入下拉選單。
        """
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT product_id, product_name FROM finished_products ORDER BY product_id")
        rows = cursor.fetchall()
        conn.close()

        self.name_to_id = {}
        prod_list = []
        for r in rows:
            pid, pname = r
            prod_list.append(pname)
            self.name_to_id[pname] = pid

        self.combo_product['values'] = prod_list
        if prod_list:
            self.combo_product.current(0)

    def adjust_stock(self):
        p_name = self.combo_product.get()
        if not p_name:
            messagebox.showerror("錯誤", "尚無成品可調整")
            return
        try:
            qty = float(self.entry_qty.get())
        except ValueError:
            messagebox.showerror("錯誤", "調整數量須為數字")
            return

        reason = self.entry_reason.get().strip()
        p_id = self.name_to_id[p_name]

        conn, cursor = get_db_cursor()
        cursor.execute("SELECT quantity_in_stock FROM finished_products WHERE product_id=?", (p_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("錯誤", "成品不存在")
            return

        old_stock = row[0]
        new_stock = old_stock + qty

        # 更新
        cursor.execute("UPDATE finished_products SET quantity_in_stock=? WHERE product_id=?", (new_stock, p_id))

        # stock_log
        change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
        """, (change_date, p_id, qty, old_stock, new_stock, "manual_adjust", reason))

        conn.commit()
        conn.close()

        messagebox.showinfo("完成", f"成品【{p_name}】由 {old_stock} 改為 {new_stock}")
        self.entry_qty.delete(0, tk.END)
        self.entry_reason.delete(0, tk.END)


# -- (H) 建立生產工單 ----------------------------------------------------------
class CreateProductionOrderFrame(tk.Frame):
    """
    建立生產工單：選擇成品(Combobox)、輸入計畫量、備註。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="建立生產工單", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="選擇成品:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_product = ttk.Combobox(form_frame, state="readonly")
        self.combo_product.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="計畫生產量:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_plan_qty = tk.Entry(form_frame)
        self.entry_plan_qty.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="備註(可留空):").grid(row=2, column=0, padx=5, pady=5)
        self.entry_remarks = tk.Entry(form_frame)
        self.entry_remarks.grid(row=2, column=1, padx=5, pady=5)

        btn_create = tk.Button(self, text="建立", command=self.create_production_order)
        btn_create.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

        self.refresh_product_list()

    def refresh_product_list(self):
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT product_id, product_name FROM finished_products")
        rows = cursor.fetchall()
        conn.close()

        self.name_to_id = {}
        prod_names = []
        for r in rows:
            pid, pname = r
            prod_names.append(pname)
            self.name_to_id[pname] = pid

        self.combo_product['values'] = prod_names
        if prod_names:
            self.combo_product.current(0)

    def create_production_order(self):
        p_name = self.combo_product.get()
        plan_str = self.entry_plan_qty.get()
        remarks = self.entry_remarks.get().strip()

        if not p_name:
            messagebox.showerror("錯誤", "尚無成品可選擇")
            return
        try:
            plan_qty = float(plan_str)
        except ValueError:
            messagebox.showerror("錯誤", "計畫量須為數字")
            return

        p_id = self.name_to_id[p_name]
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Planned"

        conn, cursor = get_db_cursor()
        sql = """
        INSERT INTO production_orders (product_id, planned_qty, actual_qty, start_date, status, remarks)
        VALUES (?, ?, 0, ?, ?, ?)
        """
        cursor.execute(sql, (p_id, plan_qty, start_date, status, remarks))
        prod_id = cursor.lastrowid

        conn.commit()
        conn.close()

        messagebox.showinfo("成功", f"已建立生產工單ID={prod_id}")
        self.entry_plan_qty.delete(0, tk.END)
        self.entry_remarks.delete(0, tk.END)


# -- (I) BOM套用：將理論用料寫入 production_materials ---------------------------
class PlanProductionMaterialsFrame(tk.Frame):
    """
    選擇生產工單ID，根據 BOM 幫該工單產生理論用料。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="BOM套用(理論用料)", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="選擇 Production ID:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_prod_id = ttk.Combobox(form_frame, state="readonly")
        self.combo_prod_id.grid(row=0, column=1, padx=5, pady=5)

        btn_plan = tk.Button(self, text="執行BOM套用", command=self.plan_bom)
        btn_plan.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

        self.refresh_production_list()

    def refresh_production_list(self):
        """
        查詢所有 production_orders，顯示 ID、status。
        """
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT production_id, status FROM production_orders ORDER BY production_id")
        rows = cursor.fetchall()
        conn.close()

        self.id_to_status = {}
        pid_list = []
        for r in rows:
            pid, status = r
            display_str = f"{pid} (status={status})"
            pid_list.append(display_str)
            self.id_to_status[display_str] = pid

        self.combo_prod_id['values'] = pid_list
        if pid_list:
            self.combo_prod_id.current(0)

    def plan_bom(self):
        combo_val = self.combo_prod_id.get()
        if not combo_val:
            messagebox.showerror("錯誤", "尚無生產工單可選")
            return
        prod_id = self.id_to_status[combo_val]  # 取得實際 production_id

        conn, cursor = get_db_cursor()
        # 查該 production_order 的 product_id, planned_qty
        cursor.execute("SELECT product_id, planned_qty FROM production_orders WHERE production_id=?", (prod_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("錯誤", f"找不到生產工單ID={prod_id}")
            return
        product_id, planned_qty = row

        # 依 BOM 插入到 production_materials
        cursor.execute("SELECT raw_material_id, quantity_needed FROM bom WHERE finished_product_id=?", (product_id,))
        bom_rows = cursor.fetchall()
        if not bom_rows:
            conn.close()
            messagebox.showerror("錯誤", "BOM中沒有此成品的配方")
            return

        for (mat_id, needed_per_unit) in bom_rows:
            plan_use = needed_per_unit * planned_qty
            cursor.execute("""
                INSERT INTO production_materials (production_id, material_id, planned_qty, actual_qty)
                VALUES (?, ?, ?, 0)
            """, (prod_id, mat_id, plan_use))

        conn.commit()
        conn.close()

        messagebox.showinfo("完成", f"生產工單 {prod_id} 已根據BOM生成理論用料。")


# -- (J) 完工 (扣原料+加成品) --------------------------------------------------
class FinishProductionFrame(tk.Frame):
    """
    選擇工單ID、輸入實際產量，然後依 production_materials 扣原料庫存並加成品庫存，並寫入 stock_log。
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="完工(扣原料+加成品)", font=("Arial", 16))
        label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="選擇 Production ID:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_prod_id = ttk.Combobox(form_frame, state="readonly")
        self.combo_prod_id.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="實際產量:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_actual = tk.Entry(form_frame)
        self.entry_actual.grid(row=1, column=1, padx=5, pady=5)

        btn_finish = tk.Button(self, text="完工", command=self.finish_production)
        btn_finish.pack(pady=5)

        btn_back = tk.Button(self, text="上一頁",
                             command=lambda: controller.show_frame(MainMenuFrame))
        btn_back.pack(pady=10)

        self.refresh_production_list()

    def refresh_production_list(self):
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT production_id, status FROM production_orders ORDER BY production_id")
        rows = cursor.fetchall()
        conn.close()

        self.id_map = {}
        pid_list = []
        for r in rows:
            pid, status = r
            combo_str = f"{pid} (status={status})"
            pid_list.append(combo_str)
            self.id_map[combo_str] = pid

        self.combo_prod_id['values'] = pid_list
        if pid_list:
            self.combo_prod_id.current(0)

    def finish_production(self):
        combo_val = self.combo_prod_id.get()
        if not combo_val:
            messagebox.showerror("錯誤", "尚無可選的生產工單")
            return
        production_id = self.id_map[combo_val]

        try:
            actual_qty = float(self.entry_actual.get())
        except ValueError:
            messagebox.showerror("錯誤", "實際產量須為數字")
            return

        conn, cursor = get_db_cursor()
        # 查 product_id, planned_qty
        cursor.execute("SELECT product_id, planned_qty FROM production_orders WHERE production_id=?", (production_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("錯誤", f"production_id={production_id} 不存在")
            return
        product_id, planned_qty = row

        ratio = 0
        if planned_qty != 0:
            ratio = actual_qty / planned_qty

        # 查 production_materials
        cursor.execute("""
            SELECT pm_id, material_id, planned_qty, actual_qty
            FROM production_materials
            WHERE production_id=?
        """, (production_id,))
        pm_rows = cursor.fetchall()

        for (pm_id, material_id, plan_use, old_actual) in pm_rows:
            real_usage = plan_use * ratio
            # 更新 production_materials.actual_qty
            cursor.execute("""
                UPDATE production_materials
                SET actual_qty=?
                WHERE pm_id=?
            """, (real_usage, pm_id))

            # 扣原料庫存
            cursor.execute("SELECT quantity_in_stock FROM raw_materials WHERE material_id=?", (material_id,))
            mat_row = cursor.fetchone()
            if mat_row:
                old_stock = mat_row[0]
                new_stock = old_stock - real_usage
                cursor.execute("""
                    UPDATE raw_materials
                    SET quantity_in_stock=?
                    WHERE material_id=?
                """, (new_stock, material_id))

                # stock_log
                change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reason = f"生產工單ID={production_id}"
                cursor.execute("""
                    INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
                    VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """, (change_date, material_id, -real_usage, old_stock, new_stock, "production", reason))

        # 加成品庫存
        cursor.execute("SELECT quantity_in_stock FROM finished_products WHERE product_id=?", (product_id,))
        prod_row = cursor.fetchone()
        if prod_row:
            old_prod = prod_row[0]
            new_prod = old_prod + actual_qty
            cursor.execute("""
                UPDATE finished_products
                SET quantity_in_stock=?
                WHERE product_id=?
            """, (new_prod, product_id))

            # stock_log
            change_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reason = f"生產工單ID={production_id}"
            cursor.execute("""
                INSERT INTO stock_log (change_date, material_id, product_id, change_qty, old_qty, new_qty, change_type, reason)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
            """, (change_date, product_id, actual_qty, old_prod, new_prod, "production", reason))

        # 更新 production_orders
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE production_orders
            SET actual_qty=?, end_date=?, status='Completed'
            WHERE production_id=?
        """, (actual_qty, end_date, production_id))

        conn.commit()
        conn.close()

        messagebox.showinfo("完成", f"生產工單 {production_id} 已完工, 實際產量={actual_qty}")
        self.entry_actual.delete(0, tk.END)


###############################################################################
# 4. 主程式執行
###############################################################################
if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
