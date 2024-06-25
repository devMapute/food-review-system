/* 
-- Alarcon, Magenta
-- Manalo, Jallen Rose T.
-- Mapute, Andrae
-- CMSC 127 ST-3L
*/

DROP DATABASE IF EXISTS 127project;
CREATE DATABASE 127project;
GRANT ALL ON 127project.* TO 'scott'@'localhost';

USE 127project;

CREATE TABLE user (
    UserID INT,
    Name VARCHAR(30) NOT NULL UNIQUE,
    Username VARCHAR(30) NOT NULL,
    Password TEXT NOT NULL,
    IsCustomer BOOLEAN NOT NULL,
    IsOwner BOOLEAN NOT NULL,
    PRIMARY KEY (UserID)
);

CREATE TABLE establishment (
	EstablishmentID INT,
    EstablishmentName VARCHAR(50) NOT NULL UNIQUE,
    ContactNumber VARCHAR(11) NOT NULL,
    UserID INT NOT NULL,
    PRIMARY KEY (EstablishmentID),
    CONSTRAINT establishment_UserID_fk FOREIGN KEY(UserID) REFERENCES user(UserID)
);

CREATE TABLE foodItem (
	FoodID INT auto_increment,
	Name VARCHAR(50) NOT NULL UNIQUE,
	Description VARCHAR(100),
	Price DECIMAL(10, 2) NOT NULL,
	Type VARCHAR(12) NOT NULL,
	EstablishmentID INT NOT NULL,
	UserID INT NOT NULL,
	PRIMARY KEY (FoodID),
	CONSTRAINT foodItem_EstablishmentID_fk FOREIGN KEY(EstablishmentID) REFERENCES establishment(EstablishmentID),
    CONSTRAINT foodItem_UserID_fk FOREIGN KEY(UserID) REFERENCES user(UserID)
);

CREATE TABLE review(
	ReviewID INT auto_increment,
	Comment VARCHAR(255),
	Rating TINYINT NOT NULL,
	Date DATE DEFAULT CURDATE(),
	UserID INT NOT NULL,
	EstablishmentID INT NOT NULL,
    FoodID INT,
    PRIMARY KEY (ReviewID),
    CONSTRAINT review_UserID_fk FOREIGN KEY(UserID) REFERENCES user(UserID),
    CONSTRAINT review_EstablishmentID_fk FOREIGN KEY(EstablishmentID) REFERENCES establishment(EstablishmentID),
    CONSTRAINT review_FoodID_fk FOREIGN KEY(FoodID) REFERENCES foodItem(FoodID)
);


-- Insert sample users
INSERT INTO user (UserID, Name, Username, Password, IsCustomer, IsOwner) VALUES
(1, 'Magenta Alarcon', 'magenta', 'cbfad02f9ed2a8d1e08d8f74f5303e9eb93637d47f82ab6f1c15871cf8dd0481', 0, 1),
(2, 'Jallen Rose T. Manalo', 'jallen', 'cbfad02f9ed2a8d1e08d8f74f5303e9eb93637d47f82ab6f1c15871cf8dd0481', 1, 0),
(3, 'Andrae Mapute', 'andrae', 'cbfad02f9ed2a8d1e08d8f74f5303e9eb93637d47f82ab6f1c15871cf8dd0481', 0, 1);

-- Insert sample establishments with creative names and appropriate food
INSERT INTO establishment (EstablishmentID, EstablishmentName, ContactNumber, UserID) VALUES
(1, 'Rustic Kitchen', '12345678901', 1), -- A cozy farmhouse-style restaurant
(2, 'Sips & Bites Café', '23456789012', 1), -- A trendy café with light bites and beverages
(3, 'Sweet Tooth Bakery', '34567890123', 3), -- A charming bakery specializing in pastries and cakes
(4, 'Cheers Bar & Lounge', '45678901234', 3), -- A vibrant bar offering cocktails and beers
(5, 'Street Snacks Corner', '56789012345', 3); -- A bustling food stall serving street food delicacies

-- Insert sample food items suitable for each establishment
INSERT INTO foodItem (Name, Description, Price, Type, EstablishmentID, UserID) VALUES
-- Rustic Kitchen
('Farmhouse Chicken', 'Grilled chicken breast served with roasted vegetables and mashed potatoes', 14.99, 'Main', 1, 1),
('Country Salad', 'Fresh mixed greens with seasonal fruits, nuts, and balsamic vinaigrette', 9.50, 'Salad', 1, 1),
('Homemade Apple Pie', 'Classic apple pie with a flaky crust, served warm with vanilla ice cream', 6.99, 'Dessert', 1, 1),
('Berry Lemonade', 'Refreshing lemonade infused with mixed berries and a hint of mint', 3.99, 'Drink', 1, 1),
('Rustic Cheese Platter', 'Assorted cheeses served with crackers, nuts, and honey', 18.99, 'Appetizer', 1, 1),

