import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import io
import threading
import tempfile
import os

class DetailView(ctk.CTkFrame):
    def __init__(self, parent, db, on_back, label_selector, tile_generator):
        super().__init__(parent)
        self.db = db
        self.on_back = on_back
        self.label_selector = label_selector
        self.tile_generator = tile_generator
        self.current_image_name = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left: Image Display
        self.detail_image_frame = ctk.CTkFrame(self)
        self.detail_image_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.detail_image_label = ctk.CTkLabel(self.detail_image_frame, text="")
        self.detail_image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # Overlay Controls (Hidden by default)
        self.btn_prev_map = ctk.CTkButton(self.detail_image_frame, text="<", width=30, height=50, fg_color="transparent", text_color="white", font=ctk.CTkFont(size=20, weight="bold"), command=self.prev_map)
        self.btn_next_map = ctk.CTkButton(self.detail_image_frame, text=">", width=30, height=50, fg_color="transparent", text_color="white", font=ctk.CTkFont(size=20, weight="bold"), command=self.next_map)
        self.lbl_overlay_title = ctk.CTkLabel(self.detail_image_frame, text="", fg_color=("black", "black"), corner_radius=5, text_color="white")


        # Right: Controls & Info
        self.detail_info_frame = ctk.CTkFrame(self, width=450)
        self.detail_info_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Back Button
        ctk.CTkButton(self.detail_info_frame, text="< Back to Gallery", command=self.on_back).pack(pady=10, padx=10, anchor="w")

        # Delete Button
        self.btn_delete = ctk.CTkButton(self.detail_info_frame, text="Delete Image", fg_color="red", hover_color="darkred", command=self.delete_current_image)
        self.btn_delete.pack(pady=20, padx=10, anchor="s", side="bottom")

        # Tabview
        self.tabview = ctk.CTkTabview(self.detail_info_frame, command=self.update_preview)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_get_labels = self.tabview.add("Get Image Labels")
        self.tab_gen_tile = self.tabview.add("Generate Tile Label")
        self.tab_tile_data = self.tabview.add("Tile Data Preview")

        # --- Tab 1: Get Image Labels ---
        ctk.CTkLabel(self.tab_get_labels, text="Analysis Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.config_frame = ctk.CTkFrame(self.tab_get_labels)
        self.config_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.config_frame, text="Top-K:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_top_k = ctk.CTkEntry(self.config_frame, width=50)
        self.entry_top_k.insert(0, "5")
        self.entry_top_k.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.config_frame, text="Threshold:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_threshold = ctk.CTkEntry(self.config_frame, width=50)
        self.entry_threshold.insert(0, "0.2")
        self.entry_threshold.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.config_frame, text="Prompt:").grid(row=1, column=0, columnspan=4, padx=5, pady=(10,0), sticky="w")
        self.entry_prompt = ctk.CTkTextbox(self.config_frame, height=80)
        self.entry_prompt.insert("1.0", "a top-down rpg map texture of {}")
        self.entry_prompt.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        self.config_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_analyze = ctk.CTkButton(self.tab_get_labels, text="Get Relevant Labels", command=self.analyze_image)
        self.btn_analyze.pack(pady=10)

        ctk.CTkLabel(self.tab_get_labels, text="Relevant Labels", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5))
        self.results_frame = ctk.CTkScrollableFrame(self.tab_get_labels, height=300)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 2: Generate Tile Label ---
        ctk.CTkLabel(self.tab_gen_tile, text="Grid Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.grid_config_frame = ctk.CTkFrame(self.tab_gen_tile)
        self.grid_config_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.grid_config_frame, text="Rows:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_rows = ctk.CTkEntry(self.grid_config_frame, width=50)
        self.entry_rows.insert(0, "20")
        self.entry_rows.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(self.grid_config_frame, text="Cols:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_cols = ctk.CTkEntry(self.grid_config_frame, width=50)
        self.entry_cols.insert(0, "20")
        self.entry_cols.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        self.check_show_grid = ctk.CTkCheckBox(self.grid_config_frame, text="Show Grid Preview", command=self.update_preview)
        self.check_show_grid.grid(row=1, column=0, columnspan=4, padx=5, pady=10)
        
        self.grid_config_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.entry_rows.bind("<KeyRelease>", lambda e: self.update_preview())
        self.entry_cols.bind("<KeyRelease>", lambda e: self.update_preview())

        self.btn_generate_tiles = ctk.CTkButton(self.tab_gen_tile, text="Generate Tile Data", command=self.generate_tile_data)
        self.btn_generate_tiles.pack(pady=20)
        self.lbl_gen_status = ctk.CTkLabel(self.tab_gen_tile, text="")
        self.lbl_gen_status.pack(pady=5)
        
        # Label List / Warning
        self.lbl_gen_labels = ctk.CTkLabel(self.tab_gen_tile, text="", font=ctk.CTkFont(size=12), wraplength=400)
        self.lbl_gen_labels.pack(pady=10)

        self.map_data = {}
        self.map_keys = ["original", "material", "slope"]
        self.current_map_index = 0

        # --- Tab 3: Tile Data Preview ---
        ctk.CTkLabel(self.tab_tile_data, text="Tile Information", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.lbl_tile_pos = ctk.CTkLabel(self.tab_tile_data, text="Hover over image...", font=ctk.CTkFont(size=14))
        self.lbl_tile_pos.pack(pady=5)
        
        self.lbl_tile_stats = ctk.CTkLabel(self.tab_tile_data, text="", font=ctk.CTkFont(size=12), justify="left")
        self.lbl_tile_stats.pack(pady=10, padx=10, anchor="w")
        
        # Walkability Threshold Slider
        ctk.CTkLabel(self.tab_tile_data, text="Walkability Threshold:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20, 5))
        self.lbl_threshold_val = ctk.CTkLabel(self.tab_tile_data, text="0.4")
        self.lbl_threshold_val.pack(pady=0)
        
        self.slider_threshold = ctk.CTkSlider(self.tab_tile_data, from_=0.0, to=1.0, number_of_steps=20, command=self.update_preview_threshold)
        self.slider_threshold.set(0.4)
        self.slider_threshold.pack(pady=5, padx=20, fill="x")
        
        self.lbl_no_preview = ctk.CTkLabel(self.tab_tile_data, text="No Tile Data Available", font=ctk.CTkFont(size=16, weight="bold"), text_color="gray")
        
        self.btn_download_json = ctk.CTkButton(self.tab_tile_data, text="Download JSON", command=self.download_json)
        self.btn_download_json.pack(pady=10, side="bottom")
        self.btn_download_json.pack_forget() # Hidden by default

        self.detail_image_label.bind("<Motion>", self.on_image_hover)

    def update_preview_threshold(self, value):
        self.lbl_threshold_val.configure(text=f"{value:.2f}")
        self.update_preview()

    def load_image(self, image_name):
        self.current_image_name = image_name
        
        # Reset UI State
        self.entry_top_k.delete(0, "end")
        self.entry_top_k.insert(0, "5")
        self.entry_threshold.delete(0, "end")
        self.entry_threshold.insert(0, "0.2")
        self.entry_prompt.delete("1.0", "end")
        self.entry_prompt.insert("1.0", "a top-down rpg map texture of {}")
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        self.entry_rows.delete(0, "end")
        self.entry_rows.insert(0, "20")
        self.entry_cols.delete(0, "end")
        self.entry_cols.insert(0, "20")
        self.lbl_gen_labels.configure(text="")
        self.lbl_gen_status.configure(text="")
        self.lbl_tile_stats.configure(text="")
        self.lbl_tile_pos.configure(text="Hover over image...")
        self.check_show_grid.deselect()
        self.lbl_no_preview.place_forget()
        self.slider_threshold.set(0.4)
        self.lbl_threshold_val.configure(text="0.40")

        img_model = self.db.get_image(image_name)
        if not img_model: return

        self.original_image_data = img_model.data
        
        # Cache resized base image
        image_data = io.BytesIO(self.original_image_data)
        self.base_pil_image = Image.open(image_data).convert("RGB")
        self.base_pil_image.thumbnail((600, 600))
        
        self.last_hovered_tile = None
        
        self.update_preview()

        if img_model.analysis_config:
            self.entry_top_k.delete(0, "end")
            self.entry_top_k.insert(0, str(img_model.analysis_config.get("top_k", 5)))
            self.entry_threshold.delete(0, "end")
            self.entry_threshold.insert(0, str(img_model.analysis_config.get("threshold", 0.2)))
            self.entry_prompt.delete("1.0", "end")
            self.entry_prompt.insert("1.0", img_model.analysis_config.get("prompt", ""))

        self.display_results(img_model.relevant_labels)
        self.update_gen_tab_state()
        
        tile_data = getattr(img_model, 'tile_data', None)
        if tile_data:
            self.lbl_gen_status.configure(text="Tile data available.", text_color="green")
        else:
            self.lbl_gen_status.configure(text="No tile data generated.", text_color="gray")

    def update_gen_tab_state(self):
        img_model = self.db.get_image(self.current_image_name)
        if not img_model: return
        
        if img_model.relevant_labels:
            self.btn_generate_tiles.configure(state="normal")
            labels = [l['name'] if isinstance(l, dict) else l for l in img_model.relevant_labels]
            self.lbl_gen_labels.configure(text=f"Using Labels: {', '.join(labels)}", text_color="gray")
        else:
            self.btn_generate_tiles.configure(state="disabled")
            self.lbl_gen_labels.configure(text="No labels found. Please run 'Get Image Labels' first.", text_color="red")

        # Check for maps
        tile_data = getattr(img_model, 'tile_data', None)
        if tile_data and 'maps' in tile_data:
            self.map_data = tile_data['maps']
        else:
            self.map_data = {}
        
        self.update_preview()

    def next_map(self):
        self.current_map_index = (self.current_map_index + 1) % len(self.map_keys)
        self.update_preview()

    def prev_map(self):
        self.current_map_index = (self.current_map_index - 1) % len(self.map_keys)
        self.update_preview()

    def on_image_hover(self, event):
        if self.tabview.get() != "Tile Data Preview":
            return
        
        img_model = self.db.get_image(self.current_image_name)
        tile_data = getattr(img_model, 'tile_data', None)
        if not img_model or not tile_data:
            return

        if not hasattr(self, 'base_pil_image'): return

        w, h = self.base_pil_image.size
        
        rows = 20
        cols = 20
        tile_data_map = {}
        
        if tile_data and 'data' in tile_data:
            try:
                data_list = tile_data['data']
                cols = max(d['grid_pos'][0] for d in data_list) + 1
                rows = max(d['grid_pos'][1] for d in data_list) + 1
                for d in data_list:
                    tile_data_map[tuple(d['grid_pos'])] = d
            except: pass
        
        tile_w = w / cols
        tile_h = h / rows
        
        col = int(event.x // tile_w)
        row = int(event.y // tile_h)
        
        col = max(0, min(col, cols - 1))
        row = max(0, min(row, rows - 1))
        
        if self.last_hovered_tile != (row, col):
            self.last_hovered_tile = (row, col)
            self.lbl_tile_pos.configure(text=f"Row: {row}, Col: {col}")
            
            # Update visuals with highlight
            self._update_tile_visuals(rows, cols, highlight_row=row, highlight_col=col)
            
            if (col, row) in tile_data_map:
                data = tile_data_map[(col, row)]
                
                # Re-calculate status for display based on current slider
                threshold = self.slider_threshold.get()
                all_labels = self.db.get_all_labels()
                label_configs = {l.name: {"walkable": l.walkable, "slope_tolerance": l.slope_tolerance} for l in all_labels}
                
                walkable, reason, dominant = self.tile_generator.analyze_tile_logic(
                    data['composition'], data['slope_val'], label_configs, threshold
                )
                
                status_str = "WALKABLE" if walkable else f"BLOCKED ({reason})"
                comp_str = "\n".join([f"{k}: {v:.1%}" for k, v in data['composition'].items()])
                stats_text = f"Status: {status_str}\nSlope: {data['slope_val']}\nDominant: {dominant}\n\nComposition:\n{comp_str}"
            else:
                stats_text = "No Data"
            
            self.lbl_tile_stats.configure(text=stats_text)

    def _get_visualization_data(self):
        img_model = self.db.get_image(self.current_image_name)
        tile_data = getattr(img_model, 'tile_data', None)
        tile_data_map = {}
        if tile_data and 'data' in tile_data:
            for d in tile_data['data']:
                tile_data_map[tuple(d['grid_pos'])] = d
        return tile_data_map

    def _get_visualization_configs(self):
        threshold = self.slider_threshold.get()
        all_labels = self.db.get_all_labels()
        label_configs = {l.name: {"walkable": l.walkable, "slope_tolerance": l.slope_tolerance} for l in all_labels}
        return threshold, label_configs

    def _draw_tile_overlay(self, draw, x, y, tile_w, tile_h, data, label_configs, threshold):
        walkable, reason, _ = self.tile_generator.analyze_tile_logic(
            data['composition'], data['slope_val'], label_configs, threshold
        )
        
        if not walkable:
            if reason == "steep_slope":
                color = "red"
                width = 2
                draw.line([x, y, x + tile_w, y + tile_h], fill=color, width=width)
                draw.line([x, y + tile_h, x + tile_w, y], fill=color, width=width)
            else:
                color = "orange"
                width = 2
                draw.rectangle([x, y, x + tile_w, y + tile_h], outline=color, width=width)
                draw.line([x, y, x + tile_w, y + tile_h], fill=color, width=width)
        else:
            draw.rectangle([x, y, x + tile_w, y + tile_h], outline="#00FF00", width=1)

    def _update_tile_visuals(self, rows, cols, highlight_row=-1, highlight_col=-1):
        img_copy = self.base_pil_image.copy()
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img_copy, "RGBA")
        
        w, h = img_copy.size
        tile_w = w / cols
        tile_h = h / rows
        
        tile_data_map = self._get_visualization_data()
        threshold, label_configs = self._get_visualization_configs()

        # Draw Tiles
        for r in range(rows):
            for c in range(cols):
                if (c, r) in tile_data_map:
                    x = c * tile_w
                    y = r * tile_h
                    self._draw_tile_overlay(draw, x, y, tile_w, tile_h, tile_data_map[(c, r)], label_configs, threshold)

        if highlight_row >= 0 and highlight_col >= 0:
            hx = highlight_col * tile_w
            hy = highlight_row * tile_h
            draw.rectangle([hx, hy, hx + tile_w, hy + tile_h], fill=(255, 255, 255, 100))

        ctk_image = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
        self.detail_image_label.configure(image=ctk_image)

    def update_preview(self):
        if not hasattr(self, 'original_image_data'): return
        
        current_tab = self.tabview.get()

        # --- Carousel Controls Management ---
        # Only show in Generate Tile Label tab if map data exists
        show_carousel = False
        if current_tab == "Generate Tile Label" and self.map_data:
            show_carousel = True
        
        if show_carousel:
            self.btn_prev_map.place(relx=0.02, rely=0.5, anchor="w")
            self.btn_next_map.place(relx=0.98, rely=0.5, anchor="e")
        else:
            self.btn_prev_map.place_forget()
            self.btn_next_map.place_forget()
            self.lbl_overlay_title.place_forget()

        # --- Tab Specific Logic ---
        if current_tab == "Generate Tile Label":
            # self.update_gen_tab_state() # REMOVED to prevent recursion
            
            pil_image = self.base_pil_image.copy()
            
            if show_carousel:
                key = self.map_keys[self.current_map_index]
                if key in self.map_data:
                    try:
                        img_bytes = self.map_data[key]
                        pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        pil_image.thumbnail((600, 600))
                        
                        titles = {"original": "Original Image", "material": "Material Map", "slope": "Slope Map"}
                        self.lbl_overlay_title.configure(text=titles.get(key, key.capitalize()))
                        self.lbl_overlay_title.place(relx=0.5, rely=0.05, anchor="n")
                    except Exception as e:
                        print(f"Error loading map {key}: {e}")

            # Draw Grid if needed
            if self.check_show_grid.get():
                try:
                    rows = int(self.entry_rows.get())
                    cols = int(self.entry_cols.get())
                    rows = max(1, min(rows, 100))
                    cols = max(1, min(cols, 100))
                    self._draw_grid(pil_image, rows, cols)
                except ValueError: pass

            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
            self.detail_image_label.configure(image=ctk_image)
        
        elif current_tab == "Tile Data Preview":
             img_model = self.db.get_image(self.current_image_name)
             tile_data = getattr(img_model, 'tile_data', None)
             
             if not tile_data:
                 # Disable preview
                 self.lbl_no_preview.place(relx=0.5, rely=0.5, anchor="center")
                 self.slider_threshold.pack_forget()
                 self.btn_download_json.pack_forget()
                 
                 # Show dimmed base image
                 pil_image = self.base_pil_image.copy()
                 from PIL import ImageEnhance
                 enhancer = ImageEnhance.Brightness(pil_image)
                 pil_image = enhancer.enhance(0.5)
                 ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                 self.detail_image_label.configure(image=ctk_image)
                 return

             self.lbl_no_preview.place_forget()
             self.slider_threshold.pack(pady=5, padx=20, fill="x")
             self.btn_download_json.pack(pady=10, side="bottom")

             rows, cols = 20, 20
             if tile_data and 'data' in tile_data:
                 try:
                    data_list = tile_data['data']
                    cols = max(d['grid_pos'][0] for d in data_list) + 1
                    rows = max(d['grid_pos'][1] for d in data_list) + 1 
                 except: pass
             self._update_tile_visuals(rows, cols)
        
        else:
            self.lbl_no_preview.place_forget()
            ctk_image = ctk.CTkImage(light_image=self.base_pil_image, dark_image=self.base_pil_image, size=self.base_pil_image.size)
            self.detail_image_label.configure(image=ctk_image)

    def _draw_grid(self, image, rows, cols):
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        w, h = image.size
        tile_w = w / cols
        tile_h = h / rows
        
        for c in range(1, cols):
            x = c * tile_w
            draw.line([(x, 0), (x, h)], fill="red", width=2)
        for r in range(1, rows):
            y = r * tile_h
            draw.line([(0, y), (w, y)], fill="red", width=2)

    def generate_tile_data(self):
        try:
            rows = int(self.entry_rows.get())
            cols = int(self.entry_cols.get())
            rows = max(1, min(rows, 100))
            cols = max(1, min(cols, 100))
        except ValueError:
            messagebox.showerror("Error", "Invalid Rows/Cols")
            return

        img_model = self.db.get_image(self.current_image_name)
        if not img_model.relevant_labels:
            messagebox.showwarning("Warning", "Please run 'Get Image Labels' first to identify materials.")
            return
            
        current_config = {'rows': rows, 'cols': cols}
        existing_config = img_model.tile_data.get('config') if img_model.tile_data else None
        
        if existing_config == current_config:
            if not messagebox.askyesno("Confirm Overwrite", "Tile data for this configuration already exists. Overwrite?"):
                return
            
        labels = [l['name'] if isinstance(l, dict) else l for l in img_model.relevant_labels]
        
        # Get current configs for generation (snapshot)
        all_labels = self.db.get_all_labels()
        label_configs = {l.name: {"walkable": l.walkable, "slope_tolerance": l.slope_tolerance} for l in all_labels}
        
        self.btn_generate_tiles.configure(state="disabled", text="Generating...")
        self.lbl_gen_status.configure(text="Starting generation...", text_color="blue")
        self.update_idletasks()
        
        threading.Thread(target=self._run_tile_gen_thread, args=(labels, rows, cols, label_configs)).start()

    def _run_tile_gen_thread(self, labels, rows, cols, label_configs):
        img_model = self.db.get_image(self.current_image_name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_model.data)
            tmp_path = tmp.name

        try:
            result = self.tile_generator.generate(tmp_path, labels, rows, cols, label_configs=label_configs)
        except Exception as e:
            print(f"Gen Error: {e}")
            result = None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        self.after(0, lambda: self._on_tile_gen_complete(result))

    def _on_tile_gen_complete(self, result):
        self.btn_generate_tiles.configure(state="normal", text="Generate Tile Data")
        if result:
            self.db.update_image_tile_data(self.current_image_name, result)
            self.lbl_gen_status.configure(text="Generation Complete!", text_color="green")
            self.update_gen_tab_state() # Update UI state
            messagebox.showinfo("Success", "Tile data generated successfully.")
        else:
            self.lbl_gen_status.configure(text="Generation Failed.", text_color="red")
            messagebox.showerror("Error", "Failed to generate tile data.")

    def analyze_image(self):
        try:
            top_k = int(self.entry_top_k.get())
            if not (1 <= top_k <= 100): raise ValueError("Top-K must be between 1 and 100")
            
            threshold = float(self.entry_threshold.get())
            if not (0.0 <= threshold <= 1.0): raise ValueError("Threshold must be between 0.0 and 1.0")
            
            prompt = self.entry_prompt.get("1.0", "end-1c").strip()
            if "{}" not in prompt: raise ValueError("Prompt must contain '{}' placeholder")
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        img_model = self.db.get_image(self.current_image_name)
        if img_model.relevant_labels:
            prev_config = img_model.analysis_config
            is_same = (prev_config.get("top_k") == top_k and 
                       prev_config.get("threshold") == threshold and 
                       prev_config.get("prompt") == prompt)
            
            msg = "Re-analyze image? Existing results will be overwritten."
            if is_same:
                msg += "\n\nWARNING: Configuration is identical to previous run."
            
            if not messagebox.askyesno("Confirm Analysis", msg):
                return

        self.btn_analyze.configure(state="disabled", text="Analyzing (Loading Model)...")
        self.update_idletasks()

        threading.Thread(target=self._run_analysis_thread, args=(top_k, threshold, prompt)).start()

    def _run_analysis_thread(self, top_k, threshold, prompt):
        all_labels = self.db.get_all_labels()
        label_names = [l.name for l in all_labels]
        
        img_model = self.db.get_image(self.current_image_name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_model.data)
            tmp_path = tmp.name

        try:
            final_labels = self.label_selector.analyze(tmp_path, label_names, prompt, top_k, threshold)
        except Exception as e:
            print(f"Analysis Error: {e}")
            final_labels = []
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        config = {"top_k": top_k, "threshold": threshold, "prompt": prompt}
        self.after(0, lambda: self._on_analysis_complete(final_labels, config))

    def _on_analysis_complete(self, final_labels, config):
        self.db.update_image_analysis(self.current_image_name, final_labels, config)
        self.display_results(final_labels)
        self.update_gen_tab_state()
        self.btn_analyze.configure(state="normal", text="Get Relevant Labels")

    def display_results(self, labels):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not labels:
            ctk.CTkLabel(self.results_frame, text="No labels found.").pack(pady=10)
            return

        for label_data in labels:
            if isinstance(label_data, str):
                text = label_data
            else:
                text = f"{label_data['name']} ({label_data['score']:.2f})"
            
            ctk.CTkLabel(self.results_frame, text=text, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=2)

    def delete_current_image(self):
        if not self.current_image_name: return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.current_image_name}'?"):
            if self.db.delete_image(self.current_image_name):
                self.on_back()
            else:
                messagebox.showerror("Error", "Failed to delete image.")

    def download_json(self):
        img_model = self.db.get_image(self.current_image_name)
        if not img_model or not img_model.tile_data:
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        try:
            import json
            
            all_labels = self.db.get_all_labels()
            label_configs = [{"name": l.name, "walkable": l.walkable, "slope_tolerance": l.slope_tolerance} for l in all_labels]
            
            raw_tiles = img_model.tile_data.get('data', [])
            clean_tiles = []
            for t in raw_tiles:
                clean_tiles.append({
                    "grid_pos": t.get("grid_pos"),
                    "composition": t.get("composition"),
                    "slope_val": t.get("slope_val")
                })

            export_data = {
                "config": img_model.tile_data.get('config', ""),
                "labels": label_configs,
                "tiles": clean_tiles
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=4)
                
            messagebox.showinfo("Success", "Tile data exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export JSON: {e}")
