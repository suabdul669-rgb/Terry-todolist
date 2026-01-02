import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import base64

class DocMenu:
    def __init__(self, root):
        self.root = root
        self.root.title('文档菜单')
        self.root.geometry('1000x600')
        
        # 创建主分割框架
        self.main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧目录树框架
        left_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(left_frame, weight=1)
        
        # 目录树标题
        ttk.Label(left_frame, text='文件夹结构', font=('Arial', 10, 'bold')).pack(anchor=tk.NW, pady=(0, 5))
        
        # 创建目录树
        self.tree = ttk.Treeview(left_frame, columns=('path',), show='tree', height=20)
        tree_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧文本编辑区域
        right_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(right_frame, weight=3)
        
        # 文本编辑区域
        self.text_edit = tk.Text(right_frame, wrap=tk.WORD)
        text_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.text_edit.yview)
        self.text_edit.configure(yscrollcommand=text_scrollbar.set)
        
        self.text_edit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建菜单栏
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='文件', menu=file_menu)
        
        # 添加菜单项
        file_menu.add_command(label='选择文件夹', command=self.browse_folder)
        file_menu.add_command(label='新建文件', command=self.new_file, accelerator='Ctrl+N')
        file_menu.add_command(label='保存', command=self.save_current_file, accelerator='Ctrl+S')
        file_menu.add_command(label='粘贴图片', command=self.paste_image, accelerator='Ctrl+V')
        file_menu.add_separator()
        file_menu.add_command(label='删除文件', command=self.delete_file, accelerator='Delete')
        file_menu.add_command(label='删除文件夹', command=self.delete_folder)
        file_menu.add_command(label='新建文件夹', command=self.new_folder)
        
        # 添加视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='视图', menu=view_menu)
        view_menu.add_command(label='展开所有', command=self.expand_all)
        view_menu.add_command(label='折叠所有', command=self.collapse_all)
        
        # 添加工具栏
        toolbar = ttk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        ttk.Button(toolbar, text='展开目录', command=self.expand_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='折叠目录', command=self.collapse_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='新建文件夹', command=self.new_folder).pack(side=tk.LEFT, padx=2)
        
        # 初始化变量
        self.current_folder = ""
        self.current_file_path = ""
        
        # 绑定事件
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-s>', lambda e: self.save_current_file())
        self.root.bind('<Delete>', lambda e: self.delete_file())
        self.root.bind('<Control-v>', lambda e: self.paste_image())
        
        # 添加右键菜单
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # 初始化右键菜单
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label='新建文件夹', command=self.new_folder_from_context)
        self.context_menu.add_command(label='删除文件夹', command=self.delete_folder_from_context)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='新建文件', command=self.new_file_from_context)
        self.context_menu.add_command(label='删除文件', command=self.delete_file_from_context)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选中被右键点击的项目
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def collapse_all(self):
        """折叠所有节点，但保留根节点展开"""
        # 获取所有根节点
        root_items = self.tree.get_children()
        # 只折叠根节点的子节点，不折叠根节点本身
        for root_item in root_items:
            self._collapse_recursive(root_item)

    def _collapse_recursive(self, item):
        """递归折叠子节点"""
        self.tree.item(item, open=False)
        for child in self.tree.get_children(item):
            self._collapse_recursive(child)

    def expand_all(self):
        """展开所有节点"""
        for item in self.tree.get_children():
            self._expand_recursive(item)

    def _expand_recursive(self, item):
        """递归展开子节点"""
        self.tree.item(item, open=True)
        for child in self.tree.get_children(item):
            self._expand_recursive(child)

    def browse_folder(self):
        """打开文件夹选择对话框"""
        folder_path = filedialog.askdirectory(title='选择文件夹')
        if folder_path:
            self.current_folder = folder_path
            self.load_directory_tree(folder_path)

    def load_directory_tree(self, folder_path):
        """加载目录树"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加根目录
        root_name = os.path.basename(folder_path)
        root_item = self.tree.insert('', 'end', text=root_name, values=[folder_path])
        self.tree.item(root_item, open=True)
        
        self.add_directory_items(root_item, folder_path)
        
        # 展开所有项
        self.expand_all()

    def add_directory_items(self, parent_item, path):
        """递归添加目录项"""
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                # 如果是目录，添加目录节点
                if os.path.isdir(item_path):
                    dir_item = self.tree.insert(parent_item, 'end', text=item, values=[item_path])
                    self.add_directory_items(dir_item, item_path)  # 递归添加子项
                
                # 如果是txt、rtf或xlsx文件，添加文件节点
                elif item.lower().endswith(('.txt', '.rtf', '.xlsx', '.bas')):
                    file_item = self.tree.insert(parent_item, 'end', text=item, values=[item_path])
        except PermissionError:
            pass  # 忽略无权限访问的目录

    def on_tree_select(self, event):
        """处理目录树选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_path = self.tree.item(item_id, 'values')[0]
        
        # 检查是否为支持的文件类型
        if os.path.isfile(item_path) and item_path.lower().endswith(('.txt', '.rtf', '.xlsx', '.bas')):
            self.current_file_path = item_path  # 保存当前文件路径
            self.show_file_content(item_path)
        else:
            # 如果是目录，不显示内容
            self.text_edit.delete(1.0, tk.END)
            self.current_file_path = ""  # 清空当前文件路径

    def show_file_content(self, file_path):
        """显示文件内容，支持文本、RTF和Excel格式"""
        try:
            if file_path.lower().endswith('.rtf'):
                # 对于RTF文件，使用普通文本方式显示
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.delete(1.0, tk.END)
                    self.text_edit.insert(tk.END, content)
            elif file_path.lower().endswith('.xlsx'):  # 添加对Excel文件的支持
                # 对于Excel文件，将其转换为文本表格显示
                df = pd.read_excel(file_path, sheet_name=0)  # 读取第一个工作表
                content = df.to_string(index=False)
                self.text_edit.delete(1.0, tk.END)
                self.text_edit.insert(tk.END, content)
            elif file_path.lower().endswith('.bas'):  # 添加对bas文件的支持
                # 对于bas文件，按文本方式显示
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.delete(1.0, tk.END)
                    self.text_edit.insert(tk.END, content)
            else:
                # 对于txt文件，普通文本显示
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.delete(1.0, tk.END)
                    self.text_edit.insert(tk.END, content)
        except Exception as e:
            self.text_edit.delete(1.0, tk.END)
            self.text_edit.insert(tk.END, f"无法读取文件: {str(e)}")

    def new_file(self):
        """新建文件，仅支持TXT格式"""
        if not self.current_folder:
            messagebox.showwarning("警告", "请先选择一个文件夹")
            return

        # 获取当前选中的目录
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            selected_item_path = self.tree.item(item_id, 'values')[0]
            # 如果选中的是文件，则使用其父目录
            if os.path.isfile(selected_item_path):
                parent_dir = os.path.dirname(selected_item_path)
            else:
                parent_dir = selected_item_path
        else:
            parent_dir = self.current_folder

        # 创建新文件对话框
        file_path = filedialog.asksaveasfilename(
            title='新建文件',
            initialdir=parent_dir,
            defaultextension='.txt',
            filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')]
        )
        
        if file_path:
            # 创建空文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
        
            # 更新目录树
            self.update_directory_tree(parent_dir)
            
            # 选中并打开新文件
            self.current_file_path = file_path
            self.show_file_content(file_path)
            self.select_item_by_path(file_path)
            self.text_edit.focus()

    def new_folder(self):
        """创建新文件夹"""
        if not self.current_folder:
            messagebox.showwarning("警告", "请先选择一个文件夹")
            return

        # 获取当前选中的目录
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            selected_item_path = self.tree.item(item_id, 'values')[0]
            # 如果选中的是文件，则使用其父目录
            if os.path.isfile(selected_item_path):
                parent_dir = os.path.dirname(selected_item_path)
            else:
                parent_dir = selected_item_path
        else:
            parent_dir = self.current_folder

        # 获取新文件夹名称
        folder_name = simpledialog.askstring("新建文件夹", "请输入文件夹名称:")
        
        if folder_name:
            new_folder_path = os.path.join(parent_dir, folder_name)
            try:
                os.makedirs(new_folder_path)
                # 更新目录树
                self.update_directory_tree(parent_dir)
                
                # 选中并定位到新创建的文件夹
                self.select_item_by_path(new_folder_path)
            except Exception as e:
                messagebox.showerror("错误", f"创建文件夹失败: {str(e)}")

    def update_directory_tree(self, parent_path):
        """更新目录树中的特定父路径"""
        # 找到父路径对应的树形项目
        parent_item = self.find_tree_item_by_path(parent_path)
        if parent_item:
            # 清除现有的子项
            self.tree.delete(*self.tree.get_children(parent_item))
            # 添加新的子项
            self.add_directory_items(parent_item, parent_path)
            # 展开父项
            self.tree.item(parent_item, open=True)
        else:
            # 如果找不到父项，重新加载整个目录树
            self.load_directory_tree(self.current_folder)

    def find_tree_item_by_path(self, path):
        """根据路径查找树形项目"""
        def search_item(parent, target_path):
            for child in self.tree.get_children(parent):
                item_path = self.tree.item(child, 'values')[0]
                if item_path == target_path:
                    return child
                result = search_item(child, target_path)
                if result:
                    return result
            return None

        # 搜索所有顶级项目
        for item in self.tree.get_children():
            item_path = self.tree.item(item, 'values')[0]
            if item_path == path:
                return item
            result = search_item(item, path)
            if result:
                return result
        return None

    def save_current_file(self):
        """保存当前编辑的文件"""
        if self.current_file_path:
            try:
                if self.current_file_path.lower().endswith('.xlsx'):  # 添加对Excel文件的保存支持
                    # 对于Excel文件，将文本内容转换回DataFrame并保存
                    try:
                        content = self.text_edit.get(1.0, tk.END)
                        # 简单的文本到DataFrame转换
                        lines = content.strip().split('\n')
                        if lines:
                            # 假设第一行是列名
                            headers = lines[0].split('\t')  # 使用制表符分割
                            data_rows = [line.split('\t') for line in lines[1:]]
                            df = pd.DataFrame(data_rows, columns=headers)
                            df.to_excel(self.current_file_path, index=False)
                            messagebox.showinfo("保存成功", "Excel文件已保存成功！")
                        else:
                            # 如果没有内容，创建空的Excel文件
                            df = pd.DataFrame()
                            df.to_excel(self.current_file_path, index=False)
                    except Exception as e:
                        messagebox.showerror("保存错误", f"无法保存Excel文件: {str(e)}")
                else:
                    # 对于txt文件，只保存纯文本内容
                    content = self.text_edit.get(1.0, tk.END)
                    with open(self.current_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                messagebox.showinfo("保存成功", f"文件已保存: {self.current_file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法保存文件: {str(e)}")
        else:
            # 如果没有当前文件路径，则提示用户先选择文件
            messagebox.showwarning("警告", "请先选择一个文件进行编辑")

    def delete_file(self):
        """删除选中的文件"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的文件")
            return
        
        item_id = selection[0]
        item_path = self.tree.item(item_id, 'values')[0]
        item_name = self.tree.item(item_id, 'text')
        
        if os.path.isfile(item_path):
            reply = messagebox.askquestion("确认删除", f"确定要删除文件 '{item_name}' 吗？\n此操作不可恢复！")
            if reply == 'yes':
                try:
                    os.remove(item_path)
                    # 从目录树中移除项目
                    self.tree.delete(item_id)
                    # 清空编辑区域
                    if self.current_file_path == item_path:
                        self.text_edit.delete(1.0, tk.END)
                        self.current_file_path = ""
                except Exception as e:
                    messagebox.showerror("错误", f"删除文件失败: {str(e)}")
        else:
            messagebox.showinfo("提示", "请选择一个文件进行删除")

    def delete_folder(self):
        """删除选中的文件夹"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的文件夹")
            return
        
        item_id = selection[0]
        item_path = self.tree.item(item_id, 'values')[0]
        item_name = self.tree.item(item_id, 'text')
        
        if os.path.isdir(item_path):
            reply = messagebox.askquestion("确认删除", f"确定要删除文件夹 '{item_name}' 吗？\n此操作将删除文件夹内所有内容，且不可恢复！")
            if reply == 'yes':
                try:
                    import shutil
                    shutil.rmtree(item_path)
                    # 从目录树中移除项目
                    self.tree.delete(item_id)
                    # 清空编辑区域
                    if self.current_file_path and self.current_file_path.startswith(item_path):
                        self.text_edit.delete(1.0, tk.END)
                        self.current_file_path = ""
                except Exception as e:
                    messagebox.showerror("错误", f"删除文件夹失败: {str(e)}")
        else:
            messagebox.showinfo("提示", "请选择一个文件夹进行删除")

    def select_item_by_path(self, path):
        """根据路径选中树形控件中的项目"""
        def find_path(parent, target_path):
            for child in self.tree.get_children(parent):
                child_path = self.tree.item(child, 'values')[0]
                
                # 如果当前项目路径与目标路径匹配
                if target_path == child_path:
                    self.tree.selection_set(child)
                    self.tree.see(child)  # 确保项目可见
                    return child
                # 如果目标路径在当前项目路径下，需要展开当前项目
                elif target_path.startswith(child_path + os.sep):
                    self.tree.item(parent, open=True)
                    result = find_path(child, target_path)
                    if result:
                        return result
            return None

        # 搜索所有顶级项目
        for item in self.tree.get_children():
            item_path = self.tree.item(item, 'values')[0]
            # 只有当目标路径在根项目下时才展开根项目
            if self.current_folder and (path == self.current_folder or path.startswith(self.current_folder + os.sep)):
                self.tree.item(item, open=True)
            result = find_path(item, path)
            if result:
                self.tree.selection_set(result)
                self.tree.see(result)
                return result
        return None
    
    def paste_image(self):
        """从剪贴板粘贴图片到编辑器 - tkinter版本不直接支持图片插入"""
        # tkinter的Text组件不直接支持图片插入，提示用户
        messagebox.showinfo("文件格式提醒", 
                           "tkinter的文本编辑器不支持直接插入图片。" +
                           "如需处理带图片的文档，请使用专业的文档编辑软件。")

    # 以下是右键菜单相关的功能
    def new_folder_from_context(self):
        """通过右键菜单创建新文件夹"""
        self.new_folder()

    def delete_folder_from_context(self):
        """通过右键菜单删除文件夹"""
        self.delete_folder()

    def new_file_from_context(self):
        """通过右键菜单新建文件"""
        self.new_file()

    def delete_file_from_context(self):
        """通过右键菜单删除文件"""
        self.delete_file()


def main():
    root = tk.Tk()
    app = DocMenu(root)
    
    # 获取exe文件所在目录
    if getattr(sys, 'frozen', False):  # 检查是否为打包后的exe文件
        app_dir = os.path.dirname(sys.executable)
    else:  # 开发环境中
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建CodeBaseVBA目录路径
    code_base_vba_dir = os.path.join(app_dir, "CodeBaseVBA")
    
    # 检查CodeBaseVBA目录是否存在，如果存在则自动加载
    if os.path.exists(code_base_vba_dir) and os.path.isdir(code_base_vba_dir):
        app.current_folder = code_base_vba_dir
        app.load_directory_tree(code_base_vba_dir)
    
    root.mainloop()


if __name__ == "__main__":
    main()