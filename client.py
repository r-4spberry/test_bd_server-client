import tkinter as tk
from tkinter import ttk, messagebox
import requests

BASE_URL = "http://localhost:8000" 
session = requests.Session()


def fetch_data(endpoint):
    try:
        response = session.get(f"{BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data from {endpoint}: {e}")
        return []


def add_data(endpoint, payload):
    try:
        response = session.post(f"{BASE_URL}{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add data: {e}")
        return None


class DataStore:
    def __init__(self):
        self.users = []
        self.posts = []
        self.comments = []

    def refresh_all(self):
        self.users = fetch_data("/users/")
        self.posts = fetch_data("/posts/")
        self.comments = fetch_data("/comments/")


data_store = DataStore()


class UsersTab(ttk.Frame):
    def __init__(self, parent, data_store):
        super().__init__(parent)
        self.data_store = data_store
        self.create_widgets()
        self.refresh_users()

    def create_widgets(self):
        self.tree = ttk.Treeview(
            self, columns=("ID", "Name", "Email"), show="headings", height=8
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        ttk.Label(self, text="Name:").grid(row=1, column=0, padx=10, sticky="e")
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=1, column=1, padx=10, sticky="w")
        ttk.Label(self, text="Email:").grid(row=1, column=2, padx=10, sticky="e")
        self.email_entry = ttk.Entry(self)
        self.email_entry.grid(row=1, column=3, padx=10, sticky="w")
        ttk.Button(self, text="Add User", command=self.add_user).grid(
            row=2, column=1, pady=10
        )
        ttk.Button(self, text="Refresh", command=self.refresh_all).grid(
            row=2, column=2, pady=10
        )
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def refresh_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for user in self.data_store.users:
            self.tree.insert(
                "", "end", values=(user.get("id"), user.get("name"), user.get("email"))
            )

    def add_user(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        if not name or not email:
            messagebox.showwarning("Input error", "Please provide both name and email.")
            return
        payload = {"name": name, "email": email}
        new_user = add_data("/users/", payload)
        if new_user:
            messagebox.showinfo("Success", f"User added with ID {new_user.get('id')}")
            self.refresh_users()

    def refresh_all(self):
        data_store.refresh_all()
        self.refresh_users()


class PostsTab(ttk.Frame):
    def __init__(self, parent, data_store):
        super().__init__(parent)
        self.data_store = data_store
        self.user_map = {}  
        self.id_to_user = {}
        self.create_widgets()
        self.populate_users()  
        self.refresh_posts()

    def create_widgets(self):
        self.tree = ttk.Treeview(
            self, columns=("ID", "Title", "Content", "User"), show="headings", height=8
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Content", text="Content")
        self.tree.heading("User", text="User")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        ttk.Label(self, text="Title:").grid(row=1, column=0, padx=10, sticky="e")
        self.title_entry = ttk.Entry(self)
        self.title_entry.grid(row=1, column=1, padx=10, sticky="w")
        ttk.Label(self, text="Content:").grid(row=1, column=2, padx=10, sticky="e")
        self.content_entry = ttk.Entry(self)
        self.content_entry.grid(row=1, column=3, padx=10, sticky="w")
        ttk.Label(self, text="User:").grid(row=2, column=0, padx=10, sticky="e")
        self.user_combo = ttk.Combobox(self, state="readonly")
        self.user_combo.grid(row=2, column=1, padx=10, sticky="w")
        ttk.Button(self, text="Add Post", command=self.add_post).grid(
            row=3, column=1, pady=10
        )
        ttk.Button(self, text="Refresh", command=self.refresh_all).grid(
            row=3, column=2, pady=10
        )
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def populate_users(self):
        names = []
        self.user_map.clear()
        self.id_to_user.clear()
        for user in self.data_store.users:
            name = user.get("name")
            uid = user.get("id")
            names.append(name)
            self.user_map[name] = uid
            self.id_to_user[uid] = name
        self.user_combo["values"] = names

    def refresh_posts(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for post in self.data_store.posts:
            uid = post.get("user_id")
            user_name = self.id_to_user.get(uid, f"ID {uid}")
            self.tree.insert(
                "",
                "end",
                values=(
                    post.get("id"),
                    post.get("title"),
                    post.get("content"),
                    user_name,
                ),
            )

    def add_post(self):
        title = self.title_entry.get().strip()
        content = self.content_entry.get().strip()
        selected_user = self.user_combo.get().strip()
        if not title or not content or not selected_user:
            messagebox.showwarning(
                "Input error", "Please fill all fields and select a user."
            )
            return
        user_id = self.user_map.get(selected_user)
        if not user_id:
            messagebox.showerror("Error", "Selected user does not exist.")
            return
        payload = {"title": title, "content": content, "user_id": user_id}
        new_post = add_data("/posts/", payload)
        if new_post:
            messagebox.showinfo("Success", f"Post added with ID {new_post.get('id')}")
            self.refresh_posts()

    def refresh_all(self):
        data_store.refresh_all()
        self.populate_users()
        self.refresh_posts()


class CommentsTab(ttk.Frame):
    def __init__(self, parent, data_store):
        super().__init__(parent)
        self.data_store = data_store
        self.post_map = {} 
        self.id_to_post = {}  
        self.user_map = {}
        self.id_to_user = {} 
        self.create_widgets()
        self.populate_posts()  
        self.populate_users() 
        self.refresh_comments()  

    def create_widgets(self):
        self.tree = ttk.Treeview(
            self, columns=("ID", "Content", "Post", "User"), show="headings", height=8
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Content", text="Content")
        self.tree.heading("Post", text="Post")
        self.tree.heading("User", text="User")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        ttk.Label(self, text="Content:").grid(row=1, column=0, padx=10, sticky="e")
        self.content_entry = ttk.Entry(self)
        self.content_entry.grid(row=1, column=1, padx=10, sticky="w")
        ttk.Label(self, text="Post:").grid(row=1, column=2, padx=10, sticky="e")
        self.post_combo = ttk.Combobox(self, state="readonly")
        self.post_combo.grid(row=1, column=3, padx=10, sticky="w")
        ttk.Label(self, text="User:").grid(row=2, column=0, padx=10, sticky="e")
        self.user_combo = ttk.Combobox(self, state="readonly")
        self.user_combo.grid(row=2, column=1, padx=10, sticky="w")
        ttk.Button(self, text="Add Comment", command=self.add_comment).grid(
            row=3, column=1, pady=10
        )
        ttk.Button(self, text="Refresh", command=self.refresh_all).grid(
            row=3, column=2, pady=10
        )
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def populate_posts(self):
        titles = []
        self.post_map.clear()
        self.id_to_post.clear()
        for post in self.data_store.posts:
            title = post.get("title")
            pid = post.get("id")
            titles.append(title)
            self.post_map[title] = pid
            self.id_to_post[pid] = title
        self.post_combo["values"] = titles

    def populate_users(self):
        names = []
        self.user_map.clear()
        self.id_to_user.clear()
        for user in self.data_store.users:
            name = user.get("name")
            uid = user.get("id")
            names.append(name)
            self.user_map[name] = uid
            self.id_to_user[uid] = name
        self.user_combo["values"] = names

    def refresh_comments(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for comment in self.data_store.comments:
            post_id = comment.get("post_id")
            user_id = comment.get("user_id")
            post_title = self.id_to_post.get(post_id, f"ID {post_id}")
            user_name = self.id_to_user.get(user_id, f"ID {user_id}")
            self.tree.insert(
                "",
                "end",
                values=(
                    comment.get("id"),
                    comment.get("content"),
                    post_title,
                    user_name,
                ),
            )

    def add_comment(self):
        content = self.content_entry.get().strip()
        selected_post = self.post_combo.get().strip()
        selected_user = self.user_combo.get().strip()
        if not content or not selected_post or not selected_user:
            messagebox.showwarning(
                "Input error", "Please fill all fields and select a post and a user."
            )
            return
        post_id = self.post_map.get(selected_post)
        user_id = self.user_map.get(selected_user)
        if not post_id:
            messagebox.showerror("Error", "Selected post does not exist.")
            return
        if not user_id:
            messagebox.showerror("Error", "Selected user does not exist.")
            return
        payload = {"content": content, "post_id": post_id, "user_id": user_id}
        new_comment = add_data("/comments/", payload)
        if new_comment:
            messagebox.showinfo(
                "Success", f"Comment added with ID {new_comment.get('id')}"
            )
            self.refresh_comments()

    def refresh_all(self):
        data_store.refresh_all()
        self.populate_posts()
        self.populate_users()
        self.refresh_comments()


class App(tk.Tk):
    def __init__(self, data_store):
        super().__init__()
        self.title("FastAPI Client")
        self.geometry("800x600")
        self.data_store = data_store
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        users_tab = UsersTab(notebook, self.data_store)
        posts_tab = PostsTab(notebook, self.data_store)
        comments_tab = CommentsTab(notebook, self.data_store)
        notebook.add(users_tab, text="Users")
        notebook.add(posts_tab, text="Posts")
        notebook.add(comments_tab, text="Comments")


if __name__ == "__main__":
    data_store.refresh_all() 
    app = App(data_store)
    app.mainloop()
