import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
import calendar


class DateEntry(simpledialog.Dialog):
    """日期选择对话框"""
    def __init__(self, parent, title, initial_date=None):
        self.selected_date = initial_date or date.today()
        self.parent = parent
        super().__init__(parent, title)
    
    def body(self, master):
        # 创建日历选择器
        self.year = tk.IntVar(value=self.selected_date.year)
        self.month = tk.IntVar(value=self.selected_date.month)
        
        # 年月选择
        frame_top = ttk.Frame(master)
        frame_top.pack(pady=5)
        
        ttk.Button(frame_top, text="<", command=self.prev_month).pack(side=tk.LEFT)
        ttk.Label(frame_top, textvariable=self.month).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_top, text="年").pack(side=tk.LEFT)
        ttk.Label(frame_top, textvariable=self.year).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame_top, text="月").pack(side=tk.LEFT)
        ttk.Button(frame_top, text=">", command=self.next_month).pack(side=tk.LEFT)
        
        # 日历部分
        self.calendar_frame = ttk.Frame(master)
        self.calendar_frame.pack()
        
        self.build_calendar()
        return self.calendar_frame
    
    def build_calendar(self):
        # 清空现有日历
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # 星期标题
        days = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=i)
        
        # 获取当月第一天和最后一天
        cal = calendar.monthcalendar(self.year.get(), self.month.get())
        
        # 显示日期
        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(
                        self.calendar_frame, 
                        text=day, 
                        width=3, 
                        command=lambda d=day: self.select_date(d)
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1)
                    
                    # 高亮今天
                    today = date.today()
                    if (today.year == self.year.get() and 
                        today.month == self.month.get() and 
                        today.day == day):
                        btn.config(bg="#ffcccc")
                    
                    # 高亮选中日期
                    if (self.selected_date.year == self.year.get() and 
                        self.selected_date.month == self.month.get() and 
                        self.selected_date.day == day):
                        btn.config(bg="#ccccff")
    
    def prev_month(self):
        if self.month.get() == 1:
            self.month.set(12)
            self.year.set(self.year.get() - 1)
        else:
            self.month.set(self.month.get() - 1)
        self.build_calendar()
    
    def next_month(self):
        if self.month.get() == 12:
            self.month.set(1)
            self.year.set(self.year.get() + 1)
        else:
            self.month.set(self.month.get() + 1)
        self.build_calendar()
    
    def select_date(self, day):
        self.selected_date = date(self.year.get(), self.month.get(), day)
        self.ok()
    
    def apply(self):
        self.result = self.selected_date


