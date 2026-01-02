import json
import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from typing import Dict, List, Optional


class NoteVersion:
    """笔记版本类，用于存储笔记的历史版本"""
    def __init__(self, title: str, content: str, version_time: datetime.datetime = None):
        self.title = title
        self.content = content
        self.version_time = version_time or datetime.datetime.now()
    
    def to_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'version_time': self.version_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        version_time = datetime.datetime.fromisoformat(data['version_time'])
        return cls(data['title'], data['content'], version_time)


class Note:
    """笔记类，表示单个笔记"""
    def __init__(self, note_id: str, title: str, content: str = "", 
                 created_time: Optional[datetime.datetime] = None, 
                 modified_time: Optional[datetime.datetime] = None):
        self.id = note_id
        self.title = title
        self.content = content
        self.created_time = created_time or datetime.datetime.now()
        self.modified_time = modified_time or datetime.datetime.now()
        self.versions: List[NoteVersion] = []  # 版本历史
    
    def update_content(self, title: str, content: str, auto_save_version: bool = True):
        """更新笔记内容"""
        # 如果需要保存版本快照，则先保存当前版本
        if auto_save_version and (self.title != title or self.content != content):
            self.save_version_snapshot()
        
        self.title = title
        self.content = content
        self.modified_time = datetime.datetime.now()
    
    def save_version_snapshot(self):
        """手动保存版本快照"""
        self.versions.append(NoteVersion(self.title, self.content))
    
    def get_versions(self) -> List[NoteVersion]:
        """获取所有版本"""
        return self.versions[:]
    
    def restore_version(self, version_idx: int) -> bool:
        """恢复到指定版本"""
        if 0 <= version_idx < len(self.versions):
            version = self.versions[version_idx]
            self.title = version.title
            self.content = version.content
            self.modified_time = datetime.datetime.now()
            return True
        return False
    
    def to_dict(self):
        """将笔记对象转换为字典格式，便于存储"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_time': self.created_time.isoformat(),
            'modified_time': self.modified_time.isoformat(),
            'versions': [v.to_dict() for v in self.versions]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典数据创建笔记对象"""
        note = cls(
            note_id=data['id'],
            title=data['title'],
            content=data.get('content', ''),
            created_time=datetime.datetime.fromisoformat(data['created_time']) if data.get('created_time') else None,
            modified_time=datetime.datetime.fromisoformat(data['modified_time']) if data.get('modified_time') else None
        )
        
        # 加载版本历史
        for version_data in data.get('versions', []):
            note.versions.append(NoteVersion.from_dict(version_data))
        
        return note


class Directory:
    """目录类，表示笔记本中的目录结构"""
    def __init__(self, dir_id: str, name: str, parent_id: Optional[str] = None, order: int = 0):
        self.id = dir_id
        self.name = name
        self.parent_id = parent_id
        self.order = order  # 用于调整目录顺序
        self.children: List[str] = []  # 子目录ID列表
        self.notes: List[str] = []     # 笔记ID列表
    
    def add_child(self, child_id: str, order: int = None):
        """添加子目录，可以指定顺序"""
        if child_id not in self.children:
            self.children.append(child_id)
            if order is not None:
                self.set_child_order(child_id, order)
    
    def remove_child(self, child_id: str):
        """移除子目录"""
        if child_id in self.children:
            self.children.remove(child_id)
    
    def set_child_order(self, child_id: str, order: int):
        """设置子目录的顺序"""
        if child_id in self.children:
            # 将指定子目录移动到指定位置
            self.children.remove(child_id)
            if order >= len(self.children):
                self.children.append(child_id)
            else:
                self.children.insert(order, child_id)
    
    def reorder_children(self, new_order: List[str]):
        """重新排序子目录"""
        # 验证新顺序中的所有ID都在当前子目录中
        if set(new_order) == set(self.children):
            self.children = new_order
    
    def add_note(self, note_id: str):
        """添加笔记到目录"""
        if note_id not in self.notes:
            self.notes.append(note_id)
    
    def remove_note(self, note_id: str):
        """从目录移除笔记"""
        if note_id in self.notes:
            self.notes.remove(note_id)
    
    def to_dict(self):
        """将目录对象转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'order': self.order,
            'children': self.children,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典数据创建目录对象"""
        directory = cls(
            dir_id=data['id'],
            name=data['name'],
            parent_id=data.get('parent_id'),
            order=data.get('order', 0)
        )
        directory.children = data.get('children', [])
        directory.notes = data.get('notes', [])
        return directory


