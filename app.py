import hashlib
import re
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector as mariadb
import config
import functions
import datetime

# Database connection
db = mariadb.connect(user="root", password=config.password, host="localhost", port="3306", database="127project")
cursor = db.cursor()

class Project(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.title("127 Project")
        
        self.user_id = None
        self.userName = None
        self.history = []
        self.selected_review_id = None
        self.selected_establishment_id = None
        self.selected_food_item_id = None
        self.establishmentName = None
        self.foodItemName = None
        self.selected_food_id = None


        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        self.show_frame(LoginPage)
    
    def show_frame(self, frame_class):
        if self.frames.get(frame_class) is None:
            frame = frame_class(parent=self.container, controller=self)
            self.frames[frame_class] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        if self.history and self.history[-1] != frame_class:
            self.history.append(frame_class)
        elif not self.history:
            self.history.append(frame_class)

        frame = self.frames[frame_class]
        frame.tkraise()

    def set_user(self, user_id, userName):
        self.user_id = user_id
        self.userName = userName
        
    def back(self):
        if len(self.history) > 1:
            self.history.pop()
            previous_page = self.history[-1]
            self.show_frame(previous_page)
#------------------------------------------------- GENERAL ---------------------------------------------------------------

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ttk.Label(self, text="Login", font=("Arial", 18))
        username = ttk.Label(self, text="Username")
        self.usernameEntry = ttk.Entry(self)
        password = ttk.Label(self, text="Password")
        self.passwordEntry = ttk.Entry(self, show="*")
        loginButton = ttk.Button(self, text="Login", command=self.login)
        notAUser = ttk.Label(self, text="No account yet?")
        signupButton = ttk.Button(self, text="Sign Up", command=lambda: self.controller.show_frame(SignUpPage))

        widgets = [label, username, self.usernameEntry, password, self.passwordEntry, loginButton, notAUser, signupButton]
        functions.apply_grid_settings(widgets, self)

    def login(self):
        username = self.usernameEntry.get()
        password = self.passwordEntry.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return

        cursor.execute("SELECT userid, password, name, IsOwner FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and user[1] == functions.hash_password(password):
            user_id, hashedPassword, name, is_owner = user
            self.controller.set_user(user_id, username)
            if is_owner:
                self.controller.show_frame(OwnerHomepage)
            else:
                self.controller.show_frame(CustomerHomepage)
        else:
            messagebox.showerror("Error", "Incorrect username or password")


class SignUpPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ttk.Label(self, text="Sign Up", font=("Verdana", 18))
        name = ttk.Label(self, text="Name")
        self.nameEntry = ttk.Entry(self)
        username = ttk.Label(self, text="Username")
        self.usernameEntry = ttk.Entry(self)
        password = ttk.Label(self, text="Password")
        self.passwordEntry = ttk.Entry(self, show="*")
        userTypeLabel = ttk.Label(self, text="Sign up as:")
        self.userType = tk.StringVar()
        customerButton = ttk.Radiobutton(self, text="Customer", variable=self.userType, value="Customer")
        ownerButton = ttk.Radiobutton(self, text="Owner", variable=self.userType, value="Owner")
        signupButton = ttk.Button(self, text="Sign Up", command=self.signup)
        backButton = ttk.Button(self, text="Back to Login", command=self.back_to_login)

        # Add validation to entries
        self.nameEntry.bind('<KeyRelease>', self.validate_length)
        self.usernameEntry.bind('<KeyRelease>', self.validate_length)
        self.passwordEntry.bind('<KeyRelease>', self.validate_length)

        widgets = [
            label, name, self.nameEntry, username, self.usernameEntry, password, self.passwordEntry, 
            userTypeLabel, customerButton, ownerButton, signupButton, backButton
        ]
        functions.apply_grid_settings(widgets, self)

    def validate_length(self, event):
        max_length = 30
        widget = event.widget
        current_text = widget.get()
        if len(current_text) > max_length:
            widget.delete(0, tk.END)
            widget.insert(tk.END, current_text[:max_length])

    def signup(self):
        name = self.nameEntry.get()
        username = self.usernameEntry.get()
        password = self.passwordEntry.get()
        userType = self.userType.get()

        cursor = db.cursor()
        try:
            if not name or not username or not password or not userType:
                messagebox.showerror("Error", "All fields are required")
                return

            if userType == "Customer":
                isCustomer = True
                isOwner = False
            elif userType == "Owner":
                isCustomer = False
                isOwner = True

            # Getting Userid
            cursor.execute("SELECT MAX(UserId) FROM user")
            result = cursor.fetchone()
            if result and result[0]:
                user_id = result[0] + 1
            else:
                user_id = 1

            # Hashing Password
            hashedPassword = hashlib.sha256(password.encode()).hexdigest()

            cursor.execute("INSERT INTO user VALUES (%s, %s, %s, %s, %s, %s)", (user_id, name, username, hashedPassword, isCustomer, isOwner))
            db.commit()
            messagebox.showinfo("Success", f"Signed up as {userType}")
            self.clear_selection()
            self.controller.show_frame(LoginPage)
        except mariadb.Error as err:
            messagebox.showerror("Error", f"Error: {err}")
        finally:
            cursor.close()

    def clear_selection(self):
        self.userType.set("")
        self.nameEntry.delete(0, tk.END)
        self.usernameEntry.delete(0, tk.END)
        self.passwordEntry.delete(0, tk.END)

    def back_to_login(self):
        self.controller.frames[SignUpPage].clear_selection()
        self.controller.show_frame(LoginPage)

#------------------------------------------------- CUSTOMER ---------------------------------------------------------------
# Customer Homepage
class CustomerHomepage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        userName = self.controller.userName
        greeting = ttk.Label(self, text=f"Hi, {userName.upper()}!", font=("Verdana", 18), padding=10)
        reviewButton = ttk.Button(self, text="My Food Reviews", command=lambda: self.controller.show_frame(MyFoodReviews))
        establishmentButton = ttk.Button(self, text="Food Establishments", command=lambda: self.controller.show_frame(EstablishmentsList))
        foodButton = ttk.Button(self, text="Food Items", command=lambda: self.controller.show_frame(FoodItemsList))
        logout = ttk.Button(self, text="Log out", command=lambda: self.controller.show_frame(LoginPage))

        widgets = [greeting, reviewButton, establishmentButton, foodButton, logout]
        functions.apply_grid_settings(widgets, self)

###################### FOOD REVIEWS BUTTON ########################################
# Customer Food Reviews
class MyFoodReviews(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        userName = self.controller.userName
        label = ttk.Label(self, text=f"{userName.upper()}'s Food Reviews", font=("Verdana", 18), padding=10)
        establishmentReviews = ttk.Button(self, text="Establishment Reviews", command= lambda: self.controller.show_frame(ViewListMyEstablishmentReviews))
        foodItemReviews = ttk.Button(self, text="Food Item Reviews", command= lambda: self.controller.show_frame(ViewListMyFoodItemReviews))
        backButton = ttk.Button(self, text="Go back", command=lambda: self.controller.show_frame(CustomerHomepage))
        
        widgets = [label, establishmentReviews, foodItemReviews, backButton]
        functions.apply_grid_settings(widgets, self)

# View List of My Establishment Reviews
class ViewListMyEstablishmentReviews(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.review_ids = {}
        self.build_ui()

    def build_ui(self):
        userName = self.controller.userName
        label = ttk.Label(self, text=f"{userName.upper()}'s Food Establishment Reviews", font=("Verdana", 18), padding=10)
        
        # Position the label at the top center
        label.place(relx=0.5, rely=0.1, anchor="center")

        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = tk.Frame(self, width=50, height=10)

        # Create a Listbox
        self.review_listbox = tk.Listbox(listbox_frame)

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.review_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.review_listbox.yview)

        # Use grid for Listbox and Scrollbar
        self.review_listbox.grid(row=0, column=0, sticky="nswe")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Use grid for listbox frame
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=20, pady=10)

        # Bind the Listbox select event
        self.review_listbox.bind('<<ListboxSelect>>', self.on_review_select)

        # Create the back button
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        backButton.place(relx=0.5, rely=0.9, anchor="center")

        # Configure grid for the entire frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Place the listbox frame in the center
        listbox_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.6)

        self.load_reviews()

    def load_reviews(self):
        # Ensure that user_id is not None
        if self.controller.user_id is not None:
            cursor.execute("SELECT reviewID, comment FROM review WHERE userid = %s AND foodID IS NULL", (self.controller.user_id,))
            reviews = cursor.fetchall()
            self.review_listbox.delete(0, tk.END) 
            self.review_ids.clear() 
            if not reviews:
                self.review_listbox.insert(tk.END, "No reviews yet")
            else:
                for index, (reviewid, comment) in enumerate(reviews):
                    self.review_listbox.insert(tk.END, comment)
                    self.review_ids[index] = reviewid  

    def on_review_select(self, event):
        selected_index = self.review_listbox.curselection()
        if selected_index:
            # If there is at least 1 review
            selected_item = self.review_listbox.get(selected_index[0])
            if selected_item != "No reviews yet":
                reviewid = self.review_ids[selected_index[0]]
                self.controller.selected_review_id = reviewid 
                self.controller.show_frame(ViewMyEstablishmentReview)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.load_reviews()

# View My Food Establishment Review
class ViewMyEstablishmentReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        # Display existing review
        self.review_details_text = tk.Text(self, wrap=tk.WORD, width=50, height=10)
        # Display the rating
        self.rating_label = ttk.Label(self, text="Rating: ", font=("Verdana", 12), padding=5)
        # Update -> UpdateEstablishmentReview
        updateButton = ttk.Button(self, text="Update Review", command= lambda: self.controller.show_frame(UpdateEstablishmentReview))
        # Delete
        deleteButton = ttk.Button(self, text="Delete Review", command=self.delete_review)
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        
        widgets = [self.label, self.review_details_text, self.rating_label, updateButton, deleteButton, backButton]
        functions.apply_grid_settings(widgets, self)

    
    def load_review_details(self):
        review_id = self.controller.selected_review_id
        cursor.execute("SELECT reviewid, comment, rating FROM review WHERE reviewid = %s", (review_id,))
        review = cursor.fetchone()
        cursor.execute("SELECT EstablishmentID FROM review WHERE reviewid = %s", (review_id,))
        establishmentid = cursor.fetchone()
        cursor.execute("SELECT EstablishmentName FROM establishment WHERE EstablishmentID = %s", (establishmentid[0],))
        self.controller.establishmentName = cursor.fetchone()
        if review:
            reviewid, comment, rating = review
            self.label.config(text=f"Review ID: " + str(reviewid))
            self.review_details_text.delete(1.0, tk.END)
            self.review_details_text.insert(tk.END, comment)
            self.rating_label.config(text="Rating: " + str(rating))

    def delete_review(self):
        review_id = self.controller.selected_review_id
        cursor.execute("DELETE FROM review WHERE reviewid = %s", (review_id,))
        db.commit()
        # Reset the selected_review_id to None
        self.controller.selected_review_id = None
        # Go back to the list of establishment reviews
        self.controller.show_frame(ViewListMyEstablishmentReviews)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_review_id:
            self.load_review_details()

# Update My Review
class UpdateEstablishmentReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_comment = None
        self.original_rating = None
        self.build_ui()

    def build_ui(self):
        estab = self.controller.establishmentName[0] if self.controller.establishmentName else "Unknown Establishment"
        self.label = ttk.Label(self, text=f"{estab}", font=("Verdana", 18), padding=10)
        
        # Likert scale for rating
        self.rating_scale = tk.Scale(self, from_=1, to=5, orient=tk.HORIZONTAL, label="Rating:", length=200)
        self.review_edit_text = tk.Text(self, wrap=tk.WORD, width=50, height=10)
        self.review_edit_text.bind('<KeyRelease>', self.validate_length)

        # Buttons
        save_button = ttk.Button(self, text="Save Changes", command=self.save_changes)
        back_button = ttk.Button(self, text="Cancel", command=self.controller.back)

        widgets = [self.label, self.rating_scale, self.review_edit_text, save_button, back_button]
        functions.apply_grid_settings(widgets, self)

    def validate_length(self, event):
        max_length = 255
        current_text = self.review_edit_text.get("1.0", tk.END)
        if len(current_text) > max_length:
            self.review_edit_text.delete("1.0", tk.END)
            self.review_edit_text.insert(tk.END, current_text[:max_length])

    
    def load_review_details(self):
        review_id = self.controller.selected_review_id
        cursor.execute("SELECT comment, rating FROM review WHERE reviewid = %s", (review_id,))
        review = cursor.fetchone()
        print(review)  # Add this line to check the retrieved review data
        if review:
            self.original_comment, self.original_rating = review  # Store the original comment and rating
            self.review_edit_text.delete(1.0, tk.END)
            self.review_edit_text.insert(tk.END, self.original_comment)  # Populate text widget with original comment
            self.rating_scale.set(self.original_rating)  # Set the scale value to the original rating


    def save_changes(self):
        review_id = self.controller.selected_review_id
        new_comment = self.review_edit_text.get(1.0, tk.END).strip()
        new_rating = self.rating_scale.get()  # Get the updated rating
        cursor.execute("UPDATE review SET comment = %s, rating = %s WHERE reviewid = %s", (new_comment, new_rating, review_id))
        db.commit()
        self.controller.back()
        self.controller.back()


    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        print("Updating Review Details...")
        if self.controller.selected_review_id:
            self.load_review_details()

# View List of My Food Item Reviews
class ViewListMyFoodItemReviews(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.review_ids = {}
        self.build_ui()

    def build_ui(self):
        userName = self.controller.userName
        label = ttk.Label(self, text=f"{userName.upper()}'s Food Item Reviews", font=("Verdana", 18), padding=10)
        
         # Position the label at the top center
        label.place(relx=0.5, rely=0.1, anchor="center")

        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = tk.Frame(self, width=50, height=10)

        # Create a Listbox
        self.review_listbox = tk.Listbox(listbox_frame)

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.review_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.review_listbox.yview)

        # Use grid for Listbox and Scrollbar
        self.review_listbox.grid(row=0, column=0, sticky="nswe")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Use grid for listbox frame
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=20, pady=10)

        # Bind the Listbox select event
        self.review_listbox.bind('<<ListboxSelect>>', self.on_review_select)

        # Create the back button
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)

        # Position the back button at the bottom center
        backButton.place(relx=0.5, rely=0.9, anchor="center")

        # Configure grid for the entire frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Place the listbox frame in the center
        listbox_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.6)

        self.load_reviews()
    
    def load_reviews(self):
       if self.controller.user_id is not None:
            cursor.execute("SELECT ReviewID, comment FROM review WHERE UserId = %s AND FoodID IS NOT NULL", (self.controller.user_id,))
            reviews = cursor.fetchall()
            self.review_listbox.delete(0, tk.END) 
            self.review_ids.clear() 
            if not reviews:
                self.review_listbox.insert(tk.END, "No reviews yet")
            else:
                for index, (reviewid, comment) in enumerate(reviews):
                    self.review_listbox.insert(tk.END, comment) 
                    self.review_ids[index] = reviewid  

    def on_review_select(self, event):
        selected_index = self.review_listbox.curselection()
        if selected_index:
            # If there is at least 1 review
            selected_item = self.review_listbox.get(selected_index[0])
            if selected_item != "No reviews yet":
                reviewid = self.review_ids[selected_index[0]]
                self.controller.selected_review_id = reviewid 
                self.controller.show_frame(ViewMyFoodItemReview)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.load_reviews()

