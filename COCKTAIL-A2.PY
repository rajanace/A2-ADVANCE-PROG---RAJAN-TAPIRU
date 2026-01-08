import tkinter as tk
from tkinter import ttk, messagebox
import requests
from io import BytesIO

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


API_BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"


def fetch_json(endpoint, params=None):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        messagebox.showerror("Network Error", f"Error contacting API:\n{e}")
        return None


def get_random_cocktail():
    data = fetch_json("random.php")
    if not data or not data.get("drinks"):
        return None
    return data["drinks"][0]


def search_cocktails_by_name(name):
    if not name.strip():
        messagebox.showinfo("Input Required", "Please enter a cocktail name.")
        return []

    data = fetch_json("search.php", params={"s": name})
    if not data or not data.get("drinks"):
        messagebox.showinfo("No Results", f"No cocktails found for '{name}'.")
        return []
    return data["drinks"]


def get_all_cocktails():
    """Fetch ALL cocktails by sending an empty search query."""
    data = fetch_json("search.php", params={"s": ""})
    if not data or not data.get("drinks"):
        messagebox.showwarning("No Data", "Could not load all cocktails.")
        return []
    return data["drinks"]


def get_cocktail_details_by_id(drink_id):
    data = fetch_json("lookup.php", params={"i": drink_id})
    if not data or not data.get("drinks"):
        return None
    return data["drinks"][0]


def extract_ingredients(drink):
    ingredients = []
    for i in range(1, 16):
        ing = drink.get(f"strIngredient{i}")
        meas = drink.get(f"strMeasure{i}")
        if ing and ing.strip():
            if meas and meas.strip():
                ingredients.append(f"{meas.strip()} {ing.strip()}")
            else:
                ingredients.append(ing.strip())
    return ingredients


class CocktailApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cocktail Explorer")

        self.resizable(True, True)
        self.state("zoomed")

        self.cocktail_list = []
        self.current_image = None

        self.create_widgets()

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Search cocktail:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda event: self.on_search())

        ttk.Button(top_frame, text="Search", command=self.on_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Random Cocktail", command=self.on_random).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="View All Drinks", command=self.on_view_all).pack(side=tk.LEFT, padx=5)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(main_frame, text="Cocktails", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.listbox = tk.Listbox(left_frame, width=35)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        right_frame = ttk.LabelFrame(main_frame, text="Details", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.name_label = ttk.Label(right_frame, text="Name:", font=("Arial", 14, "bold"))
        self.name_label.pack(anchor="w")

        self.category_label = ttk.Label(right_frame, text="Category:")
        self.category_label.pack(anchor="w")

        self.alcoholic_label = ttk.Label(right_frame, text="Alcoholic:")
        self.alcoholic_label.pack(anchor="w")

        self.image_label = ttk.Label(right_frame)
        self.image_label.pack(pady=10)

        ttk.Label(right_frame, text="Ingredients:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.ingredients_text = tk.Text(right_frame, height=6, wrap=tk.WORD)
        self.ingredients_text.pack(fill=tk.X)
        self.ingredients_text.config(state=tk.DISABLED)

        ttk.Label(right_frame, text="Instructions:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.instructions_text = tk.Text(right_frame, height=10, wrap=tk.WORD)
        self.instructions_text.pack(fill=tk.BOTH, expand=True)
        self.instructions_text.config(state=tk.DISABLED)

    def on_search(self):
        query = self.search_var.get()
        cocktails = search_cocktails_by_name(query)
        self.update_cocktail_list(cocktails)

    def on_random(self):
        drink = get_random_cocktail()
        if drink:
            self.update_cocktail_list([drink])
            self.show_cocktail_details(drink)

    def on_view_all(self):
        """Load ALL cocktails from the API."""
        cocktails = get_all_cocktails()
        self.update_cocktail_list(cocktails)

    def on_list_select(self, event):
        if not self.listbox.curselection():
            return

        index = self.listbox.curselection()[0]
        drink = self.cocktail_list[index]

        drink_id = drink.get("idDrink")
        full_drink = get_cocktail_details_by_id(drink_id)

        if full_drink:
            self.show_cocktail_details(full_drink)

    def update_cocktail_list(self, cocktails):
        self.cocktail_list = cocktails or []
        self.listbox.delete(0, tk.END)

        for drink in self.cocktail_list:
            self.listbox.insert(tk.END, drink.get("strDrink", "Unnamed"))

        if self.cocktail_list:
            self.listbox.select_set(0)
            self.listbox.event_generate("<<ListboxSelect>>")

    def show_cocktail_details(self, drink):
        self.name_label.config(text=f"Name: {drink.get('strDrink', 'N/A')}")
        self.category_label.config(text=f"Category: {drink.get('strCategory', 'N/A')}")
        self.alcoholic_label.config(text=f"Alcoholic: {drink.get('strAlcoholic', 'N/A')}")

        ingredients = extract_ingredients(drink)
        self.ingredients_text.config(state=tk.NORMAL)
        self.ingredients_text.delete("1.0", tk.END)
        for item in ingredients:
            self.ingredients_text.insert(tk.END, f"- {item}\n")
        self.ingredients_text.config(state=tk.DISABLED)

        instructions = drink.get("strInstructions", "No instructions available.")
        self.instructions_text.config(state=tk.NORMAL)
        self.instructions_text.delete("1.0", tk.END)
        self.instructions_text.insert(tk.END, instructions)
        self.instructions_text.config(state=tk.DISABLED)

        self.load_cocktail_image(drink.get("strDrinkThumb"))

    def load_cocktail_image(self, url):
        if not PIL_AVAILABLE or not url:
            self.image_label.config(image="", text="(Image unavailable)")
            return

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img_data = response.content

            image = Image.open(BytesIO(img_data))
            image = image.resize((250, 250), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            self.image_label.config(image=photo)
            self.current_image = photo
        except:
            self.image_label.config(image="", text="(Error loading image)")


if __name__ == "__main__":
    app = CocktailApp()
    app.mainloop()
