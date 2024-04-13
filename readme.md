# Flask Grocery Store Web Application

This is a Flask-based Web Application for managing and purchasing products online. Users can sign up, log in, browse products by categories, add products to their cart, and make purchases. Admins can log in and manage categories and products.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Database Configuration](#database)
- [License](#license)

## Features

- User registration and login system.
- Admin login to manage categories and products.
- Browse products by products for users.
- Add products to the cart and make purchases.
- Expiry and availability tracking of products for admins.
- User-friendly dashboard for both users and admins.

## Prerequisites

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Required Python packages
    - datetime
    - os
    - re
    - werkzeug.utils

## Installation

1. Create a virtual environment (optional but recommended):

        python3 -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate

2. Install the required packages:
        - pip install Flask
        - pip install flask-sqlalchemy

3. Set up the database:
        # Run these commands within a Python interpreter (e.g., `python` or `python3`)

        from app import db, create_default_admin
        with app.app_context():
            db.create_all()
            create_default_admin()

4. Run the application:
        python app.py


## Usage

    Access the application by visiting http://localhost:5000 in your web browser.

    Sign up as a user or log in with existing credentials.

    Browse products and add desired items to your cart.

    Go to your cart, review your items, and proceed to buy.

    Admins can log in using the admin credentials to manage categories and products.

## Database Configuration

This Flask E-Commerce Web Application uses a SQLite database for data storage.
The database is to be created manually, tables will be created automatically after first run.
Here's how you can set up and manage the database for this project:

### Database Setup

1. Open a Python interpreter (e.g., `python` or `python3`) within your project directory.

2. Run the following commands to set up the database and create tables:

        from app import db, create_default_admin
        with app.app_context():
            db.create_all()
            create_default_admin()

3. SQLite Database File
The SQLite database file (database.sqlite3) will be automatically created in the root directory of your project in 'instance' folder.

4. Tables: User, Admin, Category, Product, cart_item 

User:
CREATE TABLE "User" (
	user_id INTEGER NOT NULL, 
	username VARCHAR(25) NOT NULL, 
	password VARCHAR(15) NOT NULL, 
	PRIMARY KEY (user_id), 
	UNIQUE (username)
)

Admin:
CREATE TABLE "Admin" (
	"Admin_id"	INTEGER NOT NULL,
	"username_a"	VARCHAR(25) NOT NULL,
	"password_a"	VARCHAR(15) NOT NULL,
	PRIMARY KEY("Admin_id"),
	UNIQUE("username_a")
)

Category:
CREATE TABLE "Category" (
	"category_id"	INTEGER NOT NULL,
	"c_name"	VARCHAR(100) NOT NULL,
	"c_bg_image"	VARCHAR(255),
	PRIMARY KEY("category_id")
)

Product:
CREATE TABLE "Product" (
	"product_id"	INTEGER NOT NULL,
	"p_name"	VARCHAR(100) NOT NULL,
	"manufacture_date"	DATE NOT NULL,
	"expiry_date"	DATE NOT NULL,
	"rate_per_unit"	FLOAT NOT NULL,
	"category_id"	INTEGER NOT NULL,
	"avail_qty"	INTEGER NOT NULL,
	"p_bg_image"	VARCHAR(100),
	PRIMARY KEY("product_id"),
	FOREIGN KEY("category_id") REFERENCES "Category"("category_id")
)

cart_item:
CREATE TABLE cart_item (
	id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES "Product" (product_id), 
	FOREIGN KEY(user_id) REFERENCES "User" (user_id)
)

## License
This project is licensed under the MIT License.