class KnowledgeBaseNotebook:
    """知识库笔记本主类"""
    def __init__(self, storage_file: str = "knowledge_base.json"):
        self.storage_file = storage_file
        self.notes: Dict[str, Note] = {}
        self.directories: Dict[str, Directory] = {}
        self.root_dir_id = "root"
        
        # 初始化根目录
        if self.root_dir_id not in self.directories:
            root_dir = Directory(self.root_dir_id, "根目录")
            self.directories[self.root_dir_id] = root_dir
        
        # 尝试从文件加载数据
        self.load_from_file()
    
    def create_note(self, title: str, content: str = "", dir_id: str = None) -> Note:
        """创建新笔记"""
        import uuid
        note_id = str(uuid.uuid4())
        note = Note(note_id, title, content)
        self.notes[note_id] = note
        
        # 如果指定了目录，则将笔记添加到目录中
        if dir_id and dir_id in self.directories:
            self.directories[dir_id].add_note(note_id)
        else:
            # 默认添加到根目录
            self.directories[self.root_dir_id].add_note(note_id)
        
        self.save_to_file()
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """获取指定ID的笔记"""
        return self.notes.get(note_id)
    
    def update_note(self, note_id: str, title: str, content: str, auto_save_version: bool = True) -> bool:
        """更新笔记"""
        if note_id in self.notes:
            self.notes[note_id].update_content(title, content, auto_save_version)
            self.save_to_file()
            return True
        return False
    
    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        if note_id in self.notes:
            note = self.notes[note_id]
            
            # 从所有目录中移除该笔记的引用
            for directory in self.directories.values():
                if note_id in directory.notes:
                    directory.remove_note(note_id)
            
            del self.notes[note_id]
            self.save_to_file()
            return True
        return False
    
    def list_notes_in_directory(self, dir_id: str) -> List[Note]:
        """列出指定目录中的所有笔记"""
        if dir_id in self.directories:
            dir_notes = []
            for note_id in self.directories[dir_id].notes:
                if note_id in self.notes:
                    dir_notes.append(self.notes[note_id])
            # 按修改时间排序
            dir_notes.sort(key=lambda x: x.modified_time, reverse=True)
            return dir_notes
        return []
    
    def create_directory(self, name: str, parent_id: str = None) -> Directory:
        """创建新目录"""
        import uuid
        dir_id = str(uuid.uuid4())
        
        # 如果没有指定父目录或父目录不存在，使用根目录
        if not parent_id or parent_id not in self.directories:
            parent_id = self.root_dir_id
        
        # 确定新目录的顺序
        order = len(self.directories[parent_id].children)
        
        directory = Directory(dir_id, name, parent_id, order)
        self.directories[dir_id] = directory
        
        # 将新目录添加到父目录的子目录列表中
        if parent_id in self.directories:
            self.directories[parent_id].add_child(dir_id, order)
        
        self.save_to_file()
        return directory
    
    def rename_directory(self, dir_id: str, new_name: str) -> bool:
        """重命名目录"""
        if dir_id in self.directories:
            self.directories[dir_id].name = new_name
            self.save_to_file()
            return True
        return False
    
    def move_directory(self, dir_id: str, new_parent_id: str) -> bool:
        """移动目录到另一个父目录下"""
        if dir_id not in self.directories or new_parent_id not in self.directories:
            return False
        
        directory = self.directories[dir_id]
        
        # 从当前父目录移除
        if directory.parent_id and directory.parent_id in self.directories:
            self.directories[directory.parent_id].remove_child(dir_id)
        
        # 设置新的父目录
        directory.parent_id = new_parent_id
        
        # 添加到新父目录，设置顺序为最后
        new_order = len(self.directories[new_parent_id].children)
        self.directories[new_parent_id].add_child(dir_id, new_order)
        
        self.save_to_file()
        return True
    
    def reorder_directories(self, parent_id: str, new_order: List[str]) -> bool:
        """调整子目录顺序"""
        if parent_id in self.directories:
            self.directories[parent_id].reorder_children(new_order)
            self.save_to_file()
            return True
        return False
    
    def delete_directory(self, dir_id: str, delete_notes: bool = False) -> bool:
        """删除目录（可以选择是否同时删除目录中的笔记）"""
        if dir_id not in self.directories or dir_id == self.root_dir_id:
            return False
        
        directory = self.directories[dir_id]
        
        # 如果删除目录中的笔记
        if delete_notes:
            for note_id in directory.notes[:]:  # 使用切片复制避免在迭代中修改列表
                self.delete_note(note_id)
        else:
            # 将笔记移动到根目录
            for note_id in directory.notes:
                if note_id in self.notes:
                    self.directories[self.root_dir_id].add_note(note_id)
        
        # 递归删除所有子目录
        for child_id in directory.children[:]:
            self.delete_directory(child_id, delete_notes)
        
        # 从父目录中移除此目录的引用
        if directory.parent_id and directory.parent_id in self.directories:
            self.directories[directory.parent_id].remove_child(dir_id)
        
        # 删除目录本身
        del self.directories[dir_id]
        self.save_to_file()
        return True
    
    def get_directory(self, dir_id: str) -> Optional[Directory]:
        """获取指定ID的目录"""
        return self.directories.get(dir_id)
    
    def get_subdirectories(self, dir_id: str) -> List[Directory]:
        """获取指定目录的子目录列表，按顺序返回"""
        if dir_id in self.directories:
            subdirs = []
            for child_id in self.directories[dir_id].children:
                if child_id in self.directories:
                    subdirs.append(self.directories[child_id])
            # 按顺序排序
            subdirs.sort(key=lambda x: x.order)
            return subdirs
        return []
    
    def get_directory_tree(self, start_dir_id: str = None) -> Dict:
        """获取目录树结构"""
        if not start_dir_id:
            start_dir_id = self.root_dir_id
        
        if start_dir_id not in self.directories:
            return {}
        
        directory = self.directories[start_dir_id]
        tree = {
            'id': directory.id,
            'name': directory.name,
            'order': directory.order,
            'children': [],
            'notes': [
                {
                    'id': nid, 
                    'title': self.notes[nid].title,
                    'modified_time': self.notes[nid].modified_time.isoformat()
                } 
                for nid in directory.notes if nid in self.notes
            ]
        }
        
        for child_id in directory.children:
            child_tree = self.get_directory_tree(child_id)
            if child_tree:
                tree['children'].append(child_tree)
        
        return tree
    
    def save_to_file(self):
        """将数据保存到文件"""
        data = {
            'notes': {nid: note.to_dict() for nid, note in self.notes.items()},
            'directories': {did: directory.to_dict() 
                           for did, directory in self.directories.items()}
        }
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self):
        """从文件加载数据"""
        if not os.path.exists(self.storage_file):
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载笔记
            for nid, note_data in data.get('notes', {}).items():
                self.notes[nid] = Note.from_dict(note_data)
            
            # 加载目录
            for did, dir_data in data.get('directories', {}).items():
                self.directories[did] = Directory.from_dict(dir_data)
        
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"加载数据文件 {self.storage_file} 时出错")


