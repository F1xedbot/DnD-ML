import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import io

class GalleryTab(ctk.CTkFrame):
    def __init__(self, parent, db, on_image_click: callable):
        super().__init__(parent)
        self.db = db
        self.on_image_click = on_image_click

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.upload_button = ctk.CTkButton(self.sidebar, text="Upload Image", command=self.upload_image)
        self.upload_button.grid(row=0, column=0, padx=20, pady=20)

        # Gallery Area
        self.gallery_frame = ctk.CTkScrollableFrame(self, label_text="My Collection")
        self.gallery_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.gallery_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.load_images()

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if file_path:
            self.db.add_image(file_path)
            self.load_images()

    def load_images(self):
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        images = self.db.get_all_images()
        row, col = 0, 0
        for img_model in images:
            try:
                image_data = io.BytesIO(img_model.data)
                pil_image = Image.open(image_data)
                pil_image.thumbnail((150, 150))
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                
                # Clickable Frame
                item_frame = ctk.CTkButton(self.gallery_frame, text="", image=ctk_image, 
                                           fg_color="transparent", hover_color="gray",
                                           command=lambda n=img_model.name: self.on_image_click(n))
                item_frame.grid(row=row, column=col, padx=10, pady=10)
                
                ctk.CTkLabel(self.gallery_frame, text=img_model.name, font=ctk.CTkFont(size=12)).grid(row=row+1, column=col)
                
                # Indicators
                has_labels = "Labels: YES" if getattr(img_model, 'relevant_labels', None) else "Labels: NO"
                has_tiles = "Tiles: YES" if getattr(img_model, 'tile_data', None) else "Tiles: NO"
                
                lbl_color = "green" if getattr(img_model, 'relevant_labels', None) else "gray"
                tile_color = "green" if getattr(img_model, 'tile_data', None) else "gray"

                ctk.CTkLabel(self.gallery_frame, text=has_labels, font=ctk.CTkFont(size=10), text_color=lbl_color).grid(row=row+2, column=col)
                ctk.CTkLabel(self.gallery_frame, text=has_tiles, font=ctk.CTkFont(size=10), text_color=tile_color).grid(row=row+3, column=col)

                col += 1
                if col > 3:
                    col = 0
                    row += 4 
            except Exception as e:
                print(f"Error loading image: {e}")