# View My Food Item Review
class ViewMyFoodItemReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        # Display existing review
        self.review_details_text = tk.Text(self, wrap=tk.WORD, width=50, height=10)
        # Display the rating
        self.rating_label = ttk.Label(self, text="Rating: ", font=("Verdana", 12), padding=5)
        # Update; no function yet; -> UpdateEstablishmentReview
        updateButton = ttk.Button(self, text="Update Review", command= lambda:self.controller.show_frame(UpdateFoodItemReview))
        # Delete; no function yet
        deleteButton = ttk.Button(self, text="Delete Review", command=self.delete_review)
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        
        widgets = [self.label, self.review_details_text,self.rating_label, updateButton, deleteButton, backButton]
        functions.apply_grid_settings(widgets, self)
    
    def load_review_details(self):
        review_id = self.controller.selected_review_id
        cursor.execute("SELECT reviewid, comment, rating FROM review WHERE ReviewId = %s", (review_id,))
        review = cursor.fetchone()
        cursor.execute("SELECT FoodID FROM review WHERE ReviewId = %s", (review_id,))
        foodItem = cursor.fetchone()
        cursor.execute("SELECT Name FROM foodItem WHERE FoodID = %s", (foodItem[0],))
        self.controller.foodItemName = cursor.fetchone()
        if review:
            reviewid, comment, rating = review
            self.label.config(text="Review ID: "+str(reviewid))
            self.review_details_text.delete(1.0, tk.END)
            self.review_details_text.insert(tk.END, comment)
            self.rating_label.config(text="Rating: " + str(rating))

    def delete_review(self):
        review_id = self.controller.selected_review_id
        cursor.execute("DELETE FROM review WHERE reviewid = %s", (review_id,))
        db.commit()
        # Reset the selected_review_id to None
        self.controller.selected_review_id = None
        # Go back to the list of establishment reviews
        self.controller.show_frame(ViewListMyFoodItemReviews)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_review_id:
            self.load_review_details()

