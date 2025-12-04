import customtkinter as ctk
from tkinter import messagebox

class LabelsTab(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Add Label Section
        self.add_label_frame = ctk.CTkFrame(self)
        self.add_label_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.add_label_frame, text="New Label:").pack(side="left", padx=10)
        self.entry_name = ctk.CTkEntry(self.add_label_frame, placeholder_text="Name")
        self.entry_name.pack(side="left", padx=10)
        
        self.var_walkable = ctk.BooleanVar(value=True)
        self.check_walkable = ctk.CTkCheckBox(self.add_label_frame, text="Walkable", variable=self.var_walkable)
        self.check_walkable.pack(side="left", padx=10)
        
        ctk.CTkLabel(self.add_label_frame, text="Slope (0-1):").pack(side="left", padx=10)
        self.entry_slope = ctk.CTkEntry(self.add_label_frame, width=60, placeholder_text="0.5")
        self.entry_slope.pack(side="left", padx=10)
        
        ctk.CTkButton(self.add_label_frame, text="Add", command=self.add_label).pack(side="left", padx=10)

        # Labels List
        self.labels_list_frame = ctk.CTkScrollableFrame(self, label_text="Existing Labels")
        self.labels_list_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.load_labels()

    def add_label(self):
        name = self.entry_name.get().strip()
        if not name: return
        try:
            slope = float(self.entry_slope.get() or 0.5)
            if not (0.0 <= slope <= 1.0): raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Slope must be between 0.0 and 1.0")
            return

        if self.db.add_label(name, self.var_walkable.get(), slope):
            self.load_labels()
            self.entry_name.delete(0, "end")
            self.entry_slope.delete(0, "end")
        else:
            messagebox.showerror("Error", "Label already exists")

    def load_labels(self):
        for widget in self.labels_list_frame.winfo_children():
            widget.destroy()
        labels = self.db.get_all_labels()
        labels.sort(key=lambda x: x.name)
        for label in labels:
            frame = ctk.CTkFrame(self.labels_list_frame)
            frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(frame, text=label.name, width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            var_walk = ctk.BooleanVar(value=label.walkable)
            ctk.CTkCheckBox(frame, text="Walkable", variable=var_walk, command=lambda l=label, v=var_walk: self.update_label_walkable(l, v)).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text="Slope:").pack(side="left", padx=5)
            entry_slope = ctk.CTkEntry(frame, width=50)
            entry_slope.insert(0, str(label.slope_tolerance))
            entry_slope.pack(side="left", padx=5)
            ctk.CTkButton(frame, text="Update", width=60, command=lambda l=label, e=entry_slope: self.update_label_slope(l, e)).pack(side="left", padx=5)
            ctk.CTkButton(frame, text="Delete", width=60, fg_color="red", hover_color="darkred", command=lambda l=label: self.delete_label(l)).pack(side="right", padx=10)

    def update_label_walkable(self, label, var):
        self.db.update_label(label.name, var.get(), label.slope_tolerance)

    def update_label_slope(self, label, entry):
        try:
            slope = float(entry.get())
            if not (0.0 <= slope <= 1.0): raise ValueError
            self.db.update_label(label.name, label.walkable, slope)
            messagebox.showinfo("Success", f"Updated {label.name}")
        except ValueError:
            messagebox.showerror("Error", "Invalid slope value")

    def delete_label(self, label):
        if messagebox.askyesno("Confirm", f"Delete label '{label.name}'?"):
            self.db.delete_label(label.name)
            self.load_labels()