-- Sips & Bites Café
('Avocado Toast', 'Sourdough toast topped with smashed avocado, cherry tomatoes, and feta cheese', 8.50, 'Breakfast', 2, 1),
('Quinoa Salad Bowl', 'Quinoa mixed with roasted vegetables, chickpeas, and tahini dressing', 10.99, 'Salad', 2, 1),
('Espresso Macchiato', 'Double shot of espresso with a dollop of foamed milk', 3.50, 'Coffee', 2, 1),
('Iced Matcha Latte', 'Iced green tea latte made with matcha powder and almond milk', 5.50, 'Drink', 2, 1),
('Cinnamon Roll', 'Freshly baked cinnamon roll with cream cheese frosting', 4.99, 'Pastry', 2, 1),

-- Sweet Tooth Bakery
('Red Velvet Cupcake', 'Classic red velvet cupcake topped with cream cheese frosting', 3.99, 'Dessert', 3, 3),
('Chocolate Chip Cookies', 'Soft and chewy chocolate chip cookies made with premium chocolate', 2.50, 'Pastry', 3, 3),
('Rainbow Cake Slice', 'Layers of vibrant rainbow-colored cake with buttercream frosting', 5.99, 'Cake', 3, 3),
('Vanilla Bean Scone', 'Buttery scone infused with vanilla bean, served with clotted cream and jam', 4.50, 'Pastry', 3, 3),
('Fruit Tart', 'Shortcrust pastry filled with pastry cream and topped with fresh fruits', 6.50, 'Dessert', 3, 3),

-- Cheers Bar & Lounge
('Margarita', 'Classic cocktail made with tequila, triple sec, lime juice, and salted rim', 9.99, 'Cocktail', 4, 3),
('Craft Beer Flight', 'Sampler of four locally brewed craft beers', 12.50, 'Beer', 4, 3),
('Nachos Supreme', 'Crispy tortilla chips topped with melted cheese, jalapenos, salsa, and sour cream', 8.99, 'Appetizer', 4, 3),
('Classic Mojito', 'Refreshing cocktail made with white rum, lime juice, mint, and soda water', 10.50, 'Cocktail', 4, 3),
('Cheeseburger Sliders', 'Mini beef burgers topped with cheddar cheese, lettuce, and tomato', 11.99, 'Main', 4, 3),

-- Street Snacks Corner
('Chicken Satay', 'Grilled chicken skewers marinated in spices, served with peanut sauce', 5.99, 'Appetizer', 5, 3),
('Mango Sticky Rice', 'Sweet sticky rice topped with ripe mango slices and coconut cream', 4.50, 'Dessert', 5, 3),
('Grilled Corn on the Cob', 'Fresh corn on the cob grilled with chili lime butter', 3.50, 'Snack', 5, 3),
('Banana Cue', 'Deep-fried banana coated in caramelized sugar, served on a stick', 2.99, 'Snack', 5, 3),
('Fish Balls', 'Deep-fried fish balls served with sweet and spicy sauce', 3.99, 'Snack', 5, 3);

-- Add review for each food item in the first establishment (Rustic Kitchen)
INSERT INTO review (ReviewID, Comment, Rating, UserID, EstablishmentID, FoodID) VALUES
(1, 'Absolutely loved the Farmhouse Chicken! It was cooked perfectly and had amazing flavor.', 5, 2, 1, 1),
(2, 'The Country Salad was fresh and delicious. A great healthy option!', 4, 2, 1, 2),
(3, 'The Homemade Apple Pie was heavenly! Perfectly sweet with a flaky crust.', 5, 2, 1, 3),
(4, 'Rustic Cheese Platter was a great start to the meal. Loved the variety of cheeses!', 4, 2, 1, 5),
(5, 'Berry Lemonade was so refreshing! Just what I needed on a hot day.', 5, 2, 1, 4);

-- Add a review for the establishment itself (Rustic Kitchen)
INSERT INTO review (ReviewID, Comment, Rating, UserID, EstablishmentID) VALUES
(6, 'Had a wonderful dining experience at Rustic Kitchen. The ambiance was cozy and the food was excellent!', 5, 2, 1);


CREATE VIEW TopRatedEstablishments AS
SELECT 
    e.EstablishmentID,
    e.EstablishmentName,
    COALESCE(AVG(r.Rating), 0) AS AverageRating
FROM 
    establishment e
LEFT JOIN 
    review r ON e.EstablishmentID = r.EstablishmentID
GROUP BY 
    e.EstablishmentID, e.EstablishmentName
ORDER BY 
    AverageRating DESC;

CREATE VIEW TopRatedFoodItems AS
SELECT 
    f.FoodID,
    f.Name AS FoodItemName,
    COALESCE(AVG(r.Rating), 0) AS AverageRating
FROM 
    foodItem f
LEFT JOIN 
    review r ON f.FoodID = r.FoodID
GROUP BY 
    f.FoodID, f.Name
ORDER BY 
    AverageRating DESC;

-- CREATE VIEW FOR FOOD ITEMS FILTER
CREATE VIEW FoodItemsAndEstabName AS
SELECT
    foodID,
    Name,
    Type,
    Price,
    e.EstablishmentName
FROM 
    foodItem f
LEFT JOIN 
    establishment e ON f.EstablishmentID = e.EstablishmentID;
