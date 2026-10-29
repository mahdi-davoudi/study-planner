import ttkbootstrap as tb
from tkinter import messagebox


class ManageSubjectsFrame(tb.Frame):
    def __init__(self, parent, db, on_subjects_changed=None):
        super().__init__(parent, padding=20)
        self.db = db
        self.on_subjects_changed = on_subjects_changed

        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        title = tb.Label(self, text="Manage Subjects", font=("Tahoma", 16, "bold"))
        title.grid(row=0, column=0, sticky="e", pady=(0, 15))

        # add new subject section
        add_frame = tb.Frame(self)
        add_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        add_frame.columnconfigure(0, weight=1)

        add_btn = tb.Button(add_frame, text="Add Subject", command=self.add_subject, bootstyle="success")
        add_btn.grid(row=0, column=1, padx=(0, 8))

        self.new_subject_entry = tb.Entry(add_frame, font=("Tahoma", 11), justify="right", bootstyle="primary")
        self.new_subject_entry.grid(row=0, column=0, sticky="ew")
        self.new_subject_entry.bind("<Return>", lambda e: self.add_subject())

        # subject list card
        card = tb.Labelframe(self, text="Subject List", padding=10, bootstyle="primary")
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        self.listbox = tb.Treeview(card, columns=("name",), show="headings", bootstyle="primary")
        self.listbox.heading("name", text="Subject Name")
        self.listbox.column("name", anchor="e")
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = tb.Scrollbar(card, orient="vertical", command=self.listbox.yview, bootstyle="round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # action buttons for the selected subject 
        action_frame = tb.Frame(self)
        action_frame.grid(row=3, column=0, sticky="e")

        delete_btn = tb.Button(action_frame, text="Delete Selected Subject", command=self.delete_selected, bootstyle="danger")
        delete_btn.grid(row=0, column=1, padx=(8, 0))

        rename_btn = tb.Button(action_frame, text="Rename", command=self.rename_selected, bootstyle="info")
        rename_btn.grid(row=0, column=0)

        self._subject_docs = []

    def refresh_list(self):
        # Reload the subject list from the database and display it in the table.
        self._subject_docs = self.db.get_subjects()
        for row in self.listbox.get_children():
            self.listbox.delete(row)
        for doc in self._subject_docs:
            self.listbox.insert("", "end", iid=str(doc["_id"]), values=(doc["name"],))

    def add_subject(self):
        name = self.new_subject_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "Enter a subject name.")
            return
        self.db.add_subject(name)
        self.new_subject_entry.delete(0, "end")
        self.refresh_list()
        if self.on_subjects_changed:
            self.on_subjects_changed()

    def _get_selected_doc(self):
        selection = self.listbox.selection()
        if not selection:
            messagebox.showinfo("Notice", "Select a subject from the list first.")
            return None
        selected_id = selection[0]
        for doc in self._subject_docs:
            if str(doc["_id"]) == selected_id:
                return doc
        return None

    def delete_selected(self):
        doc = self._get_selected_doc()
        if not doc:
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete subject '{doc['name']}'?\n(Previously logged study records for this subject will remain in reports)"
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

        dialog = tb.Toplevel(self)
        dialog.title("Rename Subject")
        dialog.geometry("320x150")
        dialog.resizable(False, False)

        tb.Label(dialog, text="New name:", font=("Tahoma", 11)).pack(pady=(20, 8))
        entry = tb.Entry(dialog, font=("Tahoma", 11), justify="right", bootstyle="primary")
        entry.insert(0, doc["name"])
        entry.pack(padx=20, fill="x")
        entry.focus()

        def save():
            new_name = entry.get().strip()
            if new_name:
                if not self.db.rename_subject(doc["_id"], new_name):
                    messagebox.showwarning("Error", "A subject with this name already exists.", parent=dialog)
                    return
                self.refresh_list()
                if self.on_subjects_changed:
                    self.on_subjects_changed()
            dialog.destroy()

        tb.Button(dialog, text="Save", command=save, bootstyle="success").pack(pady=15)
        entry.bind("<Return>", lambda e: save())