class EditDialog(simpledialog.Dialog):
    """编辑待办事项对话框"""
    def __init__(self, parent, title, todo_item):
        self.todo_item = todo_item
        self.result = None
        super().__init__(parent, title)
    
    def body(self, master):
        # 任务描述
        ttk.Label(master, text="任务:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(master, width=30)
        self.text_entry.grid(row=0, column=1, pady=5, padx=(5, 0))
        self.text_entry.insert(0, self.todo_item.text)
        
        # 优先级选择
        ttk.Label(master, text="优先级:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.StringVar(value=self.todo_item.priority)
        self.priority_combo = ttk.Combobox(
            master,
            textvariable=self.priority_var,
            values=["普通", "重要", "紧急", "重要紧急"],
            state="readonly"
        )
        self.priority_combo.grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # 开始日期
        ttk.Label(master, text="开始日期:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_date_entry = ttk.Entry(master)
        self.start_date_entry.grid(row=2, column=1, pady=5, padx=(5, 0))
        start_date_str = self.todo_item.start_date.strftime("%Y-%m-%d") if self.todo_item.start_date else ""
        self.start_date_entry.insert(0, start_date_str)
        
        # 计划完成日期
        ttk.Label(master, text="计划完成日期:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.due_date_entry = ttk.Entry(master)
        self.due_date_entry.grid(row=3, column=1, pady=5, padx=(5, 0))
        due_date_str = self.todo_item.due_date.strftime("%Y-%m-%d") if self.todo_item.due_date else ""
        self.due_date_entry.insert(0, due_date_str)
        
        return self.text_entry  # 设置焦点到第一个输入框

    def apply(self):
        # 获取输入值
        text = self.text_entry.get().strip()
        priority = self.priority_var.get()
        start_date_str = self.start_date_entry.get().strip()
        due_date_str = self.due_date_entry.get().strip()
        
        if not text:
            messagebox.showwarning("警告", "请输入任务内容")
            return
        
        # 解析日期
        start_date = None
        if start_date_str:
            try:
                parts = start_date_str.split('-')
                start_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                messagebox.showerror("错误", "开始日期格式不正确，请使用 YYYY-MM-DD 格式")
                return
        
        due_date = None
        if due_date_str:
            try:
                parts = due_date_str.split('-')
                due_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                messagebox.showerror("错误", "计划完成日期格式不正确，请使用 YYYY-MM-DD 格式")
                return
        
        # 更新任务对象
        self.todo_item.text = text
        self.todo_item.priority = priority
        if start_date:
            self.todo_item.start_date = start_date
        if due_date:
            self.todo_item.due_date = due_date
        
        self.result = self.todo_item


class TodoItem:
    def __init__(self, text, start_date=None, due_date=None, completed_date=None, priority="普通"):
        self.text = text
        self.start_date = start_date or date.today()
        self.due_date = due_date
        self.completed_date = completed_date
        self.priority = priority  # "普通", "重要", "紧急", "重要紧急"
    
    def mark_completed(self):
        self.completed_date = date.today()
    
    def mark_uncompleted(self):
        self.completed_date = None


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("待办事项清单")
        self.root.geometry("1200x500")
        
        # 初始化数据
        self.todo_items = []
        self.completed_items = []
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧目录框架
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 目录标题
        ttk.Label(left_frame, text="目录", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # 待办事项按钮
        self.todo_btn = ttk.Button(
            left_frame, 
            text="待办事项", 
            command=self.show_todo,
            style="Left.TButton"
        )
        self.todo_btn.pack(fill=tk.X, pady=2)
        
        # 已完成事项按钮
        self.completed_btn = ttk.Button(
            left_frame, 
            text="已完成事项", 
            command=self.show_completed,
            style="Left.TButton"
        )
        self.completed_btn.pack(fill=tk.X, pady=2)
        
        # 右侧面板框架
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 右侧标题
        self.title_label = ttk.Label(right_frame, text="待办事项", font=("Arial", 12, "bold"))
        self.title_label.pack(anchor=tk.W)
        
        # 添加新待办事项的输入框和按钮
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 任务描述输入
        ttk.Label(input_frame, text="任务:").grid(row=0, column=0, sticky=tk.W)
        self.entry = ttk.Entry(input_frame, width=15)
        self.entry.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))
        
        # 开始日期输入
        ttk.Label(input_frame, text="开始日期:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.start_date_entry = ttk.Entry(input_frame, width=12)
        self.start_date_entry.grid(row=0, column=3, sticky=tk.EW, padx=(5, 0))
        self.start_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        
        # 计划完成日期输入
        ttk.Label(input_frame, text="计划完成日期:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.due_date_entry = ttk.Entry(input_frame, width=12)
        self.due_date_entry.grid(row=1, column=3, sticky=tk.EW, padx=(5, 0))
        
        # 为计划完成日期输入框添加点击事件
        self.due_date_entry.bind("<Button-1>", self.on_due_date_click)
        
        # 优先级选择
        ttk.Label(input_frame, text="优先级:").grid(row=1, column=0, sticky=tk.W, padx=(10, 0))
        self.priority_var = tk.StringVar(value="普通")
        self.priority_combo = ttk.Combobox(
            input_frame, 
            textvariable=self.priority_var,
            values=["普通", "重要", "紧急", "重要紧急"],
            state="readonly",
            width=10
        )
        self.priority_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # 添加按钮
        add_btn = ttk.Button(input_frame, text="添加", command=self.add_item)
        add_btn.grid(row=1, column=4, padx=(10, 0), pady=(5, 0))
        
        # 删除按钮
        delete_btn = ttk.Button(input_frame, text="删除", command=self.delete_item)
        delete_btn.grid(row=1, column=5, padx=(5, 0), pady=(5, 0))
        
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(4, weight=1)
        
        # 创建表格视图
        columns = ("序号", "任务", "优先级", "开始日期", "计划完成日期", "完成日期", "状态")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        # 定义表头
        self.tree.heading("序号", text="序号")
        self.tree.heading("任务", text="任务")
        self.tree.heading("优先级", text="优先级")
        self.tree.heading("开始日期", text="开始日期")
        self.tree.heading("计划完成日期", text="计划完成日期")
        self.tree.heading("完成日期", text="完成日期")
        self.tree.heading("状态", text="状态")
        
        # 设置列宽
        self.tree.column("序号", width=50, anchor="center")
        self.tree.column("任务", width=250, anchor="w")
        self.tree.column("优先级", width=80, anchor="center")
        self.tree.column("开始日期", width=100, anchor="center")
        self.tree.column("计划完成日期", width=100, anchor="center")
        self.tree.column("完成日期", width=100, anchor="center")
        self.tree.column("状态", width=80, anchor="center")
        
        # 表格放入框架
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.tree.bind('<Double-Button-1>', self.on_item_double_click)
        self.tree.bind('<ButtonRelease-1>', self.on_item_click)
        
        # 设置当前视图状态
        self.current_view = "todo"
        
        # 添加一些示例数据
        self.add_sample_data()
        
        # 显示待办事项
        self.show_todo()
        
    def add_sample_data(self):
        """添加一些示例数据"""
        # 创建带日期和优先级的待办事项
        item1 = TodoItem("完成项目报告", priority="重要")
        item1.due_date = date.today().replace(day=date.today().day+7)
        self.todo_items.append(item1)
        
        item2 = TodoItem("购买日用品", due_date=date.today().replace(day=date.today().day+2), priority="普通")
        self.todo_items.append(item2)
        
        # 修复日期计算，避免月份为0的情况
        today = date.today()
        if today.month == 1:
            # 如果当前是一月，设置为去年12月的同一天
            prev_month_date = today.replace(year=today.year-1, month=12)
        else:
            # 否则，设置为上个月的同一天
            prev_month_date = today.replace(month=today.month-1)
        
        item3 = TodoItem("预约医生", start_date=prev_month_date, priority="紧急")
        item3.due_date = date.today().replace(day=date.today().day+1)
        item3.completed_date = date.today()
        self.completed_items.append(item3)
    
    def add_item(self):
        """添加新的待办事项"""
        text = self.entry.get().strip()
        if not text:
            messagebox.showwarning("警告", "请输入待办事项内容")
            return
        
        # 解析开始日期
        start_date_str = self.start_date_entry.get().strip()
        start_date = None
        if start_date_str:
            try:
                start_date_parts = start_date_str.split('-')
                start_date = date(int(start_date_parts[0]), int(start_date_parts[1]), int(start_date_parts[2]))
            except (ValueError, IndexError):
                messagebox.showerror("错误", "开始日期格式不正确，请使用 YYYY-MM-DD 格式")
                return
        
        # 解析计划完成日期
        due_date_str = self.due_date_entry.get().strip()
        due_date = None
        if due_date_str:
            try:
                due_date_parts = due_date_str.split('-')
                due_date = date(int(due_date_parts[0]), int(due_date_parts[1]), int(due_date_parts[2]))
            except (ValueError, IndexError):
                messagebox.showerror("错误", "计划完成日期格式不正确，请使用 YYYY-MM-DD 格式")
                return
        
        # 获取优先级
        priority = self.priority_var.get()
        
        # 创建待办事项对象
        item = TodoItem(text, start_date, due_date, priority=priority)
        self.todo_items.append(item)
        
        # 清空输入框
        self.entry.delete(0, tk.END)
        self.due_date_entry.delete(0, tk.END)
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.priority_combo.set("普通")
        
        self.refresh_list()
    
    def delete_item(self):
        """删除待办事项"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的待办事项")
            return
        
        item_id = selection[0]
        item_values = self.tree.item(item_id, "values")
        item_idx = int(item_values[0]) - 1
        
        # 确认删除
        task_text = item_values[1]  # 获取任务文本
        confirm = messagebox.askquestion("确认删除", f"确定要删除任务 '{task_text}' 吗？\n此操作不可恢复！")
        if confirm != 'yes':
            return
        
        if self.current_view == "todo":
            self.todo_items.pop(item_idx)
        else:
            self.completed_items.pop(item_idx)
        self.refresh_list()
    
    def show_todo(self):
        """显示待办事项"""
        self.current_view = "todo"
        self.title_label.config(text="待办事项")
        self.refresh_list()
        
        # 更新按钮样式
        self.todo_btn.state(['pressed'])
        self.completed_btn.state(['!pressed'])
    
    def show_completed(self):
        """显示已完成事项"""
        self.current_view = "completed"
        self.title_label.config(text="已完成事项")
        self.refresh_list()
        
        # 更新按钮样式
        self.todo_btn.state(['!pressed'])
        self.completed_btn.state(['pressed'])
    
    def refresh_list(self):
        """刷新列表显示"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.current_view == "todo":
            items = self.todo_items
        else:
            items = self.completed_items
            
        for i, item in enumerate(items):
            # 格式化日期显示
            start_str = item.start_date.strftime("%Y-%m-%d") if item.start_date else "未设置"
            due_str = item.due_date.strftime("%Y-%m-%d") if item.due_date else "未设置"
            completed_str = item.completed_date.strftime("%Y-%m-%d") if item.completed_date and self.current_view == "completed" else ""
            
            # 确定状态
            status = "已完成" if item.completed_date else "待办"
            
            # 插入数据到表格
            self.tree.insert("", tk.END, values=(
                i+1,
                item.text,
                item.priority,
                start_str,
                due_str,
                completed_str,
                status
            ), tags=(f"item_{i}",))
    
    def on_due_date_click(self, event):
        """处理计划完成日期输入框的点击事件"""
        # 获取当前输入框的日期值
        due_date_str = self.due_date_entry.get().strip()
        current_date = None
        
        if due_date_str:
            try:
                parts = due_date_str.split('-')
                current_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                current_date = date.today()
        else:
            current_date = date.today()
        
        # 打开日期选择器
        dialog = DateEntry(self.root, "选择计划完成日期", current_date)
        if dialog.result:
            # 将选择的日期填入输入框
            formatted_date = dialog.result.strftime("%Y-%m-%d")
            self.due_date_entry.delete(0, tk.END)
            self.due_date_entry.insert(0, formatted_date)
    
    def on_item_click(self, event):
        """处理表格项点击事件"""
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        
        # 获取当前选择项
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        item_values = self.tree.item(item_id, "values")
        item_idx = int(item_values[0]) - 1
        
        # 检查是否点击了"计划完成日期"列（第5列，索引为5）
        if region == "cell" and column == "#5":
            # 根据当前视图获取对应的项目
            if self.current_view == "todo":
                todo_item = self.todo_items[item_idx]
            else:
                todo_item = self.completed_items[item_idx]
            
            # 打开日期选择器
            dialog = DateEntry(self.root, "选择计划完成日期", todo_item.due_date)
            if dialog.result:
                todo_item.due_date = dialog.result
                self.refresh_list()
        
        # 检查是否点击了"完成日期"列（第6列，索引为6）且在已完成列表中
        elif region == "cell" and column == "#6" and self.current_view == "completed":
            completed_item = self.completed_items[item_idx]
            
            # 打开日期选择器
            dialog = DateEntry(self.root, "选择完成日期", completed_item.completed_date)
            if dialog.result:
                completed_item.completed_date = dialog.result
                self.refresh_list()
        
        # 检查是否点击了"任务"列（第2列，索引为2），触发编辑
        elif region == "cell" and column == "#2":
            self.edit_item(item_id)
        
        # 检查是否点击了"优先级"列（第3列，索引为3），触发编辑
        elif region == "cell" and column == "#3":
            self.edit_item(item_id)

    def edit_item(self, item_id):
        """编辑待办事项"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        item_values = self.tree.item(item_id, "values")
        item_idx = int(item_values[0]) - 1
        
        # 根据当前视图获取对应的项目
        if self.current_view == "todo":
            todo_item = self.todo_items[item_idx]
        else:
            todo_item = self.completed_items[item_idx]
        
        # 创建编辑对话框
        dialog = EditDialog(self.root, "编辑待办事项", todo_item)
        if dialog.result:
            # 更新数据并刷新列表
            self.refresh_list()

    def on_item_double_click(self, event):
        """处理列表项双击事件，切换任务状态"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        selection = self.tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        item_values = self.tree.item(item_id, "values")
        item_idx = int(item_values[0]) - 1
        
        if self.current_view == "todo":
            # 从待办事项移到已完成事项
            item = self.todo_items.pop(item_idx)
            item.mark_completed()  # 设置完成日期
            self.completed_items.append(item)
            self.refresh_list()
        elif self.current_view == "completed":
            # 从已完成事项移到待办事项
            item = self.completed_items.pop(item_idx)
            item.mark_uncompleted()  # 清除完成日期
            self.todo_items.append(item)
            self.refresh_list()


def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":


    main()


