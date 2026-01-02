import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
from datetime import datetime
import uuid

class KnowledgeBaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("知识库笔记本")
        self.geometry("800x600")
        self.data = {}
        self.current_note_id = None
        self.drag_item = None
        self.load_data()
        self.create_widgets()
        self.populate_tree()

    def load_data(self):
        if os.path.exists('knowledge_base.json'):
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "notes": {},
                "directories": {
                    "root": {
                        "id": "root",
                        "name": "根目录",
                        "parent_id": None,
                        "order": 0,
                        "children": [],
                        "notes": []
                    }
                }
            }

    def save_data(self):
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def create_widgets(self):
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 左侧树状目录
        self.tree_frame = tk.Frame(self.paned)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.heading('#0', text='目录/笔记')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Button-3>', self.show_tree_menu)
        self.tree.bind('<ButtonPress-1>', self.on_drag_start)
        self.tree.bind('<B1-Motion>', self.on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self.on_drag_release)

        # 右键菜单
        self.tree_menu = tk.Menu(self, tearoff=0)
        self.tree_menu.add_command(label="添加目录", command=self.add_directory)
        self.tree_menu.add_command(label="添加笔记", command=self.add_note)
        self.tree_menu.add_command(label="删除", command=self.delete_item)
        self.tree_menu.add_command(label="重命名", command=self.rename_item)

        self.paned.add(self.tree_frame, minsize=200)

        # 右侧文本编辑器
        self.text_frame = tk.Frame(self.paned)
        self.text = tk.Text(self.text_frame, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # 为文本框绑定内容变更事件
        self.text.bind('<KeyRelease>', self.on_text_change)
        self.text.bind('<ButtonRelease-1>', self.on_text_change)
        self.text.bind('<<Modified>>', self.on_text_modified)
        
        # 添加一个变量来跟踪是否需要保存
        self.text_modified = False
        
        self.save_button = tk.Button(self.text_frame, text="保存", command=self.save_note)
        self.save_button.pack(side=tk.BOTTOM)

        self.paned.add(self.text_frame, minsize=400)

    def populate_tree(self):
        # 记录展开状态，使用目录ID
        expanded_dir_ids = set()
        for item in self.tree.get_children():
            self.get_expanded_dir_ids(item, expanded_dir_ids)
        
        self.tree.delete(*self.tree.get_children())
        
        def add_items(parent_id, tree_parent):
            dir_data = self.data['directories'][parent_id]
            tree_id = self.tree.insert(tree_parent, 'end', text=dir_data['name'], values=(parent_id, 'dir'))
            for note_id in dir_data['notes']:
                if note_id in self.data['notes']:
                    note = self.data['notes'][note_id]
                    self.tree.insert(tree_id, 'end', text=note['title'], values=(note_id, 'note'))
            for child_id in dir_data['children']:
                add_items(child_id, tree_id)
        add_items('root', '')
        
        # 恢复展开状态，通过目录ID查找并展开对应节点
        self.restore_expanded_by_dir_id(expanded_dir_ids)
        
        # 确保根目录始终展开
        root_items = self.tree.get_children('')
        if root_items:
            self.tree.item(root_items[0], open=True)

    def get_expanded_dir_ids(self, item, expanded_dir_ids):
        """递归获取所有展开的目录ID"""
        item_values = self.tree.item(item, 'values')
        if item_values and len(item_values) > 0:
            # 如果这是一个目录项并且是展开的，记录其ID
            if item_values[1] == 'dir' and self.tree.item(item, 'open'):
                dir_id = item_values[0]
                expanded_dir_ids.add(dir_id)
        
        for child in self.tree.get_children(item):
            self.get_expanded_dir_ids(child, expanded_dir_ids)

    def restore_expanded_by_dir_id(self, expanded_dir_ids):
        """根据目录ID恢复展开状态"""
        def traverse_and_expand(parent):
            for child in self.tree.get_children(parent):
                child_values = self.tree.item(child, 'values')
                if child_values and len(child_values) > 0:
                    # 如果这是一个目录项，检查是否需要展开
                    if child_values[1] == 'dir':
                        dir_id = child_values[0]
                        if dir_id in expanded_dir_ids:
                            self.tree.item(child, open=True)
                
                # 递归处理子节点
                traverse_and_expand(child)
        
        traverse_and_expand('')

    def on_text_change(self, event=None):
        """处理文本变更事件"""
        # 检查文本是否真的被修改
        if self.current_note_id:
            # 设置修改标志
            self.text_modified = True
            # 更改保存按钮的文本以提示用户
            self.save_button.config(text="保存*")

    def on_text_modified(self, event=None):
        """处理文本修改事件"""
        # 这个事件会在文本被修改时触发
        self.on_text_change()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            item_id, item_type = self.tree.item(item, 'values')
            if item_type == 'note':
                # 如果之前有编辑过的笔记且未保存，提示用户保存
                if self.current_note_id and self.text_modified:
                    self.ask_to_save_current_note()
                
                self.current_note_id = item_id
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, self.data['notes'][item_id]['content'])
                
                # 重置修改标志
                self.text_modified = False
                self.save_button.config(text="保存")
            else:
                # 如果切换到目录，检查是否有编辑过的笔记未保存
                if self.current_note_id and self.text_modified:
                    self.ask_to_save_current_note()
                    
                self.current_note_id = None
                self.text.delete(1.0, tk.END)

    def ask_to_save_current_note(self):
        """询问用户是否保存当前笔记"""
        if self.current_note_id and self.text_modified:
            result = messagebox.askyesnocancel("保存更改", "笔记已修改，是否保存？")
            if result is True:  # 用户选择保存
                self.save_current_note_content()
            elif result is False:  # 用户选择不保存
                self.text_modified = False
                self.save_button.config(text="保存")
            # 如果选择取消，则什么都不做

    def save_current_note_content(self):
        """保存当前笔记内容"""
        if self.current_note_id:
            content = self.text.get(1.0, tk.END).strip()
            self.data['notes'][self.current_note_id]['content'] = content
            self.data['notes'][self.current_note_id]['modified_time'] = datetime.now().isoformat()
            self.save_data()
            self.text_modified = False
            self.save_button.config(text="保存")
            messagebox.showinfo("保存", "笔记已保存")

    def save_note(self):
        """保存当前编辑的文件"""
        if self.current_note_id:
            self.save_current_note_content()
            messagebox.showinfo("保存", "笔记已保存")
        else:
            messagebox.showwarning("警告", "没有选中任何笔记")

    def show_tree_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def add_directory(self):
        selected = self.tree.selection()
        if selected:
            parent_id = self.tree.item(selected[0], 'values')[0]
            name = simpledialog.askstring("添加目录", "目录名称:")
            if name:
                dir_id = str(uuid.uuid4())
                self.data['directories'][dir_id] = {
                    "id": dir_id,
                    "name": name,
                    "parent_id": parent_id,
                    "order": len(self.data['directories'][parent_id]['children']),
                    "children": [],
                    "notes": []
                }
                self.data['directories'][parent_id]['children'].append(dir_id)
                self.save_data()
                self.populate_tree()

    def add_note(self):
        selected = self.tree.selection()
        if selected:
            parent_id = self.tree.item(selected[0], 'values')[0]
            title = simpledialog.askstring("添加笔记", "笔记标题:")
            if title:
                note_id = str(uuid.uuid4())
                self.data['notes'][note_id] = {
                    "id": note_id,
                    "title": title,
                    "content": "",
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat(),
                    "versions": []
                }
                self.data['directories'][parent_id]['notes'].append(note_id)
                self.save_data()
                self.populate_tree()

    def delete_item(self):
        selected = self.tree.selection()
        if selected:
            item_id, item_type = self.tree.item(selected[0], 'values')
            if messagebox.askyesno("删除", "确定删除吗？"):
                if item_type == 'dir':
                    self.delete_directory(item_id)
                elif item_type == 'note':
                    self.delete_note(item_id)
                self.save_data()
                self.populate_tree()

    def delete_directory(self, dir_id):
        # 递归删除子目录和笔记
        for child_id in self.data['directories'][dir_id]['children'][:]:
            self.delete_directory(child_id)
        for note_id in self.data['directories'][dir_id]['notes'][:]:
            del self.data['notes'][note_id]
        parent_id = self.data['directories'][dir_id]['parent_id']
        if parent_id:
            self.data['directories'][parent_id]['children'].remove(dir_id)
        del self.data['directories'][dir_id]

    def delete_note(self, note_id):
        del self.data['notes'][note_id]
        # 从目录中移除
        for dir_data in self.data['directories'].values():
            if note_id in dir_data['notes']:
                dir_data['notes'].remove(note_id)
                break

    def rename_item(self):
        selected = self.tree.selection()
        if selected:
            item_id, item_type = self.tree.item(selected[0], 'values')
            if item_type == 'dir':
                new_name = simpledialog.askstring("重命名目录", "新名称:", initialvalue=self.data['directories'][item_id]['name'])
                if new_name:
                    self.data['directories'][item_id]['name'] = new_name
            elif item_type == 'note':
                new_title = simpledialog.askstring("重命名笔记", "新标题:", initialvalue=self.data['notes'][item_id]['title'])
                if new_title:
                    self.data['notes'][item_id]['title'] = new_title
            self.save_data()
            self.populate_tree()

    def on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.drag_item = item

    def on_drag_motion(self, event):
        # 可以添加视觉反馈
        pass

    def on_drag_release(self, event):
        if self.drag_item:
            target = self.tree.identify_row(event.y)
            if target and target != self.drag_item:
                self.move_item(self.drag_item, target)
            self.drag_item = None

    def move_item(self, item, target):
        item_id, item_type = self.tree.item(item, 'values')
        target_id, target_type = self.tree.item(target, 'values')
        if item_type == 'dir' and target_type == 'dir' and item_id != target_id:
            # 移动目录
            old_parent = self.data['directories'][item_id]['parent_id']
            if old_parent:
                self.data['directories'][old_parent]['children'].remove(item_id)
            self.data['directories'][item_id]['parent_id'] = target_id
            self.data['directories'][target_id]['children'].append(item_id)
            self.save_data()
            self.populate_tree()
        elif item_type == 'note' and target_type == 'dir':
            # 移动笔记到目录
            old_parent = None
            for dir_data in self.data['directories'].values():
                if item_id in dir_data['notes']:
                    old_parent = dir_data['id']
                    dir_data['notes'].remove(item_id)
                    break
            self.data['directories'][target_id]['notes'].append(item_id)
            self.save_data()
            self.populate_tree()

if __name__ == "__main__":
    app = KnowledgeBaseApp()
    app.mainloop()