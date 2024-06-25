import hashlib
# import bcrypt
from app import cursor

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_next_user_id():
    cursor.execute("SELECT MAX(UserId) FROM user")
    result = cursor.fetchone()
    if result and result[0]:
        return result[0] + 1
    else:
        return 1

def get_next_food_id():
    cursor.execute("SELECT MAX(FoodId) FROM foodItem")
    result = cursor.fetchone()
    if result and result[0]:
        return result[0] + 1
    else:
        return 

def get_next_establishment_id():
    cursor.execute("SELECT MAX(EstablishmentId) FROM establishment")
    result = cursor.fetchone()
    if result and result[0]:
        return result[0] + 1
    else:
        return 1
    
# def get_next_review_id():
#     cursor.execute("SELECT MAX(ReviewId) FROM review")
#     result = cursor.fetchone()
#     if result and result[0]:
#         return result[0] + 1
#     else:
#         return 1

def apply_grid_settings(widgets, parent):
    for i, widget in enumerate(widgets):
        widget.grid(row=i, column=0, columnspan=2, pady=5, padx=10)
    
    parent.grid_rowconfigure(len(widgets), weight=1)
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_columnconfigure(1, weight=1)    
    
def fetch_my_estab_reviews(user_id):
    cursor.execute("SELECT reviewID, comment FROM review WHERE userid = %s AND foodID IS NULL", (user_id,))
    return cursor.fetchall()

def fetch_all_estab_reviews():
    cursor.execute("SELECT reviewID, comment FROM review WHERE foodID IS NULL")
    return cursor.fetchall()

def fetch_all_estabs_list():
    cursor.execute("SELECT establishmentID, establishmentName FROM establishment")
    return cursor.fetchall()

def fetch_my_food_reviews(user_id):
    cursor.execute("SELECT reviewID, comment FROM review WHERE userID = %s and foodID IS NOT NULL ORDER BY reviewID;", (user_id,))
    return cursor.fetchall()

def fetch_all_food_reviews():
    cursor.execute("SELECT reviewID, comment FROM review WHERE foodID IS NOT NULL")
    return cursor.fetchall()

def fetch_all_food_items_list():
    cursor.execute("SELECT foodID, name FROM foodItem")
    return cursor.fetchall()

#functions for establishment (owner)
def fetch_all_estabs(user_id):
    cursor.execute("SELECT EstablishmentId, EstablishmentName, ContactNumber FROM establishment WHERE user_id = %s", (user_id,))
    return cursor.fetchall()

def fetch_my_estabs(user_id):
    cursor.execute("SELECT EstablishmentId, EstablishmentName FROM establishment WHERE userid = %s", (user_id,))
    return cursor.fetchall()

def fetch_food_by_type(type):
    cursor.execute("SELECT * FROM foodItem where type = %s", (type,))
    return cursor.fetchall()

def fetch_all_food_types():
    cursor.execute("SELECT distinct type FROM foodItem")
    return cursor.fetchall()