# Update Food Review
class UpdateFoodItemReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_comment = None
        self.original_rating = None
        self.build_ui()

    def build_ui(self):
        food = self.controller.foodItemName[0] if self.controller.foodItemName else "Unknown Food"
        self.label = ttk.Label(self, text=f"{food}", font=("Verdana", 18), padding=10)
        
        # Likert scale for rating
        self.rating_scale = tk.Scale(self, from_=1, to=5, orient=tk.HORIZONTAL, label="Rating:", length=200)
        self.review_edit_text = tk.Text(self, wrap=tk.WORD, width=50, height=10)
        self.review_edit_text.bind('<KeyRelease>', self.validate_length)

        # Buttons
        save_button = ttk.Button(self, text="Save Changes", command=self.save_changes)
        back_button = ttk.Button(self, text="Cancel", command=self.controller.back)

        widgets = [self.label, self.rating_scale, self.review_edit_text, save_button, back_button]
        functions.apply_grid_settings(widgets, self)

    def validate_length(self, event):
        max_length = 255
        current_text = self.review_edit_text.get("1.0", tk.END)
        if len(current_text) > max_length:
            self.review_edit_text.delete("1.0", tk.END)
            self.review_edit_text.insert(tk.END, current_text[:max_length])
    
    def load_review_details(self):
        review_id = self.controller.selected_review_id
        cursor.execute("SELECT comment, rating FROM review WHERE reviewid = %s", (review_id,))
        review = cursor.fetchone()
        print(review)  # Add this line to check the retrieved review data
        if review:
            self.original_comment, self.original_rating = review  # Store the original comment and rating
            self.review_edit_text.delete(1.0, tk.END)
            self.review_edit_text.insert(tk.END, self.original_comment)  # Populate text widget with original comment
            self.rating_scale.set(self.original_rating)  # Set the scale value to the original rating


    def save_changes(self):
        review_id = self.controller.selected_review_id
        new_comment = self.review_edit_text.get(1.0, tk.END).strip()
        new_rating = self.rating_scale.get()  # Get the updated rating
        cursor.execute("UPDATE review SET comment = %s, rating = %s WHERE reviewid = %s", (new_comment, new_rating, review_id))
        db.commit()
        self.controller.back()
        self.controller.back()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        print("Updating Review Details...")
        if self.controller.selected_review_id:
            self.load_review_details()

############################# FOOD ESTABLISHMENTS BUTTON ############################################
# Establishments List
class EstablishmentsList(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.establishment_ids = {}
        self.build_ui()

    def build_ui(self):
        label = ttk.Label(self, text="All Food Establishments", font=("Verdana", 18), padding=10)
        label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = tk.Frame(self, width=50, height=10)

        # Create a Listbox
        self.establishment_listbox = tk.Listbox(listbox_frame)

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.establishment_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.establishment_listbox.yview)

        # Use grid for Listbox and Scrollbar
        self.establishment_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Use grid for listbox frame
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Bind the Listbox select event
        self.establishment_listbox.bind('<<ListboxSelect>>', self.on_establishment_select)

        # Create search box and button
        search_label = ttk.Label(self, text="Search Establishment:")
        # search_label.grid(row=1, column=0, pady=5, padx=10, sticky="w")
        self.search_entry = ttk.Entry(self)
        self.search_entry.grid(row=2, column=1, pady=5, padx=10)
        search_button = ttk.Button(self, text="Search", command=self.search_establishment)
        search_button.grid(row=3, column=1, pady=5, padx=10)

        # Create filter buttons
        all_button = ttk.Button(self, text="All Establishments", command=self.load_all_establishments)
        all_button.grid(row=5, column=0, pady=5, padx=10)
        high_rated_button = ttk.Button(self, text="High Rated (>= 4)", command=self.load_high_rated_establishments)
        high_rated_button.grid(row=5, column=1, pady=5, padx=10)

        # Create the back button
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        # backButton.grid(row=3, column=2, pady=5, padx=10, sticky="e")
        
        # Load food items into the Listbox
        self.load_all_establishments()
        widgets = [label, search_label, self.search_entry, search_button, all_button, high_rated_button, listbox_frame, backButton]
        functions.apply_grid_settings(widgets, self)
    
    def load_all_establishments(self):
        establishments = cursor.execute("SELECT EstablishmentID, EstablishmentName FROM establishment")
        establishments = cursor.fetchall()
        self.establishment_listbox.delete(0, tk.END)  # Clear the listbox first
        self.establishment_ids.clear()  # Clear the dictionary
        if not establishments:
            self.establishment_listbox.insert(tk.END, "No establishment to review yet")
        else:
            for index, (establishmentid, establishmentname) in enumerate(establishments):
                self.establishment_listbox.insert(tk.END, establishmentname)
                self.establishment_ids[index] = establishmentid  # Map the index to the review ID

    def load_high_rated_establishments(self):
        establishments = cursor.execute("""
            SELECT EstablishmentID, EstablishmentName
            FROM TopRatedEstablishments
            WHERE AverageRating >= 4
        """)
        establishments = cursor.fetchall()
        self.establishment_listbox.delete(0, tk.END)  # Clear the listbox first
        self.establishment_ids.clear()  # Clear the dictionary
        if not establishments:
            self.establishment_listbox.insert(tk.END, "No high rated establishment to review yet")
        else:
            for index, (establishmentid, establishmentname) in enumerate(establishments):
                self.establishment_listbox.insert(tk.END, establishmentname)
                self.establishment_ids[index] = establishmentid  # Map the index to the review ID

    def on_establishment_select(self, event):
        selected_index = self.establishment_listbox.curselection()
        if selected_index:
            # If there is at least 1 establishment
            selected_item = self.establishment_listbox.get(selected_index[0])
            if selected_item != "No establishment to review yet" and selected_item != "No high rated establishment to review yet":
                establishmentid = self.establishment_ids[selected_index[0]]
                self.controller.selected_establishment_id = establishmentid 
                self.controller.show_frame(ViewEstablishment)
    
    def search_establishment(self):
        search_query = self.search_entry.get().strip()
        if search_query:
            establishments = cursor.execute("SELECT EstablishmentID, EstablishmentName FROM establishment WHERE EstablishmentName LIKE %s", ('%' + search_query + '%',))
            establishments = cursor.fetchall()
            self.establishment_listbox.delete(0, tk.END)  # Clear the listbox first
            self.establishment_ids.clear()  # Clear the dictionary
            if not establishments:
                self.establishment_listbox.insert(tk.END, "No matching establishment found")
            else:
                for index, (establishmentid, establishmentname) in enumerate(establishments):
                    self.establishment_listbox.insert(tk.END, establishmentname)
                    self.establishment_ids[index] = establishmentid  # Map the index to the review ID
        else:
            self.load_all_establishments()


# Review Details
class ViewReviewDetails(tk.Toplevel):
    def __init__(self, parent, review_id, review_text, review_rating, reviewer_name, review_date):
        super().__init__(parent)
        self.title("Review Details")
        self.geometry("400x300")
        self.resizable(False, False)

        # Review ID
        review_id_label = ttk.Label(self, text="Review ID:")
        review_id_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        review_id_value = ttk.Label(self, text=review_id)
        review_id_value.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        # Review Text
        review_text_label = ttk.Label(self, text="Review Text:")
        review_text_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        review_text_value = tk.Text(self, wrap=tk.WORD, height=5, width=30)
        review_text_value.insert(tk.END, review_text)
        review_text_value.config(state='disabled')
        review_text_value.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        # Review Rating
        review_rating_label = ttk.Label(self, text="Rating:")
        review_rating_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        review_rating_value = ttk.Label(self, text=review_rating)
        review_rating_value.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        # Reviewer Name
        reviewer_name_label = ttk.Label(self, text="Reviewer:")
        reviewer_name_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        reviewer_name_value = ttk.Label(self, text=reviewer_name)
        reviewer_name_value.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        # Review Date
        review_date_label = ttk.Label(self, text="Date:")
        review_date_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        review_date_value = ttk.Label(self, text=review_date)
        review_date_value.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

        # Close Button
        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.grid(row=5, column=0, columnspan=2, pady=10)