class NotebookApp:
    """知识库笔记本GUI应用程序"""
    def __init__(self, root):
        self.root = root
        self.root.title("知识库笔记本")
        self.root.geometry("1000x700")
        
        # 创建笔记本实例
        self.notebook = KnowledgeBaseNotebook()
        
        # 当前选中的目录ID
        self.current_dir_id = self.notebook.root_dir_id
        
        # 当前编辑的笔记ID
        self.current_note_id = None
        
        # 创建界面
        self.create_widgets()
        
        # 加载初始数据
        self.refresh_directory_tree()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧目录树
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 目录树标题
        dir_label = ttk.Label(left_frame, text="目录结构")
        dir_label.pack(anchor=tk.W)
        
        # 目录树滚动区域
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dir_tree = ttk.Treeview(
            left_frame,
            yscrollcommand=tree_scroll.set,
            height=20
        )
        self.dir_tree.pack(side=tk.LEFT, fill=tk.Y)
        tree_scroll.config(command=self.dir_tree.yview)
        
        # 目录树事件绑定
        self.dir_tree.bind("<<TreeviewSelect>>", self.on_directory_select)
        
        # 目录操作按钮
        dir_btn_frame = ttk.Frame(left_frame)
        dir_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(dir_btn_frame, text="新建目录", command=self.create_new_directory).pack(fill=tk.X, pady=2)
        ttk.Button(dir_btn_frame, text="重命名目录", command=self.rename_directory).pack(fill=tk.X, pady=2)
        ttk.Button(dir_btn_frame, text="删除目录", command=self.delete_directory).pack(fill=tk.X, pady=2)
        
        # 右侧内容区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 笔记列表区域
        list_frame = ttk.LabelFrame(right_frame, text="笔记列表", padding=5)
        list_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 笔记列表滚动区域
        note_list_scroll = ttk.Scrollbar(list_frame)
        note_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.note_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=note_list_scroll.set
        )
        self.note_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        note_list_scroll.config(command=self.note_listbox.yview)
        
        # 笔记列表事件绑定
        self.note_listbox.bind("<<ListboxSelect>>", self.on_note_select)
        
        # 笔记操作按钮
        note_btn_frame = ttk.Frame(list_frame)
        note_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(note_btn_frame, text="新建笔记", command=self.create_new_note).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(note_btn_frame, text="删除笔记", command=self.delete_selected_note).pack(side=tk.LEFT, padx=(0, 5))
        
        # 笔记编辑区域
        edit_frame = ttk.LabelFrame(right_frame, text="笔记内容", padding=5)
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        # 笔记标题
        title_frame = ttk.Frame(edit_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(title_frame, text="标题:").pack(anchor=tk.W)
        self.title_entry = ttk.Entry(title_frame)
        self.title_entry.pack(fill=tk.X)
        
        # 笔记内容
        content_frame = ttk.Frame(edit_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="内容:").pack(anchor=tk.W)
        
        # 创建文本编辑区域和滚动条
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=60,
            height=15
        )
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 版本控制按钮
        version_frame = ttk.Frame(right_frame)
        version_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(version_frame, text="保存版本快照", command=self.save_version_snapshot).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(version_frame, text="查看历史版本", command=self.view_note_versions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(version_frame, text="自动保存版本", command=self.toggle_auto_save_version).pack(side=tk.LEFT, padx=(0, 5))
        
        # 自动保存版本的标志
        self.auto_save_version = tk.BooleanVar(value=True)
        
        # 保存按钮
        save_btn = ttk.Button(right_frame, text="保存笔记", command=self.save_current_note)
        save_btn.pack(pady=5)
    
    def refresh_directory_tree(self):
        """刷新目录树"""
        # 清空现有项
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)
        
        # 递归添加目录和笔记
        self.add_directory_to_tree(self.notebook.root_dir_id, "")
    
    def add_directory_to_tree(self, dir_id, parent):
        """递归添加目录到树中"""
        directory = self.notebook.get_directory(dir_id)
        if not directory:
            return
        
        # 添加目录节点
        node_id = self.dir_tree.insert(
            parent,
            tk.END,
            text=directory.name,
            values=(dir_id, "directory")
        )
        
        # 添加该目录下的笔记
        notes = self.notebook.list_notes_in_directory(dir_id)
        for note in notes:
            self.dir_tree.insert(
                node_id,
                tk.END,
                text=note.title,
                values=(note.id, "note")
            )
        
        # 递归添加子目录
        subdirs = self.notebook.get_subdirectories(dir_id)
        for subdir in subdirs:
            self.add_directory_to_tree(subdir.id, node_id)
    
    def on_directory_select(self, event):
        """处理目录选择事件"""
        selection = self.dir_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_values = self.dir_tree.item(item_id, "values")
        
        if not item_values:
            return
        
        obj_id, obj_type = item_values
        
        if obj_type == "directory":
            self.current_dir_id = obj_id
            self.load_notes_for_directory(obj_id)
        elif obj_type == "note":
            self.load_note_content(obj_id)
    
    def load_notes_for_directory(self, dir_id):
        """加载指定目录下的笔记列表"""
        self.note_listbox.delete(0, tk.END)
        
        notes = self.notebook.list_notes_in_directory(dir_id)
        for note in notes:
            self.note_listbox.insert(tk.END, f"{note.title} ({note.modified_time.strftime('%m-%d %H:%M')})")
        
        # 清空当前笔记编辑区
        self.clear_note_editor()
    
    def on_note_select(self, event):
        """处理笔记选择事件"""
        selection = self.note_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        dir_notes = self.notebook.list_notes_in_directory(self.current_dir_id)
        
        if 0 <= index < len(dir_notes):
            note = dir_notes[index]
            self.load_note_content(note.id)
    
    def load_note_content(self, note_id):
        """加载笔记内容到编辑区"""
        note = self.notebook.get_note(note_id)
        if not note:
            return
        
        self.current_note_id = note_id
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note.title)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, note.content)
    
    def clear_note_editor(self):
        """清空笔记编辑区"""
        self.current_note_id = None
        self.title_entry.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)
    
    def create_new_note(self):
        """创建新笔记"""
        title = simpledialog.askstring("新建笔记", "请输入笔记标题:")
        if title:
            note = self.notebook.create_note(title, "", self.current_dir_id)
            self.load_note_content(note.id)
            self.load_notes_for_directory(self.current_dir_id)
            
            # 选中新的笔记
            notes = self.notebook.list_notes_in_directory(self.current_dir_id)
            idx = next((i for i, n in enumerate(notes) if n.id == note.id), -1)
            if idx >= 0:
                self.note_listbox.selection_set(idx)
    
    def save_current_note(self):
        """保存当前笔记"""
        if not self.current_note_id:
            messagebox.showwarning("警告", "请先选择一个笔记进行编辑")
            return
        
        title = self.title_entry.get().strip()
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not title:
            messagebox.showwarning("警告", "笔记标题不能为空")
            return
        
        if self.notebook.update_note(self.current_note_id, title, content, self.auto_save_version.get()):
            messagebox.showinfo("成功", "笔记已保存")
            self.load_notes_for_directory(self.current_dir_id)
            
            # 重新选中当前笔记
            notes = self.notebook.list_notes_in_directory(self.current_dir_id)
            idx = next((i for i, n in enumerate(notes) if n.id == self.current_note_id), -1)
            if idx >= 0:
                self.note_listbox.selection_set(idx)
        else:
            messagebox.showerror("错误", "保存笔记失败")
    
    def delete_selected_note(self):
        """删除选中的笔记"""
        selection = self.note_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个笔记进行删除")
            return
        
        index = selection[0]
        dir_notes = self.notebook.list_notes_in_directory(self.current_dir_id)
        
        if 0 <= index < len(dir_notes):
            note = dir_notes[index]
            result = messagebox.askyesno("确认删除", f"确定要删除笔记 '{note.title}' 吗？")
            if result:
                if self.notebook.delete_note(note.id):
                    self.clear_note_editor()
                    self.load_notes_for_directory(self.current_dir_id)
                    messagebox.showinfo("成功", "笔记已删除")
                else:
                    messagebox.showerror("错误", "删除笔记失败")
    
    def create_new_directory(self):
        """创建新目录"""
        name = simpledialog.askstring("新建目录", "请输入目录名称:")
        if name:
            directory = self.notebook.create_directory(name, self.current_dir_id)
            self.refresh_directory_tree()
    
    def rename_directory(self):
        """重命名选中的目录"""
        selection = self.dir_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个目录进行重命名")
            return
        
        item_id = selection[0]
        item_values = self.dir_tree.item(item_id, "values")
        
        if not item_values or item_values[1] != "directory":
            messagebox.showwarning("警告", "请选择一个目录进行重命名")
            return
        
        dir_id = item_values[0]
        directory = self.notebook.get_directory(dir_id)
        
        new_name = simpledialog.askstring("重命名目录", f"请输入新的目录名称:", initialvalue=directory.name)
        if new_name:
            if self.notebook.rename_directory(dir_id, new_name):
                self.refresh_directory_tree()
            else:
                messagebox.showerror("错误", "重命名目录失败")
    
    def delete_directory(self):
        """删除选中的目录"""
        selection = self.dir_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个目录进行删除")
            return
        
        item_id = selection[0]
        item_values = self.dir_tree.item(item_id, "values")
        
        if not item_values or item_values[1] != "directory":
            messagebox.showwarning("警告", "请选择一个目录进行删除")
            return
        
        dir_id = item_values[0]
        directory = self.notebook.get_directory(dir_id)
        
        result = messagebox.askyesno("确认删除", f"确定要删除目录 '{directory.name}' 吗？\n目录中的笔记将移至根目录。")
        if result:
            if self.notebook.delete_directory(dir_id, delete_notes=False):
                self.refresh_directory_tree()
                if dir_id == self.current_dir_id:
                    self.current_dir_id = self.notebook.root_dir_id
                    self.load_notes_for_directory(self.current_dir_id)
                messagebox.showinfo("成功", "目录已删除")
            else:
                messagebox.showerror("错误", "删除目录失败")
    
    def save_version_snapshot(self):
        """手动保存版本快照"""
        if not self.current_note_id:
            messagebox.showwarning("警告", "请先选择一个笔记")
            return
        
        note = self.notebook.get_note(self.current_note_id)
        if note:
            note.save_version_snapshot()
            self.notebook.save_to_file()
            messagebox.showinfo("成功", "版本快照已保存")
    
    def view_note_versions(self):
        """查看笔记历史版本"""
        if not self.current_note_id:
            messagebox.showwarning("警告", "请先选择一个笔记")
            return
        
        note = self.notebook.get_note(self.current_note_id)
        if not note or not note.versions:
            messagebox.showinfo("信息", "该笔记没有历史版本")
            return
        
        # 创建版本历史窗口
        version_window = tk.Toplevel(self.root)
        version_window.title("笔记版本历史")
        version_window.geometry("800x500")
        
        # 创建列表框显示版本
        list_frame = ttk.Frame(version_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        version_listbox = tk.Listbox(list_frame)
        version_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=version_listbox.yview)
        version_listbox.configure(yscrollcommand=version_scroll.set)
        
        version_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加版本到列表
        for i, version in enumerate(note.versions):
            version_listbox.insert(
                tk.END,
                f"版本 {i+1}: {version.version_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # 详情显示区域
        detail_frame = ttk.LabelFrame(version_window, text="版本详情", padding=5)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        title_label = ttk.Label(detail_frame, text="标题:")
        title_label.pack(anchor=tk.W)
        title_display = tk.Text(detail_frame, height=2, state=tk.DISABLED)
        title_display.pack(fill=tk.X, pady=(0, 5))
        
        content_label = ttk.Label(detail_frame, text="内容:")
        content_label.pack(anchor=tk.W)
        content_display = scrolledtext.ScrolledText(detail_frame, height=10, state=tk.DISABLED)
        content_display.pack(fill=tk.BOTH, expand=True)
        
        # 按钮区域
        btn_frame = ttk.Frame(version_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        restore_btn = ttk.Button(
            btn_frame,
            text="恢复此版本",
            state=tk.DISABLED,
            command=lambda: self.restore_version(
                note,
                version_listbox,
                version_window
            )
        )
        restore_btn.pack(side=tk.LEFT)
        
        close_btn = ttk.Button(btn_frame, text="关闭", command=version_window.destroy)
        close_btn.pack(side=tk.RIGHT)
        
        # 选择版本事件
        def on_version_select(event):
            selection = version_listbox.curselection()
            if not selection:
                return
            
            idx = selection[0]
            version = note.versions[idx]
            
            # 显示版本详情
            title_display.config(state=tk.NORMAL)
            title_display.delete(1.0, tk.END)
            title_display.insert(1.0, version.title)
            title_display.config(state=tk.DISABLED)
            
            content_display.config(state=tk.NORMAL)
            content_display.delete(1.0, tk.END)
            content_display.insert(1.0, version.content)
            content_display.config(state=tk.DISABLED)
            
            restore_btn.config(state=tk.NORMAL)
        
        version_listbox.bind("<<ListboxSelect>>", on_version_select)
    
    def restore_version(self, note, version_listbox, window):
        """恢复选中的版本"""
        selection = version_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if note.restore_version(idx):
            self.notebook.save_to_file()
            self.load_note_content(note.id)
            window.destroy()
            messagebox.showinfo("成功", "已恢复到选定版本")
    
    def toggle_auto_save_version(self):
        """切换自动保存版本功能"""
        self.auto_save_version.set(not self.auto_save_version.get())
        status = "开启" if self.auto_save_version.get() else "关闭"
        messagebox.showinfo("提示", f"自动保存版本功能已{status}")


def main():
    """主函数，启动GUI应用程序"""
    root = tk.Tk()
    app = NotebookApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()