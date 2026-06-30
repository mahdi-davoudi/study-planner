import tkinter as tk
from tkinter import ttk, messagebox


class ManageSubjectsFrame(ttk.Frame):
    def __init__(self, parent, db, on_subjects_changed=None):
        super().__init__(parent, padding=15)
        self.db = db
        # تابعی که وقتی لیست درس‌ها تغییر کرد صدا زده می‌شود (برای رفرش تب‌های دیگر)
        self.on_subjects_changed = on_subjects_changed

        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        title = ttk.Label(self, text="manage Lesson", font=("Tahoma", 14, "bold"))
        title.pack(anchor="e", pady=(0, 10))

        # --- بخش افزودن درس جدید ---
        add_frame = ttk.Frame(self)
        add_frame.pack(fill="x", pady=(0, 10))

        self.new_subject_entry = ttk.Entry(add_frame, font=("Tahoma", 11), justify="right")
        self.new_subject_entry.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.new_subject_entry.bind("<Return>", lambda e: self.add_subject())

        add_btn = ttk.Button(add_frame, text="add Lesson", command=self.add_subject)
        add_btn.pack(side="right")

        # --- لیست درس‌ها ---
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame, font=("Tahoma", 11), justify="right",
            activestyle="none", selectmode="single"
        )
        self.listbox.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- دکمه‌های عملیات روی درس انتخاب‌شده ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", pady=(10, 0))

        delete_btn = ttk.Button(action_frame, text="remove Lesson", command=self.delete_selected)
        delete_btn.pack(side="right", padx=(5, 0))

        rename_btn = ttk.Button(action_frame, text="change name", command=self.rename_selected)
        rename_btn.pack(side="right")

        # نگه‌داری اسناد فعلی برای دسترسی بر اساس ایندکس انتخاب‌شده در لیست‌باکس
        self._subject_docs = []

    def refresh_list(self):
        self._subject_docs = self.db.get_subjects()
        self.listbox.delete(0, tk.END)
        for doc in self._subject_docs:
            self.listbox.insert(tk.END, doc["name"])

    def add_subject(self):
        name = self.new_subject_entry.get().strip()
        if not name:
            messagebox.showwarning("error", "Enter Lesson name")
            return
        self.db.add_subject(name)
        self.new_subject_entry.delete(0, tk.END)
        self.refresh_list()
        if self.on_subjects_changed:
            self.on_subjects_changed()

    def _get_selected_doc(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("atention", "chose a Lesson from the list")
            return None
        index = selection[0]
        return self._subject_docs[index]

    def delete_selected(self):
        doc = self._get_selected_doc()
        if not doc:
            return
        confirm = messagebox.askyesno(
            "delete",
            f"should Lesson «{doc['name']}» be deleted? \n(Records of previous study of this lesson remain in reports)"
        )
        if confirm:
            self.db.delete_subject(doc["_id"])
            self.refresh_list()
            if self.on_subjects_changed:
                self.on_subjects_changed()

    def rename_selected(self):
        doc = self._get_selected_doc()
        if not doc:
            return

        # یک پنجره کوچک برای گرفتن نام جدید
        dialog = tk.Toplevel(self)
        dialog.title("change Lesson name")
        dialog.geometry("300x120")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="new name:", font=("Tahoma", 11)).pack(pady=(15, 5))
        entry = ttk.Entry(dialog, font=("Tahoma", 11), justify="right")
        entry.insert(0, doc["name"])
        entry.pack(padx=15, fill="x")
        entry.focus()

        def save():
            new_name = entry.get().strip()
            if new_name:
                self.db.rename_subject(doc["_id"], new_name)
                self.refresh_list()
                if self.on_subjects_changed:
                    self.on_subjects_changed()
            dialog.destroy()

        ttk.Button(dialog, text="save", command=save).pack(pady=10)
        entry.bind("<Return>", lambda e: save())