# View Establishment
class ViewEstablishment(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.review_ids = {}
        self.build_ui()

    def build_ui(self):
        # Display existing establishment
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = ttk.Label(self, text="Establishment Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        contact_label = ttk.Label(self, text="Contact Number:")
        contact_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        rating_label = ttk.Label(self, text="Average Rating:")
        rating_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        reviews_label = ttk.Label(self, text="Food Establishment Reviews", font=("Verdana", 18), padding=10)
        # reviews_label.grid(row=5, column=0, pady=10, padx=10, sticky=tk.W)
        sort_label = ttk.Label(self, text="Filter by:")
        # sort_label.grid(row=6, column=0, pady=10, padx=5, sticky=tk.W)
        
        # Text Widgets
        self.establishment_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.establishment_contact_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_contact_text.grid(row=2, column=1, padx=10, pady=5)
        self.establishment_rating_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_rating_text.grid(row=3, column=1, padx=10, pady=5)

        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = ttk.Frame(self, height=10, width=10)
        listbox_frame.grid(row=6, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")

        # Create a Listbox
        self.review_listbox = tk.Listbox(listbox_frame)
        self.review_listbox.grid(row=0, column=0, sticky="nswe")

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.review_listbox.yview)
        self.review_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Buttons
        addButton = ttk.Button(self, text="Add Review", command=lambda: self.controller.show_frame(AddEstablishmentReview))
        addButton.grid(row=4, column=0, pady=10, padx=10)
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        backButton.grid(row=4, column=1, pady=10, padx=10)

        # Buttons for filtering reviews by month
        currentMonthButton = ttk.Button(self, text="Current Month", command=self.show_current_month_reviews)
        currentMonthButton.grid(row=6, column=1)
        previousMonthButton = ttk.Button(self, text="Previous Month", command=self.show_previous_month_reviews)
        previousMonthButton.grid(row=7, column=1)

        # Bind double click event to show review details
        self.review_listbox.bind('<Double-Button-1>', self.show_review_details)

        # Configure grid for the entire frame
        self.grid_rowconfigure(6, weight=1)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        widgets = [self.label, self.establishment_name_text, self.establishment_contact_text, self.establishment_rating_text, addButton, reviews_label, sort_label, currentMonthButton, previousMonthButton, listbox_frame, backButton]
        functions.apply_grid_settings(widgets, self)
    
    def load_establishment_details(self):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute("SELECT establishmentName, ContactNumber FROM establishment WHERE establishmentid = %s", (establishment_id,))
        establishment = cursor.fetchone()
        
        cursor.execute("""
            SELECT COALESCE(AVG(r.Rating), 0) AS AverageRating
            FROM review r
            WHERE r.EstablishmentId = %s
        """, (establishment_id,))
        average_rating = cursor.fetchone()[0]
        
        if establishment:
            EstablishmentName, ContactNumber = establishment
            self.label.config(text=EstablishmentName)
            
            # Enable, insert text, and disable the establishment name text widget
            self.establishment_name_text.config(state='normal')
            self.establishment_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_name_text.insert(tk.END, EstablishmentName)
            self.establishment_name_text.config(state='disabled')
            
            # Enable, insert text, and disable the establishment contact text widget
            self.establishment_contact_text.config(state='normal')
            self.establishment_contact_text.delete(1.0, tk.END) # Clear any existing text
            self.establishment_contact_text.insert(tk.END, ContactNumber)
            self.establishment_contact_text.config(state='disabled')

            # Enable, insert text, and disable the establishment rating text widget
            self.establishment_rating_text.config(state='normal')
            self.establishment_rating_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_rating_text.insert(tk.END, f"{average_rating:.2f}")
            self.establishment_rating_text.config(state='disabled')

    # List of establishment reviews
    def load_reviews(self, query):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute(query, (establishment_id,))
        reviews = cursor.fetchall()
        self.review_listbox.delete(0, tk.END) 
        self.review_ids.clear() 
        if not reviews:
            self.review_listbox.insert(tk.END, "No reviews yet")
        else:
            for index, (reviewid, comment) in enumerate(reviews):
                self.review_listbox.insert(tk.END, comment) 
                self.review_ids[index] = reviewid

    def show_current_month_reviews(self):
        # Query to select reviews made in the current month
        query = """
            SELECT ReviewID, Comment FROM review 
            WHERE YEAR(Date) = YEAR(CURRENT_DATE()) AND MONTH(Date) = MONTH(CURRENT_DATE()) 
                AND EstablishmentId = %s
        """
        self.load_reviews(query)

    def show_previous_month_reviews(self):
        # Query to select reviews made in the previous month
        query = """
            SELECT ReviewID, Comment 
            FROM review 
            WHERE YEAR(Date) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) AND MONTH(Date) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
                AND EstablishmentId = %s
        """
        self.load_reviews(query)

    def show_review_details(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            review_id = self.review_ids.get(index)
            if review_id:
                cursor.execute("SELECT Comment, Rating, Name, Date FROM review r join user u on r.UserID = u.UserID WHERE ReviewID = %s", (review_id,))
                result = cursor.fetchone()
                if result:
                    comment, rating, name, date = result  # Unpack values
                    review_details_popup = ViewReviewDetails(self, review_id, comment, rating, name, date)
                    review_details_popup.grab_set()


    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_establishment_id:
            self.load_establishment_details()
            self.load_reviews("SELECT ReviewID, Comment FROM review WHERE EstablishmentId = %s")

# Add Establishment Review
class AddEstablishmentReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_rating = 1
        self.build_ui()

    def build_ui(self):
        label = ttk.Label(self, text="Add Establishment Review", font=("Verdana", 18), padding=10)
        
        # Establishment Review Form Fields
        establishmentReview = ttk.Label(self, text="Comment:")
        self.establishmentReviewEntry = tk.Text(self, width=40, height=10)  # Updated to tk.Text for multi-line input
        self.establishmentReviewEntry.bind('<KeyRelease>', self.validate_length)
        self.rating_scale = tk.Scale(self, from_=1, to=5, orient=tk.HORIZONTAL, label="Rating:", length=200)

        # Buttons
        submitButton = ttk.Button(self, text="Submit", command=self.addEstablishmentReviewToDb)
        backButton = ttk.Button(self, text="Cancel", command=self.controller.back)
        
        widgets = [label, establishmentReview, self.establishmentReviewEntry, self.rating_scale, submitButton, backButton]
        functions.apply_grid_settings(widgets, self)

    def validate_length(self, event):
        max_length = 255
        current_text = self.establishmentReviewEntry.get("1.0", tk.END)
        if len(current_text) > max_length:
            self.establishmentReviewEntry.delete("1.0", tk.END)
            self.establishmentReviewEntry.insert(tk.END, current_text[:max_length])

    def addEstablishmentReviewToDb(self):
        review = self.establishmentReviewEntry.get("1.0", tk.END) # Get multi-line input from tk.Text
        rating = self.rating_scale.get()
        user_id = self.controller.user_id
        establishment_id = self.controller.selected_establishment_id
        food_id = None

        cursor = db.cursor()
        try:
            cursor.execute("SELECT MAX(ReviewId) FROM review")
            result = cursor.fetchone()
            if result and result[0]:
                establishmentReview_id = result[0] + 1
            else:
                establishmentReview_id = 1
            
            if not rating:
                messagebox.showerror("Error", "rating field is required")
                return
            
            cursor.execute(
                "INSERT INTO review (ReviewId, Comment, Rating, UserId, EstablishmentId, FoodId) VALUES (%s, %s, %s, %s, %s, %s)", 
                (establishmentReview_id, review, rating, user_id, establishment_id, food_id)
            )
            db.commit()
            cursor.close()
            messagebox.showinfo("Success", "Establishment Review added successfully!")
            
            # Reset the form fields
            self.establishmentReviewEntry.delete("1.0", tk.END)
            self.rating_scale.set(self.original_rating)  # Reset the scale to the original rating

            self.back_to_ViewEstablishment()
        except mariadb.Error as err:
            messagebox.showerror("Error", f"Error: {err}")
        finally:
            cursor.close()


    def back_to_ViewEstablishment(self):
        self.controller.frames[ViewEstablishment].load_establishment_details()  # Ensure the list is reloaded
        self.controller.back()


#################################### FOOD ITEMS LIST #########################################
# Food Items List
class FoodItemsList(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.food_item_ids = {}
        self.build_ui()

    def build_ui(self):
        label = ttk.Label(self, text="All Food Items", font=("Verdana", 18), padding=10)
        label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Labels
        food_item = ttk.Label(self, text="Food Item Name:")
        food_item.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        name = ttk.Label(self, text="Establishment Name:")
        name.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)       
        type = ttk.Label(self, text="Food type:")
        type.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        minprice = ttk.Label(self, text="Minimum price: ")
        minprice.grid(row=4, column=0, pady=10, padx=10, sticky=tk.W)
        maxprice = ttk.Label(self, text="Maximum price: ")
        maxprice.grid(row=5, column=0, pady=10, padx=10, sticky=tk.W)
        
        # Sort by price
        sort_by_price = ttk.Label(self, text="Sort by: ")
        sort_by_price.grid(row=6, column=0, pady=10, padx=10, sticky=tk.W)

        # Dropdown for Sorting
        # Dropdown for Sorting by Price
        self.sort_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(self, textvariable=self.sort_var, values=["Ascending Price", "Descending Price"])
        self.sort_combobox.grid(row=6, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Dropdown for Establishment Name
        self.establishmentid_var = tk.StringVar()
        self.establishmentid_combobox = ttk.Combobox(self, textvariable=self.establishmentid_var)
        self.establishmentid_combobox.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Dropdown for Food Type
        self.type_var = tk.StringVar()
        self.food_type_combobox = ttk.Combobox(self, textvariable=self.type_var)
        self.food_type_combobox.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Validate function for numeric input
        def validate_numeric_input(P):
            if P.isdigit() or P == "":
                return True
            return False

        vcmd = (self.register(validate_numeric_input), '%P')
        
        # Entries for Minimum and Maximum Price
        self.minprice_var = tk.StringVar()
        self.minprice_entry = ttk.Entry(self, textvariable=self.minprice_var, validate='key', validatecommand=vcmd)
        self.minprice_entry.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        self.maxprice_var = tk.StringVar()
        self.maxprice_entry = ttk.Entry(self, textvariable=self.maxprice_var, validate='key', validatecommand=vcmd)
        self.maxprice_entry.grid(row=5, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Entry for food item name
        self.food_item_var = tk.StringVar()
        self.food_item_entry = ttk.Entry(self, textvariable=self.food_item_var)
        self.food_item_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Filter Button
        filterButton = ttk.Button(self, text="Search", command=self.filter_food_items)
        
        # Reset Button
        resetButton = ttk.Button(self, text="Reset", command=self.reset_filters)
        
        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = tk.Frame(self, width=50, height=10)

        # Create a Listbox
        self.food_item_listbox = tk.Listbox(listbox_frame)

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.food_item_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.food_item_listbox.yview)

        # Use grid for Listbox and Scrollbar
        self.food_item_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Use grid for listbox frame
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Bind the Listbox select event
        self.food_item_listbox.bind('<<ListboxSelect>>', self.on_food_item_select)

        # Create the back button
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)

        # Load food items into the Listbox
        self.load_food_items()
        
        # Load establishment IDs into the Combobox
        self.load_establishment_ids()
        
        # Load types into the Combobox
        self.load_food_types()

        # Apply grid settings to all widgets
        widgets = [label, food_item, name, type, minprice, maxprice, sort_by_price, filterButton, resetButton, listbox_frame, backButton]
        functions.apply_grid_settings(widgets, self)
        
    def load_food_items(self):
        food_items = functions.fetch_all_food_items_list()
        self.food_item_listbox.delete(0, tk.END)  # Clear the listbox first
        self.food_item_ids.clear() # Clear the dictionary
        if not food_items:
            self.food_item_listbox.insert(tk.END, "No food item to review yet")
        else:
            for index, (food_itemid, name) in enumerate(food_items):
                self.food_item_listbox.insert(tk.END, name)
                self.food_item_ids[index] = food_itemid  # Map the index to the review ID

    def reset_filters(self):
        # Clear dropdown menus
        self.establishmentid_var.set('')
        self.type_var.set('')
        self.sort_var.set('')

        # Clear price fields
        self.minprice_var.set('')
        self.maxprice_var.set('')
        self.food_item_var.set('')

        # Reload food items
        self.load_food_items()
    
    def load_establishment_ids(self):
        # Fetch establishment IDs and names from the database
        establishments = functions.fetch_all_estabs_list()
        establishment_names = [name for _, name in establishments]
        if establishment_names:
            self.establishmentid_combobox['values'] = establishment_names
        else:
            self.establishmentid_combobox['values'] = ["No establishments available"]

    def load_food_types(self):
        # Fetch food types from the database
        types = functions.fetch_all_food_types()
        if types:
            self.food_type_combobox['values'] = types
        else:
            self.food_type_combobox['values'] = ["No food types available"]

    def on_food_item_select(self, event):
        selected_index = self.food_item_listbox.curselection()
        if selected_index:
            # If there is at least 1 review
            selected_item = self.food_item_listbox.get(selected_index[0])
            if selected_item != "No food item to view yet":
                fooditemid = self.food_item_ids[selected_index[0]]
                self.controller.selected_food_id = fooditemid 
                self.controller.show_frame(ViewFoodItem)
                
    def filter_food_items(self):
        selected_food_item = self.food_item_var.get()
        selected_establishment = self.establishmentid_var.get()
        selected_type = self.type_var.get()
        min_price = self.minprice_var.get()
        max_price = self.maxprice_var.get()
        sort_order = self.sort_var.get()

        query = "SELECT foodid, name FROM foodItemsAndEstabName WHERE 1=1"
        params = []

        if selected_food_item:
            query += " AND name LIKE %s"
            params.append(f"%{selected_food_item}%")

        if selected_establishment:
            query += " AND establishmentname = %s"
            params.append(selected_establishment)

        if selected_type:
            query += " AND type = %s"
            params.append(selected_type)

        if min_price:
            query += " AND price >= %s"
            params.append(min_price)

        if max_price:
            query += " AND price <= %s"
            params.append(max_price)
            
        if sort_order == "Ascending Price":
            query += " ORDER BY price ASC"
        elif sort_order == "Descending Price":
            query += " ORDER BY price DESC"

        results = cursor.execute(query, params)
        results = cursor.fetchall()

        self.food_item_listbox.delete(0, tk.END)  # Clear the listbox first
        self.food_item_ids.clear()  # Clear the dictionary
        if not results:
            self.food_item_listbox.insert(tk.END, "No food items match the criteria")
        else:
            print(results)
            for index, (food_itemid, name) in enumerate(results):
                    self.food_item_listbox.insert(tk.END, name)
                    self.food_item_ids[index] = food_itemid  # Map the index to the food item ID
        
# View Food Item
class ViewFoodItem(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.review_ids = {}
        self.build_ui()

    def build_ui(self):
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = tk.Label(self, text="Food Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        description_label = tk.Label(self, text="Description:")
        description_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        price_label = tk.Label(self, text="Price:")
        price_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        type_label = tk.Label(self, text="Type:")
        type_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        reviews_label = ttk.Label(self, text="Food Item Reviews", font=("Verdana", 18), padding=10)
        rating_label = tk.Label(self, text="Rating:")
        rating_label.grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        sort_label = ttk.Label(self, text="Filter by:")

        # Text Widgets
        self.food_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.food_description_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_description_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_price_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_price_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_type_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_type_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_rating_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_rating_text.grid(row=5, column=1, padx=10, pady=5)

        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)

        # Create a frame to contain the Listbox and the Scrollbar
        listbox_frame = ttk.Frame(self)
        listbox_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")

        # Create a Listbox
        self.review_listbox = tk.Listbox(listbox_frame)
        self.review_listbox.grid(row=0, column=0, sticky="nswe")

        # Create a Scrollbar and attach it to the Listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.review_listbox.yview)
        self.review_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Make the listbox frame expandable
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Bind double click event to show review details
        self.review_listbox.bind('<Double-Button-1>', self.show_review_details)

        # Buttons for filtering reviews by month
        currentMonthButton = ttk.Button(self, text="Current Month", command=self.show_current_month_reviews)
        currentMonthButton.grid(row=8, column=1)
        previousMonthButton = ttk.Button(self, text="Previous Month", command=self.show_previous_month_reviews)
        previousMonthButton.grid(row=9, column=1)

        # Buttons
        add_button = ttk.Button(self, text="Add Review", command=lambda: self.controller.show_frame(AddFoodItemReview))
        add_button.grid(row=10, column=0, pady=10, padx=10)
        back_button = ttk.Button(self, text="Go back", command=self.controller.back)
        back_button.grid(row=10, column=1, pady=10, padx=10)

        # Configure grid for the entire frame
        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        widgets = [self.label, self.food_name_text, self.food_description_text, self.food_price_text, self.food_type_text, self.food_rating_text, add_button, reviews_label, sort_label, currentMonthButton, previousMonthButton, listbox_frame, back_button]
        functions.apply_grid_settings(widgets, self)

    def load_food_item_details(self):
        food_id = self.controller.selected_food_id
        cursor = db.cursor()

        # Fetch food item details and average rating
        cursor.execute("SELECT Name, Description, Price, Type FROM foodItem WHERE FoodId = %s", (food_id,))
        food_item = cursor.fetchone()

        cursor.execute("""
            SELECT COALESCE(AVG(r.Rating), 0) AS AverageRating
            FROM review r
            WHERE r.FoodId = %s
        """, (food_id,))
        Rating = cursor.fetchone()[0]
        print(food_item)
        if food_item:
            Name, Description, Price, Type = food_item
            self.label.config(text=Name)
            # Enable, insert text, and disable the food name text widget
            self.food_name_text.config(state='normal')
            self.food_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_name_text.insert(tk.END, Name)
            self.food_name_text.config(state='disabled')
            
            # Enable, insert text, and disable the food description text widget
            self.food_description_text.config(state='normal')
            self.food_description_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_description_text.insert(tk.END, Description)
            self.food_description_text.config(state='disabled')

            # Enable, insert text, and disable the food price text widget
            self.food_price_text.config(state='normal')
            self.food_price_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_price_text.insert(tk.END, Price)
            self.food_price_text.config(state='disabled')

            # Enable, insert text, and disable the food price text widget
            self.food_type_text.config(state='normal')
            self.food_type_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_type_text.insert(tk.END, Type)
            self.food_type_text.config(state='disabled')

            # Enable, insert text, and disable the food rating text widget
            self.food_rating_text.config(state='normal')
            self.food_rating_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_rating_text.insert(tk.END, str(Rating))
            self.food_rating_text.config(state='disabled')
    # List of food item reviews
    def load_reviews(self, query):
        food_id = self.controller.selected_food_id
        cursor.execute(query, (food_id,))       
        # cursor.execute("SELECT EstablishmentId FROM foodItem WHERE FoodId = %s", (food_id,))
        # establishment_id = cursor.fetchone()[0]
        # cursor.execute("SELECT reviewID, comment FROM review WHERE foodID = %s AND EstablishmentId = %s", (food_id, establishment_id,))
        reviews = cursor.fetchall()
        self.review_listbox.delete(0, tk.END) 
        self.review_ids.clear() 
        if not reviews:
            self.review_listbox.insert(tk.END, "No reviews yet")
        else:
            for index, (reviewid, comment) in enumerate(reviews):
                self.review_listbox.insert(tk.END, comment) 
                self.review_ids[index] = reviewid

    def show_current_month_reviews(self):
    # Query to select reviews made in the current month for the specific food item
        query = """
            SELECT ReviewID, Comment 
            FROM review 
            WHERE YEAR(Date) = YEAR(CURRENT_DATE()) AND MONTH(Date) = MONTH(CURRENT_DATE()) 
                AND FoodID = %s
        """
        self.load_reviews(query)

    def show_previous_month_reviews(self):
        # Query to select reviews made in the previous month for the specific food item
        query = """
            SELECT ReviewID, Comment 
            FROM review 
            WHERE YEAR(Date) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) AND MONTH(Date) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) 
                AND FoodID = %s
        """
        self.load_reviews(query)

    def show_review_details(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            review_id = self.review_ids.get(index)
            if review_id:
                cursor.execute("SELECT Comment, Rating, Name, Date FROM review r join user u on r.UserID = u.UserID WHERE ReviewID = %s", (review_id,))
                result = cursor.fetchone()
                if result:
                    comment, rating, name, date = result  # Unpack values
                    review_details_popup = ViewReviewDetails(self, review_id, comment, rating, name, date)
                    review_details_popup.grab_set()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_food_id:
            self.load_food_item_details()
            self.load_reviews("SELECT ReviewID, Comment FROM review WHERE FoodID = %s")

# Add Food Item Review
class AddFoodItemReview(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.original_rating = 1
        self.build_ui()

    def build_ui(self):
        label = ttk.Label(self, text="Add Food Review", font=("Verdana", 18), padding=10)
        
        # Food Item Review Form Fields
        foodReview = ttk.Label(self, text="Comment:")
        self.foodReviewEntry = tk.Text(self, wrap=tk.WORD, width=50, height=10)
        self.foodReviewEntry.bind('<KeyRelease>', self.validate_length)
        self.rating_scale = tk.Scale(self, from_=1, to=5, orient=tk.HORIZONTAL, label="Rating:", length=200)

        # Buttons
        submitButton = ttk.Button(self, text="Submit", command=self.addFoodReviewToDb)
        backButton = ttk.Button(self, text="Cancel", command=self.controller.back)
        
        widgets = [label, foodReview, self.foodReviewEntry, self.rating_scale, submitButton, backButton]
        functions.apply_grid_settings(widgets, self)

    def validate_length(self, event):
        max_length = 255
        current_text = self.foodReviewEntry.get("1.0", tk.END)
        if len(current_text) > max_length:
            self.foodReviewEntry.delete("1.0", tk.END)
            self.foodReviewEntry.insert(tk.END, current_text[:max_length])

    def addFoodReviewToDb(self):
        review = self.foodReviewEntry.get("1.0", tk.END)
        rating = self.rating_scale.get()
        user_id = self.controller.user_id
        food_id = self.controller.selected_food_id
        
        cursor = db.cursor()
        try: 
            cursor.execute("SELECT MAX(ReviewId) FROM review")
            result = cursor.fetchone()
            if result and result[0]:
                foodReview_id = result[0] + 1
            else:
                foodReview_id =  1
            
            # getting EstablishmentId of the food item        
            cursor.execute("SELECT EstablishmentId FROM foodItem WHERE FoodId = %s", (food_id,))
            establishment_id = cursor.fetchone()
            if establishment_id:
                establishment_id = establishment_id[0]
            else:
                messagebox.showerror("Error", "Unable to retrieve establishment ID")
                return
            
            # rating constraint
            if not rating:
                messagebox.showerror("Error", "rating field is required")
                return

            cursor.execute(
                "INSERT INTO review (ReviewId, Comment, Rating, UserId, EstablishmentId, FoodId) VALUES (%s, %s, %s, %s, %s, %s)", 
                (foodReview_id, review, rating, user_id, establishment_id, food_id)
            )
            db.commit()
            cursor.close()
            messagebox.showinfo("Success", "Food Review added successfully!")

            # Reset the form fields
            self.foodReviewEntry.delete("1.0", tk.END)  # Clear the text entry
            self.rating_scale.set(self.original_rating)  # Reset the scale to the original rating

            self.back_to_ViewFoodItem()
        except mariadb.Error as err:
            messagebox.showerror("Error", f"Error: {err}") 
        finally:
            cursor.close()

    def back_to_ViewFoodItem(self):
        self.controller.frames[ViewFoodItem].load_food_item_details()  # Ensure the list is reloaded
        self.controller.show_frame(ViewFoodItem)


#--------------O----W----N----E----R-----------S----C----R----E----E----N----S-----------------#

class OwnerHomepage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.establishment_ids = {}
        self.build_ui()

    def build_ui(self):
        userName = self.controller.userName
        greeting = ttk.Label(self, text=f"Hi, {userName.upper()}!", font=("Verdana", 18), padding=10)

        label = ttk.Label(self, text="Establishments", font=("Verdana", 18), padding=10)
        self.establishment_listbox = tk.Listbox(self, width=100)
        self.establishment_listbox.bind('<<ListboxSelect>>', self.on_establishment_select)

        addEstablishmentButton = ttk.Button(self, text="Add Establishment", command=self.add_establishment)
        logout = ttk.Button(self, text="Log out", command=lambda: self.controller.show_frame(LoginPage))

        widgets = [greeting, label, self.establishment_listbox, addEstablishmentButton, logout]
        functions.apply_grid_settings(widgets, self)

    def load_establishments(self):
        establishments = cursor.execute("SELECT EstablishmentId, EstablishmentName FROM establishment WHERE userid = %s", (self.controller.user_id,))
        establishments = cursor.fetchall()
        self.establishment_listbox.delete(0, tk.END)  # Clear the listbox first
        self.establishment_ids.clear()  # Clear the dictionary
        print(f"Loaded establishments: {establishments}")  # Debug print
        if not establishments:
            self.establishment_listbox.insert(tk.END, "No establishments yet")
        else:
            for index, (establishmentid, EstablishmentName) in enumerate(establishments):
                self.establishment_listbox.insert(tk.END, EstablishmentName)
                self.establishment_ids[index] = establishmentid  # Map the index to the review ID

    def on_establishment_select(self, event):
        selected_index = self.establishment_listbox.curselection()
        if selected_index:
            selected_item = self.establishment_listbox.get(selected_index[0])
            if selected_item != "No establishments yet":
                establishmentid = self.establishment_ids[selected_index[0]]
                self.controller.selected_establishment_id = establishmentid 
                self.controller.show_frame(ViewMyEstablishment)  

    def add_establishment(self):
        self.controller.show_frame(AddEstablishment)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.load_establishments()  # Ensure establishments are reloaded when this frame is raised

# add establishment
class AddEstablishment(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        label = ttk.Label(self, text="Add Establishment", font=("Arial", 18))

         # Labels
        name_label = tk.Label(self, text="Establishment Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)  
        contact_label = tk.Label(self, text="Contact Number:")
        contact_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)

        # Text Widgets
        self.establishment_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.establishment_name_text.bind('<KeyRelease>', self.validate_name_length)
        self.establishment_contact_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_contact_text.grid(row=2, column=1, padx=10, pady=5)
        self.establishment_contact_text.bind('<KeyRelease>', self.validate_contact_number)

        # Buttons
        submitButton = ttk.Button(self, text="Submit", command=self.addEstablishmentToDb)
        backButton = ttk.Button(self, text="Cancel", command=self.controller.back)

        widgets = [label, self.establishment_name_text, self.establishment_contact_text, submitButton, backButton]
        functions.apply_grid_settings(widgets, self)

    def validate_name_length(self, event):
        max_length = 50
        current_text = self.establishment_name_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.establishment_name_text.delete("1.0", tk.END)
            self.establishment_name_text.insert("1.0", current_text[:max_length])
        
    def validate_contact_number(self, event):
        pattern = r'^\d{0,11}$'  # Allows up to 11 digits
        current_text = self.establishment_contact_text.get("1.0", "end-1c")
        if not re.match(pattern, current_text):
            self.establishment_contact_text.delete("1.0", tk.END)
            filtered_text = re.sub(r'\D', '', current_text)[:11]
            self.establishment_contact_text.insert("1.0", filtered_text)

    def addEstablishmentToDb(self):
        name = self.establishment_name_text.get("1.0", tk.END)
        contactNum = self.establishment_contact_text.get("1.0", tk.END)
        user_id = self.controller.user_id

        try:
            cursor = db.cursor()

            #getting EstablishmentId
            cursor.execute("SELECT MAX(EstablishmentId) FROM establishment")
            result = cursor.fetchone()
            if result and result[0]:
                establishment_id = result[0] + 1
            else:
                establishment_id = 1 

            if not name or not contactNum:
                messagebox.showerror("Error", "All fields are required")
                return

            cursor.execute(
                "INSERT INTO establishment (EstablishmentId, EstablishmentName, ContactNumber, UserId) VALUES (%s, %s, %s, %s)", 
                (establishment_id, name, contactNum, user_id)
            )
            db.commit()
            cursor.close()
            messagebox.showinfo("Success", "Establishment added successfully!")
            self.establishment_name_text.delete("1.0", tk.END)
            self.establishment_contact_text.delete("1.0", tk.END)
            self.back_to_homepage()
        except mariadb.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def back_to_homepage(self):
        self.controller.frames[OwnerHomepage].load_establishments()  # Ensure the list is reloaded
        self.controller.show_frame(OwnerHomepage)
        
# View My Establishment details
class ViewMyEstablishment(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Display existing establishment
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = tk.Label(self, text="Establishment Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        contact_label = tk.Label(self, text="Contact Number:")
        contact_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        
        # Text Widgets
        self.establishment_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_name_text.grid(row=1, column=1, padx=10, pady=5)
        
        self.establishment_contact_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_contact_text.grid(row=2, column=1, padx=10, pady=5)
        
        # Buttons  
        update_button = ttk.Button(self, text="Edit Establishment", command=lambda: self.controller.show_frame(UpdateEstablishment))
        update_button.grid(row=4, column=0, padx=10, pady=5)
        
        delete_button = ttk.Button(self, text="Remove Establishment", command=self.remove_establishment)
        delete_button.grid(row=4, column=1, padx=10, pady=5)
        
        list_food_item_button = ttk.Button(self, text="List all food items", command=lambda: self.controller.show_frame(ViewListFoodItems))
        list_food_item_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        back_button = ttk.Button(self, text="Go back", command=self.controller.back)
        back_button.grid(row=6, column=0, columnspan=2, pady=10)
        
        widgets = [self.label, self.establishment_name_text, self.establishment_contact_text, update_button, delete_button, list_food_item_button, back_button]
        functions.apply_grid_settings(widgets, self)
    
    def load_establishment_details(self):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute("SELECT EstablishmentName, ContactNumber FROM establishment WHERE EstablishmentId = %s", (establishment_id,))
        establishment = cursor.fetchone()
        if establishment:
            EstablishmentName, ContactNumber = establishment
            self.label.config(text=EstablishmentName)
            # Enable, insert text, and disable the establishment name text widget
            self.establishment_name_text.config(state='normal')
            self.establishment_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_name_text.insert(tk.END, EstablishmentName)
            self.establishment_name_text.config(state='disabled')
            
            # Enable, insert text, and disable the establishment contact text widget
            self.establishment_contact_text.config(state='normal')
            self.establishment_contact_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_contact_text.insert(tk.END, ContactNumber)
            self.establishment_contact_text.config(state='disabled')

    def remove_establishment(self):
        establishment_id = self.controller.selected_establishment_id
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to remove this establishment?")
        if confirm:
            try:
                # Delete related records first
                cursor.execute("DELETE FROM fooditem WHERE EstablishmentID = %s", (establishment_id,))
                # Then delete the establishment
                cursor.execute("DELETE FROM establishment WHERE EstablishmentId = %s", (establishment_id,))
                db.commit()
                messagebox.showinfo("Success", "Establishment removed successfully.")
                # Navigate back to previous frame or perform any other necessary actions
                # For example:
                self.controller.back()
            except Exception as e:
                messagebox.showerror("Error", str(e))


    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_establishment_id:
            self.load_establishment_details()

# update establishment
class UpdateEstablishment(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Display existing establishment
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = tk.Label(self, text="Establishment Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)  
        contact_label = tk.Label(self, text="Contact Number:")
        contact_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        
        # Text Widgets
        self.establishment_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.establishment_name_text.bind('<KeyRelease>', self.validate_name_length)
        self.establishment_contact_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.establishment_contact_text.grid(row=2, column=1, padx=10, pady=5)
        self.establishment_contact_text.bind('<KeyRelease>', self.validate_contact_number)
        
        # Buttons  
        save_button = ttk.Button(self, text="Save", command=self.save_establishment)
        save_button.grid(row=4, column=0, padx=10, pady=5)
        back_button = ttk.Button(self, text="Cancel", command=self.controller.back)
        back_button.grid(row=4, column=1, padx=10, pady=5)
        
        widgets = [self.label, self.establishment_name_text, self.establishment_contact_text, save_button, back_button]
        functions.apply_grid_settings(widgets, self)

    def validate_name_length(self, event):
        max_length = 50
        current_text = self.establishment_name_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.establishment_name_text.delete("1.0", tk.END)
            self.establishment_name_text.insert("1.0", current_text[:max_length])
        
    def validate_contact_number(self, event):
        pattern = r'^\d{0,11}$'  # Allows up to 11 digits
        current_text = self.establishment_contact_text.get("1.0", "end-1c")
        if not re.match(pattern, current_text):
            self.establishment_contact_text.delete("1.0", tk.END)
            filtered_text = re.sub(r'\D', '', current_text)[:11]
            self.establishment_contact_text.insert("1.0", filtered_text)

    def load_establishment_details(self):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute("SELECT EstablishmentName, ContactNumber FROM establishment WHERE EstablishmentId = %s", (establishment_id,))
        establishment = cursor.fetchone()
        if establishment:
            EstablishmentName, ContactNumber = establishment
            self.label.config(text=EstablishmentName)
            # Enable, insert text, and disable the establishment name text widget
            self.establishment_name_text.config(state='normal')
            self.establishment_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_name_text.insert(tk.END, EstablishmentName)
            
            # Enable, insert text, and disable the establishment contact text widget
            self.establishment_contact_text.config(state='normal')
            self.establishment_contact_text.delete(1.0, tk.END)  # Clear any existing text
            self.establishment_contact_text.insert(tk.END, ContactNumber)
    
    def save_establishment(self):
        establishment_name = self.establishment_name_text.get("1.0", "end-1c")
        contact_number = self.establishment_contact_text.get("1.0", "end-1c")
        establishment_id = self.controller.selected_establishment_id
        
        # Update establishment in the database
        cursor.execute("UPDATE establishment SET EstablishmentName = %s, ContactNumber = %s WHERE EstablishmentId = %s", (establishment_name, contact_number, establishment_id))
        db.commit()
        
        # Notify user
        messagebox.showinfo("Success", "Establishment details updated successfully.")
        self.controller.back()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_establishment_id:
            self.load_establishment_details()

# View Food Items in My Establishment
class ViewListFoodItems(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.food_ids = {}
        self.build_ui()

    def build_ui(self):
        self.greeting = ttk.Label(self, text="", font=("Verdana", 18), padding=10)

        label = ttk.Label(self, text="Food Items", font=("Verdana", 18), padding=10)
        self.food_items_listbox = tk.Listbox(self, width=100)
        self.food_items_listbox.bind('<<ListboxSelect>>', self.on_food_item_select)
        
        # Buttons
        addFoodButton = ttk.Button(self, text="Add Food Item", command=lambda: self.controller.show_frame(AddFoodItem))
        backButton = ttk.Button(self, text="Go back", command=self.controller.back)
        
        widgets = [label, self.greeting, self.food_items_listbox, addFoodButton, backButton]
        functions.apply_grid_settings(widgets, self)
    
    def load_food_items(self):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute("SELECT EstablishmentName FROM establishment WHERE EstablishmentId = %s", (establishment_id,))
        establishment_name = cursor.fetchone()[0]  # Fetch the first result
        self.greeting.config(text=establishment_name)

        # display list of food items
        food_items = cursor.execute("Select FoodId, Name from foodItem WHERE EstablishmentId = %s and userid = %s", (establishment_id, self.controller.user_id,))
        food_items = cursor.fetchall()
        self.food_items_listbox.delete(0, tk.END)  # Clear the listbox first
        self.food_ids.clear()  # Clear the dictionary
        print(f"Loaded food items: {food_items}")  # Debug print
        if not food_items:
            self.food_items_listbox.insert(tk.END, "No food items yet")
        else:
            for index, (foodid, Name) in enumerate(food_items):
                self.food_items_listbox.insert(tk.END, Name)
                self.food_ids[index] = foodid  # Map the index to the review ID

    def on_food_item_select(self, event):
        selected_index = self.food_items_listbox.curselection()
        if selected_index:
            selected_item = self.food_items_listbox.get(selected_index[0])
            if selected_item != "No food items yet":
                foodid = self.food_ids[selected_index[0]]
                self.controller.selected_food_id = foodid 
                self.controller.show_frame(ViewMyFoodItem)  

    def add_establishment(self):
        self.controller.show_frame(AddFoodItem)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.load_food_items()
        
# adds food item to specific estab
class AddFoodItem(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Display Title
        self.establishment_name = ttk.Label(self, text="Add Food Item", font=("Arial", 18)) 

        # Labels
        name_label = tk.Label(self, text="Food Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        description_label = tk.Label(self, text="Description:")
        description_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        price_label = tk.Label(self, text="Price:")
        price_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        type_label = tk.Label(self, text="Type:")
        type_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)

        # Text Widgets
        self.food_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.food_name_text.bind('<KeyRelease>', self.validate_name_length)
        self.food_description_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_description_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_description_text.bind('<KeyRelease>', self.validate_description_length)
        self.food_price_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_price_text.grid(row=3, column=1, padx=10, pady=5)
        self.food_price_text.bind('<KeyRelease>', self.validate_price)
        self.food_type_text = tk.StringVar()
        self.food_type_text = ttk.Combobox(self, textvariable=self.food_type_text, state="readonly", width=28)  # Set width here
        self.food_type_text['values'] = ('Meat', 'Seafood', 'Vegetable', 'Fruit', 'Grains and Cereals', 'Sweets and Snacks', 'Nuts and Seeds', 'Beverages')
        self.food_type_text.grid(row=4, column=1, padx=10, pady=5)
		
		# Buttons
        submitButton = ttk.Button(self, text="Submit", command=self.addFoodToDb)
        backButton = ttk.Button(self, text="Cancel", command=self.controller.back)

        widgets = [self.establishment_name, self.food_name_text, self.food_description_text, self.food_price_text, self.food_type_text, submitButton, backButton]
        functions.apply_grid_settings(widgets, self)

    def validate_name_length(self, event):
        max_length = 50
        current_text = self.food_name_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.food_name_text.delete("1.0", tk.END)
            self.food_name_text.insert("1.0", current_text[:max_length])

    def validate_description_length(self, event):
        max_length = 100
        current_text = self.food_description_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.food_description_text.delete("1.0", tk.END)
            self.food_description_text.insert("1.0", current_text[:max_length])

    def validate_price(self, event):
        current_text = self.food_price_text.get("1.0", "end-1c")
        if not re.match(r'^(\d{1,10}(\.\d{0,2})?)?$', current_text):
            self.food_price_text.delete("1.0", tk.END)
            self.food_price_text.insert("1.0", current_text[:-1])

    def update_ui(self):
        establishment_id = self.controller.selected_establishment_id
        cursor.execute("SELECT EstablishmentName FROM establishment WHERE EstablishmentId = %s", (establishment_id,))
        establishment_name = cursor.fetchone()[0]  # Fetch the first result
        self.establishment_name.config(text=f"Add Food Item to {establishment_name}")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.update_ui()
		
	# called from submit button
    def addFoodToDb(self):
		# stores inputs from add food item form
        name = self.food_name_text.get("1.0", "end-1c")
        description = self.food_description_text.get("1.0", "end-1c")
        price = self.food_price_text.get("1.0", "end-1c")
        type = self.food_type_text.get()
		
		# Get IDs from the controller
        establishment_id = self.controller.selected_establishment_id
        user_id = self.controller.user_id
		
        try:
            cursor = db.cursor()

            #getting FoodId
            cursor.execute("SELECT MAX(FoodId) FROM foodItem")
            result = cursor.fetchone()
            if result and result[0]:
                foodId = result[0] + 1
            else:
                foodId = 1 

            # checks if fields are empty except description
            if not name or not price or not type:
                messagebox.showerror("Error", "All fields are required except desccription field")
                return

            # executes insert query after pressing submit button
            cursor.execute("INSERT INTO foodItem (FoodId, Name, Description, Price, Type, EstablishmentId, UserId) VALUES (%s, %s, %s, %s, %s, %s, %s)", (foodId, name, description, price, type, establishment_id, user_id))
            db.commit()
            cursor.close()
            messagebox.showinfo("Success", "Food item added successfully!")
            self.food_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_description_text.delete(1.0, tk.END)
            self.food_price_text.delete(1.0, tk.END) 
            self.food_type_text.set('')
            self.back_to_ViewListFoodItems()
        except mariadb.Error as err:
            messagebox.showerror("Error", f"Error: {err}")
    
    def back_to_ViewListFoodItems(self):
        self.controller.frames[ViewListFoodItems].load_food_items()  # Ensure the list is reloaded
        self.controller.back()
        
# View My Food Item details from ViewListFoodItems
class ViewMyFoodItem(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Display existing food item
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = tk.Label(self, text="Food Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        description_label = tk.Label(self, text="Description:")
        description_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        price_label = tk.Label(self, text="Price:")
        price_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        type_label = tk.Label(self, text="Type:")
        type_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)

        # Text Widgets
        self.food_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_name_text.grid(row=1, column=1, padx=10, pady=5)  
        self.food_description_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_description_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_price_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_price_text.grid(row=3, column=1, padx=10, pady=5)
        self.food_type_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_type_text.grid(row=4, column=1, padx=10, pady=5)

        # Buttons  
        update_button = ttk.Button(self, text="Update Food Item", command=lambda: self.controller.show_frame(UpdateFoodItem))
        update_button.grid(row=5, column=0, padx=10, pady=5)        
        delete_button = ttk.Button(self, text="Remove Food Item", command=self.remove_food_item)
        delete_button.grid(row=5, column=1, padx=10, pady=5)
        back_button = ttk.Button(self, text="Go back", command=self.controller.back)
        back_button.grid(row=6, column=0, columnspan=2, pady=10)

        widgets = [self.label, self.food_name_text, self.food_description_text, self.food_price_text, self.food_type_text, update_button, delete_button, back_button]
        functions.apply_grid_settings(widgets, self)

    def load_food_item_details(self):
        food_id = self.controller.selected_food_id
        cursor.execute("SELECT Name, Description, Price, Type FROM foodItem WHERE FoodId = %s", (food_id,))
        food_item = cursor.fetchone()

        if food_item:
            Name, Description, Price, Type = food_item
            self.label.config(text=Name)
            # Enable, insert text, and disable the food name text widget
            self.food_name_text.config(state='normal')
            self.food_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_name_text.insert(tk.END, Name)
            self.food_name_text.config(state='disabled')
            
            # Enable, insert text, and disable the food description text widget
            self.food_description_text.config(state='normal')
            self.food_description_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_description_text.insert(tk.END, Description)
            self.food_description_text.config(state='disabled')

            # Enable, insert text, and disable the food price text widget
            self.food_price_text.config(state='normal')
            self.food_price_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_price_text.insert(tk.END, Price)
            self.food_price_text.config(state='disabled')

            # Enable, insert text, and disable the food price text widget
            self.food_type_text.config(state='normal')
            self.food_type_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_type_text.insert(tk.END, Type)
            self.food_type_text.config(state='disabled')

    def remove_food_item(self):
        food_id = self.controller.selected_food_id
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to remove this food item?")
        if confirm:
            try:
                cursor.execute("DELETE FROM foodItem WHERE FoodId = %s", (food_id,))
                db.commit()
                messagebox.showinfo("Success", "Food item removed successfully.")
                # Navigate back to previous frame or perform any other necessary actions
                # For example:
                self.controller.back()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_food_id:
            self.load_food_item_details()

# update food item
class UpdateFoodItem(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        # Display existing food item
        self.label = ttk.Label(self, text="", font=("Verdana", 18), padding=10)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # Labels
        name_label = tk.Label(self, text="Food Name:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        description_label = tk.Label(self, text="Description:")
        description_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        price_label = tk.Label(self, text="Price:")
        price_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        type_label = tk.Label(self, text="Type:")
        type_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        
        # Text Widgets
        self.food_name_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_name_text.grid(row=1, column=1, padx=10, pady=5)
        self.food_name_text.bind('<KeyRelease>', self.validate_name_length)
        self.food_description_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_description_text.grid(row=2, column=1, padx=10, pady=5)
        self.food_description_text.bind('<KeyRelease>', self.validate_description_length)
        self.food_price_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        self.food_price_text.grid(row=3, column=1, padx=10, pady=5)
        self.food_price_text.bind('<KeyRelease>', self.validate_price)
        # self.food_type_text = tk.Text(self, wrap=tk.WORD, height=1, width=30)
        # self.food_type_text.grid(row=4, column=1, padx=10, pady=5)
        self.food_type_text = tk.StringVar()
        self.food_type_text = ttk.Combobox(self, textvariable=self.food_type_text, state="readonly", width=28)  # Set width here
        self.food_type_text['values'] = ('Meat', 'Seafood', 'Vegetable', 'Fruit', 'Grains and Cereals', 'Sweets and Snacks', 'Nuts and Seeds', 'Beverages')
        self.food_type_text.grid(row=4, column=1, padx=10, pady=5)

        # Buttons  
        save_button = ttk.Button(self, text="Save", command=self.save_food_item)
        save_button.grid(row=5, column=0, padx=10, pady=5)      
        back_button = ttk.Button(self, text="Cancel", command=self.controller.back)
        back_button.grid(row=5, column=1, padx=10, pady=5)

        widgets = [self.label, self.food_name_text, self.food_description_text, self.food_price_text, self.food_type_text, save_button, back_button]
        functions.apply_grid_settings(widgets, self)

    def validate_name_length(self, event):
        max_length = 50
        current_text = self.food_name_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.food_name_text.delete("1.0", tk.END)
            self.food_name_text.insert("1.0", current_text[:max_length])

    def validate_description_length(self, event):
        max_length = 100
        current_text = self.food_description_text.get("1.0", "end-1c")
        if len(current_text) > max_length:
            self.food_description_text.delete("1.0", tk.END)
            self.food_description_text.insert("1.0", current_text[:max_length])

    def validate_price(self, event):
        current_text = self.food_price_text.get("1.0", "end-1c")
        if not re.match(r'^(\d{1,10}(\.\d{0,2})?)?$', current_text):
            self.food_price_text.delete("1.0", tk.END)
            self.food_price_text.insert("1.0", current_text[:-1])

    def load_food_item_details(self):
        food_id = self.controller.selected_food_id
        cursor.execute("SELECT Name, Description, Price, Type FROM foodItem WHERE FoodId = %s", (food_id,))
        food_item = cursor.fetchone()

        if food_item:
            Name, Description, Price, Type = food_item
            self.label.config(text=Name)
            # Enable, insert text, and disable the food name text widget
            self.food_name_text.config(state='normal')
            self.food_name_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_name_text.insert(tk.END, Name)
            
            # Enable, insert text, and disable the food description text widget
            self.food_description_text.config(state='normal')
            self.food_description_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_description_text.insert(tk.END, Description)

            # Enable, insert text, and disable the food price text widget
            self.food_price_text.config(state='normal')
            self.food_price_text.delete(1.0, tk.END)  # Clear any existing text
            self.food_price_text.insert(tk.END, Price)

            # disable the food type text widget
            self.food_type_text.set('')  # Clear any existing text
            self.food_type_text.insert(tk.END, Type)

    def save_food_item(self):
        food_name = self.food_name_text.get("1.0", "end-1c")
        description = self.food_description_text.get("1.0", "end-1c")
        price = self.food_price_text.get("1.0", "end-1c")
        food_type = self.food_type_text.get()
        food_id = self.controller.selected_food_id

        try:
            # checks if fields are empty except description
            if not food_name or not price or not food_type:
                messagebox.showerror("Error", "All fields are required except desccription field")
                return

            cursor.execute("UPDATE foodItem SET Name = %s, Description = %s, Price = %s, Type = %s WHERE FoodId = %s", (food_name, description, price, food_type, food_id))
            db.commit()  # Commit changes
            messagebox.showinfo("Success", "Food item details updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
        self.controller.back()

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        if self.controller.selected_food_id:
            self.load_food_item_details()

if __name__ == "__main__":
    app = Project()
    app.geometry("500x600")
    app.mainloop()
