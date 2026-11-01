import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import datetime
from decimal import Decimal
import threading
import re
import PyPDF2

class PersonalFinanceGUI:
    def __init__(self, master):
        self.root = master
        self.root.title("Finance Tracer")
        self.root.geometry("1000x650")
        
        # Quirky Minimalist Palette
        self.bg_color = "#F4F4F6"      
        self.card_color = "#FFFFFF"    
        self.text_color = "#2B2D42"    
        self.accent_1 = "#FF6B6B"      
        self.accent_2 = "#4ECDC4"      
        
        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        
        self.mydb = None
        self.cursor = None
        self.connect_db()

        self.chart_canvas = None
        self.create_login_screen()

    def setup_styles(self):
        style = ttk.Style(self.root)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        main_font = ("Trebuchet MS", 11)
        bold_font = ("Trebuchet MS", 11, "bold")
        title_font = ("Trebuchet MS", 24, "bold")
        
        style.configure(".", font=main_font, background=self.bg_color, foreground=self.text_color)
        style.configure("Card.TFrame", background=self.card_color)
        style.configure("Card.TLabel", background=self.card_color, font=main_font)
        style.configure("Header.TLabel", font=title_font, background=self.card_color, foreground=self.text_color)
        style.configure("SubHeader.TLabel", font=bold_font, background=self.card_color, foreground=self.text_color)
        
        style.configure("TButton", font=bold_font, padding=8, relief="flat", borderwidth=0)
        style.configure("Primary.TButton", background=self.accent_1, foreground="white")
        style.map("Primary.TButton", background=[('active', '#FF8787')])
        style.configure("Success.TButton", background=self.accent_2, foreground="white")
        style.map("Success.TButton", background=[('active', '#6EDCD5')])

        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", font=bold_font, padding=[15, 10], background="#EAEAEA", borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.card_color)], foreground=[("selected", self.accent_1)]) 

        style.configure("Treeview", font=("Trebuchet MS", 10), rowheight=35, background=self.card_color, fieldbackground=self.card_color, borderwidth=0)
        style.configure("Treeview.Heading", font=bold_font, background=self.card_color, foreground=self.text_color, relief="flat", borderwidth=0)
        style.map("Treeview", background=[('selected', self.accent_2)], foreground=[('selected', "white")])

    def connect_db(self):
        try:
            self.mydb = mysql.connector.connect(
                host="localhost",
                user="Lakshya",
                password="laks"
            )
            self.cursor = self.mydb.cursor()
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS finance")
            self.cursor.execute("USE finance")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type ENUM('Income', 'Expense') NOT NULL,
                    amount DECIMAL(12, 2) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    description VARCHAR(255),
                    transaction_date DATE NOT NULL
                )
            """)
            self.mydb.commit()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Connection failed:\n{e}")
            self.root.destroy()

    def create_login_screen(self):
        self.login_container = tk.Frame(self.root, bg=self.bg_color)
        self.login_container.pack(expand=True, fill="both")

        self.login_frame = ttk.Frame(self.login_container, style="Card.TFrame")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=350)

        ttk.Label(self.login_frame, text="hello.", style="Header.TLabel").pack(pady=(40, 20))
        ttk.Label(self.login_frame, text="username", style="Card.TLabel").pack(anchor="w", padx=40)
        self.entry_user = tk.Entry(self.login_frame, font=("Trebuchet MS", 12), relief="flat", bg="#F4F4F6", highlightthickness=1, highlightcolor=self.accent_2)
        self.entry_user.pack(fill="x", padx=40, pady=(0, 15), ipady=5)

        ttk.Label(self.login_frame, text="password", style="Card.TLabel").pack(anchor="w", padx=40)
        self.entry_pass = tk.Entry(self.login_frame, show="*", font=("Trebuchet MS", 12), relief="flat", bg="#F4F4F6", highlightthickness=1, highlightcolor=self.accent_2)
        self.entry_pass.pack(fill="x", padx=40, pady=(0, 30), ipady=5)

        ttk.Button(self.login_frame, text="ENTER", style="Primary.TButton", command=self.verify_login).pack(fill="x", padx=40, pady=10)

    def verify_login(self):
        if self.entry_user.get() == "admin" and self.entry_pass.get() == "123":
            self.login_container.destroy()
            self.create_main_app()
        else:
            messagebox.showerror("Error", "Invalid Username or Password")

    def create_main_app(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_add = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_upload = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_summary = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_search = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_add, text=" ✧ add ")
        self.notebook.add(self.tab_upload, text=" ✦ upload ")
        self.notebook.add(self.tab_summary, text=" ◒ summary ")
        self.notebook.add(self.tab_search, text=" ⌕ search ")

        self.build_add_tab()
        self.build_upload_tab()
        self.build_summary_tab()
        self.build_search_tab()

    # ---------------- 1. ADD TRANSACTION TAB ----------------
    def build_add_tab(self):
        card = ttk.Frame(self.tab_add, style="Card.TFrame")
        card.place(relx=0.5, rely=0.4, anchor="center")
        
        ttk.Label(card, text="New entry.", style="Header.TLabel").grid(row=0, columnspan=2, pady=(0, 20))

        labels = ["type", "amount (₹)", "category", "description", "date (yyyy-mm-dd)"]
        for i, text in enumerate(labels):
            ttk.Label(card, text=text, style="Card.TLabel").grid(row=i+1, column=0, padx=10, pady=12, sticky="e")

        self.var_type = tk.StringVar(value="Income")
        ttk.Combobox(card, textvariable=self.var_type, values=["Income", "Expense"], state="readonly", font=("Trebuchet MS", 11)).grid(row=1, column=1, padx=10, pady=12, sticky="ew")

        self.entry_amount = ttk.Entry(card, font=("Trebuchet MS", 11))
        self.entry_amount.grid(row=2, column=1, padx=10, pady=12, sticky="ew")

        self.entry_category = ttk.Entry(card, font=("Trebuchet MS", 11))
        self.entry_category.grid(row=3, column=1, padx=10, pady=12, sticky="ew")

        self.entry_desc = ttk.Entry(card, font=("Trebuchet MS", 11))
        self.entry_desc.grid(row=4, column=1, padx=10, pady=12, sticky="ew")

        self.entry_date = ttk.Entry(card, font=("Trebuchet MS", 11))
        self.entry_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.entry_date.grid(row=5, column=1, padx=10, pady=12, sticky="ew")

        ttk.Button(card, text="SAVE", style="Success.TButton", command=self.save_transaction).grid(row=6, columnspan=2, pady=(30, 0), ipadx=30)

    def save_transaction(self):
        if not self.cursor or not self.mydb: return
        try:
            t_type = self.var_type.get()
            amount = Decimal(self.entry_amount.get().strip()).quantize(Decimal("0.01"))
            category = self.entry_category.get().strip()
            desc = self.entry_desc.get().strip()
            t_date = datetime.strptime(self.entry_date.get().strip(), "%Y-%m-%d").date()
            
            if amount <= 0 or not category: raise ValueError
            
            self.cursor.execute("INSERT INTO transactions (type, amount, category, description, transaction_date) VALUES (%s, %s, %s, %s, %s)", 
                                (t_type, amount, category, desc or None, t_date))
            self.mydb.commit()
            messagebox.showinfo("Success", "Entry saved.")
            self.entry_amount.delete(0, tk.END)
            self.entry_category.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
        except:
            messagebox.showerror("Error", "Check your inputs.")

    # ---------------- 2. AUTO UPLOAD TAB ----------------
    def build_upload_tab(self):
        card = ttk.Frame(self.tab_upload, style="Card.TFrame", padding=40)
        card.place(relx=0.5, rely=0.4, anchor="center")

        ttk.Label(card, text="file upload.", style="Header.TLabel").pack(pady=(0, 10))
        ttk.Label(card, text="Upload bank statement (PDF, or CSV).", background=self.card_color, foreground="#999999").pack(pady=(0, 10))
        
        self.upload_status = ttk.Label(card, text="Ready.", background=self.card_color, foreground=self.accent_2)
        self.upload_status.pack(pady=(0, 20))
        
        ttk.Button(card, text="SELECT FILE", style="Primary.TButton", command=self.start_auto_upload).pack(ipadx=20, ipady=5)

    def start_auto_upload(self):
        if not self.cursor or not self.mydb: return
        filepath = filedialog.askopenfilename(filetypes=[("Statement Files", "*.pdf *.csv *.txt")])
        if not filepath: return
        
        self.upload_status.config(text="Processing document... (please wait)", foreground=self.accent_1)
        threading.Thread(target=self.process_document_auto, args=(filepath,), daemon=True).start()

    def process_document_auto(self, filepath):
        try:
            lines = []
            if filepath.lower().endswith('.pdf'):
                reader = PyPDF2.PdfReader(filepath)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        lines.extend(extracted.splitlines())
            else:
                with open(filepath, "r", encoding="utf-8-sig") as file:
                    lines = file.readlines()

            records = []
            
            # Common regex patterns for date and numerical amounts
            date_pattern = r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})'

            # Expanded Keyword-to-Category Mappings (39 categories total)
            keyword_map = {
                'Groceries': ['grocery', 'supermarket', 'blinkit', 'zepto', 'bigbasket'],
                'Snacks & Coffee': ['coffee', 'cafe', 'tea', 'starbucks', 'bakery'],
                'Dining Out': ['dining', 'restaurant', 'zomato', 'swiggy', 'bistro'],
                'Fast Food': ['mcdonalds', 'kfc', 'burger', 'pizza', 'dominos'],
                'E-Commerce': ['amazon', 'flipkart', 'myntra', 'meesho'],
                'Electronics': ['croma', 'reliance digital', 'apple', 'laptop', 'gadgets'],
                'Clothing': ['zara', 'h&m', 'apparel', 'trends', 'fashion'],
                'Home Decor': ['ikea', 'furniture', 'decor', 'curtains'],
                'Electricity': ['electricity', 'power', 'bescom', 'state electricity'],
                'Water Bill': ['water', 'jal board'],
                'Wi-Fi & Broadband': ['wifi', 'broadband', 'act fiber', 'airtel xtream', 'jiofiber'],
                'Piped Gas': ['gas bill', 'piped gas', 'indane', 'hp gas'],
                'Mobile Recharge': ['recharge', 'prepaid'],
                'Postpaid Mobile Bill': ['postpaid', 'mobile bill'],
                'House Rent': ['house rent', 'flat rent', 'landlord'],
                'Maintenance Charges': ['society maintenance', 'maintenance', 'housing fee'],
                'Streaming Subscriptions': ['netflix', 'spotify', 'prime video', 'hotstar', 'youtube'],
                'Movies & Events': ['bookmyshow', 'cinema', 'pvr', 'inox'],
                'Gaming': ['playstation', 'steam', 'xbox', 'nintendo'],
                'Hobbies': ['craft', 'music class', 'sports center', 'bookstore'],
                'Fuel & Gas': ['petrol', 'diesel', 'fuel', 'hpcl', 'bpcl', 'iocl'],
                'Cab & Ride Share': ['uber', 'ola', 'rapido'],
                'Public Transit': ['metro', 'bus', 'train', 'irctc'],
                'Vehicle Servicing': ['car service', 'bike repair', 'garage', 'mechanic'],
                'Pharmacy & Medicines': ['pharmacy', 'apollo', 'pharmeasy', '1mg', 'chemist'],
                'Doctor Consultation': ['hospital', 'clinic', 'doctor', 'consultation'],
                'Gym & Fitness': ['gym', 'cult.fit', 'fitness', 'yoga'],
                'Health Insurance': ['health insurance', 'mediclaim'],
                'Tuition & School Fees': ['tuition', 'school fee', 'college fee'],
                'Books & Supplies': ['stationery', 'textbooks', 'books'],
                'Online Learning': ['udemy', 'coursera', 'unacademy'],
                'Salary Credit': ['monthly salary', 'salary', 'payroll'],
                'Performance Bonus': ['bonus', 'incentive'],
                'Freelance Income': ['freelance', 'client payout'],
                'Consulting Fees': ['consulting', 'advisory fee'],
                'Savings Interest': ['savings account interest', 'savings interest'],
                'FD Interest': ['fd interest', 'fixed deposit interest'],
                'Gift Received': ['gift', 'cashback reward'],
                'Cashback & Rewards': ['cashback', 'reward']
            }

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                dates = re.findall(date_pattern, line)
                amounts = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d{1,2})\b', line)

                if dates and amounts:
                    try:
                        raw_date = dates[0]
                        formatted_date = datetime.today().strftime('%Y-%m-%d')
                        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
                            try:
                                formatted_date = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                pass

                        raw_amount = Decimal(amounts[0].replace(',', '')).quantize(Decimal("0.01"))
                        if raw_amount <= 0:
                            continue

                        line_lower = line.lower()
                        t_type = "Income" if any(w in line_lower for w in ['cr', 'credit', 'deposit', 'salary', 'received', 'bonus', 'interest']) else "Expense"

                        category = "Other"
                        for cat_name, keywords in keyword_map.items():
                            if any(kw in line_lower for kw in keywords):
                                category = cat_name
                                break

                        description = line[:250]
                        records.append((t_type, raw_amount, category, description, formatted_date))

                    except Exception:
                        continue

            if records:
                if self.cursor and self.mydb:
                    self.cursor.executemany(
                        "INSERT INTO transactions (type, amount, category, description, transaction_date) VALUES (%s, %s, %s, %s, %s)", 
                        records
                    )
                    self.mydb.commit()
                self.root.after(0, lambda: self.upload_status.config(text=f"Success! {len(records)} entries extracted across {len(set([r[2] for r in records]))} categories.", foreground=self.accent_2))
                self.root.after(0, lambda: messagebox.showinfo("Done", f"Successfully extracted and saved all {len(records)} entries!"))
            else:
                self.root.after(0, lambda: self.upload_status.config(text="No transactions detected.", foreground=self.accent_1))

        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: self.upload_status.config(text="An error occurred.", foreground=self.accent_1))
            self.root.after(0, lambda msg=error_message: messagebox.showerror("Import Error", msg))

    # ---------------- 3. VIEW SUMMARY TAB ----------------
    def build_summary_tab(self):
        frame_top = ttk.Frame(self.tab_summary, style="Card.TFrame")
        frame_top.pack(fill="x", padx=30, pady=20)

        ttk.Label(frame_top, text="filter: ", style="Card.TLabel").pack(side="left")
        self.var_period = tk.StringVar(value="All Time")
        ttk.Combobox(frame_top, textvariable=self.var_period, values=["All Time", "This Year", "This Month"], state="readonly", width=15).pack(side="left", padx=10)
        ttk.Button(frame_top, text="REFRESH", style="Primary.TButton", command=self.generate_summary).pack(side="left", padx=10)

        self.lbl_totals = ttk.Label(self.tab_summary, text="ready.", font=("Trebuchet MS", 14, "bold"), background=self.card_color, foreground="#999999")
        self.lbl_totals.pack(pady=(0, 20))

        frame_content = ttk.Frame(self.tab_summary, style="Card.TFrame")
        frame_content.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        frame_table = ttk.Frame(frame_content, style="Card.TFrame")
        frame_table.pack(side="left", fill="both", expand=True)

        columns = ("Category", "Income", "Expense", "Net", "Count")
        self.tree_summary = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree_summary.heading(col, text=col.lower()) 
            self.tree_summary.column(col, width=80, anchor="center")
        self.tree_summary.pack(side="left", fill="both", expand=True)

        self.frame_chart = ttk.Frame(frame_content, style="Card.TFrame", width=300)
        self.frame_chart.pack(side="right", fill="both", expand=True, padx=(20, 0))

    def generate_summary(self):
        if not self.cursor or not self.mydb: return
        period = self.var_period.get()
        where_clause = ""
        if period == "This Year":
            where_clause = f"WHERE YEAR(transaction_date) = {datetime.today().year}"
        elif period == "This Month":
            where_clause = f"WHERE YEAR(transaction_date) = {datetime.today().year} AND MONTH(transaction_date) = {datetime.today().month}"

        self.cursor.execute(f"SELECT COALESCE(SUM(CASE WHEN type='Income' THEN amount ELSE 0 END),0), COALESCE(SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END),0) FROM transactions {where_clause}")
        tot_inc, tot_exp = self.cursor.fetchone()
        balance = tot_inc - tot_exp
        
        color = self.accent_1 if balance < 0 else self.accent_2 
        self.lbl_totals.config(text=f"Total Income: ₹{tot_inc:,.2f}  |  Total Expenses: ₹{tot_exp:,.2f}  |  Net Balance: ₹{balance:,.2f}", foreground=color)

        self.cursor.execute(f"SELECT category, COALESCE(SUM(CASE WHEN type='Income' THEN amount ELSE 0 END),0) as inc, COALESCE(SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END),0) as exp, COUNT(*) FROM transactions {where_clause} GROUP BY category")
        
        for row in self.tree_summary.get_children(): self.tree_summary.delete(row)
        
        expense_labels, expense_values = [], []
        for cat, inc, exp, count in self.cursor.fetchall():
            self.tree_summary.insert("", "end", values=(cat.lower(), f"₹{inc:,.2f}", f"₹{exp:,.2f}", f"₹{inc-exp:,.2f}", count))
            if exp > 0:
                expense_labels.append(cat.lower())
                expense_values.append(float(exp))

        if self.chart_canvas: self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.card_color)
        ax = fig.add_subplot(111)
        
        if expense_values:
            distinct_colors = [
                self.accent_1, self.accent_2, "#FFC857", "#484D6D", 
                "#9D4EDD", "#2EC4B6", "#FF9F1C", "#FE4A90", 
                "#8AC926", "#1982C4", "#6A4C93", "#E9724C", 
                "#8D99AE", "#D90429", "#00B4D8"
            ]
            wedges, _, _ = ax.pie(
                expense_values, autopct='%1.1f%%', startangle=90, 
                colors=distinct_colors,
                textprops={'color': self.text_color, 'fontsize': 8}, pctdistance=0.8
            )
            
            ax.set_title("Expenses by Category", color=self.text_color, pad=10, fontdict={'fontname': 'DejaVu Sans', 'weight': 'bold'})
            ax.legend(wedges, expense_labels, title="Categories", loc="center left", bbox_to_anchor=(0.95, 0.5), frameon=False, fontsize=8, title_fontsize=9)
            fig.subplots_adjust(left=0.0, right=0.65)
        else:
            ax.text(0.5, 0.5, "No Expenses Yet", ha='center', va='center', color="#999999", fontname='DejaVu Sans')
            ax.axis('off')

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.frame_chart)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------------- 4. SEARCH RECORDS TAB ----------------
    def build_search_tab(self):
        frame_top = ttk.Frame(self.tab_search, style="Card.TFrame")
        frame_top.pack(fill="x", padx=30, pady=20)

        ttk.Label(frame_top, text="category: ", style="Card.TLabel").pack(side="left")
        self.search_category = ttk.Entry(frame_top, width=12)
        self.search_category.pack(side="left", padx=5)

        ttk.Label(frame_top, text="type: ", style="Card.TLabel").pack(side="left", padx=(10, 0))
        self.search_type = ttk.Combobox(frame_top, values=["All", "Income", "Expense"], state="readonly", width=8)
        self.search_type.set("All")
        self.search_type.pack(side="left", padx=5)

        ttk.Label(frame_top, text="from (yyyy-mm-dd): ", style="Card.TLabel").pack(side="left", padx=(10, 0))
        self.search_date_from = ttk.Entry(frame_top, width=11)
        self.search_date_from.pack(side="left", padx=5)

        ttk.Label(frame_top, text="to: ", style="Card.TLabel").pack(side="left", padx=(5, 0))
        self.search_date_to = ttk.Entry(frame_top, width=11)
        self.search_date_to.pack(side="left", padx=5)

        ttk.Button(frame_top, text="SEARCH", style="Success.TButton", command=self.execute_search).pack(side="left", padx=(15, 0))

        frame_table = ttk.Frame(self.tab_search, style="Card.TFrame")
        frame_table.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        columns = ("ID", "Date", "Type", "Amount", "Category", "Description")
        self.tree_search = ttk.Treeview(frame_table, columns=columns, show="headings", height=12)
        scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree_search.yview)
        self.tree_search.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        widths = [40, 90, 80, 100, 130, 200]
        for col, w in zip(columns, widths):
            self.tree_search.heading(col, text=col.lower())
            self.tree_search.column(col, width=w, anchor="center" if col != "Description" else "w")
            
        self.tree_search.pack(side="left", fill="both", expand=True)

    def execute_search(self):
        if not self.cursor or not self.mydb: return
        
        cat = self.search_category.get().strip()
        t_type = self.search_type.get()
        date_from = self.search_date_from.get().strip()
        date_to = self.search_date_to.get().strip()
        
        query, params = "SELECT id, transaction_date, type, amount, category, description FROM transactions WHERE 1=1", []
        
        if cat: 
            query += " AND category LIKE %s"
            params.append(f"%{cat}%")
        if t_type != "All": 
            query += " AND type = %s"
            params.append(t_type)
        if date_from:
            query += " AND transaction_date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND transaction_date <= %s"
            params.append(date_to)
        
        try:
            self.cursor.execute(query + " ORDER BY transaction_date DESC", tuple(params))
            
            for row in self.tree_search.get_children(): 
                self.tree_search.delete(row)
                
            for id, date, typ, amt, category, desc in self.cursor.fetchall():
                self.tree_search.insert("", "end", values=(id, date, typ.lower(), f"₹ {amt:,.2f}", category.lower(), desc or "-"))
                
        except mysql.connector.Error:
            messagebox.showerror("Search Error", "Invalid date format or database error.\nPlease use YYYY-MM-DD.")

    def __del__(self):
        if self.cursor: self.cursor.close()
        if self.mydb: self.mydb.close()

if __name__ == "__main__":
    main_window = tk.Tk()
    app = PersonalFinanceGUI(main_window)
    main_window.mainloop()