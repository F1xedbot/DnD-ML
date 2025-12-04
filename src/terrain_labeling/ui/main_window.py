import customtkinter as ctk
from core.database import Database
from ui.gallery_tab import GalleryTab
from ui.labels_tab import LabelsTab
from ui.detail_view import DetailView
from ml.label_selector import LabelSelector
from ml.tile_generator import TileGenerator

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("2D Map Terrain Labeler")
        self.geometry("1000x700")

        self.db = Database()
        self.label_selector = LabelSelector() # Singleton lazy init
        self.tile_generator = TileGenerator() # Singleton lazy init

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Container
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Views
        self.main_view = ctk.CTkFrame(self.container)
        self.detail_view = DetailView(self.container, self.db, self.show_main_view, self.label_selector, self.tile_generator)

        self.setup_main_view()
        self.show_main_view()

    def setup_main_view(self):
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_view)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_gallery = self.tabview.add("Gallery")
        self.tab_labels = self.tabview.add("Labels")

        # Initialize Tabs
        self.gallery_tab = GalleryTab(self.tab_gallery, self.db, self.show_detail_view)
        self.gallery_tab.pack(fill="both", expand=True)

        self.labels_tab = LabelsTab(self.tab_labels, self.db)
        self.labels_tab.pack(fill="both", expand=True)

    def show_main_view(self):
        self.detail_view.grid_forget()
        self.main_view.grid(row=0, column=0, sticky="nsew")
        self.gallery_tab.load_images() # Refresh gallery

    def show_detail_view(self, image_name):
        self.main_view.grid_forget()
        self.detail_view.grid(row=0, column=0, sticky="nsew")
        self.detail_view.load_image(image_name)

    def on_closing(self):
        self.db.close()
        self.destroy()
