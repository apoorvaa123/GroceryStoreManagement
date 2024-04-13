from datetime import datetime,date,timedelta
from flask import Flask,request,render_template,redirect, url_for,session,flash
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import or_
import re
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

app=Flask(__name__)

app.secret_key="SK234J8sd48)@z@!0nnFDNlkjsoinc#ghp*$()"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db=SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = 'static/images'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Function to check if the uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class User(db.Model):
    __tablename__ = 'User'
    user_id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    username=db.Column(db.String(25), unique=True,nullable=False)
    password=db.Column(db.String(15),nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    
class Admin(db.Model):
    __tablename__ = 'Admin'
    Admin_id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    username_a=db.Column(db.String(25), unique=True,nullable=False)
    password_a=db.Column(db.String(15),nullable=False)

  
class Category(db.Model):
    __tablename__ = 'Category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    c_name = db.Column(db.String(100), nullable=False,unique=True)
    c_bg_image = db.Column(db.String(255),nullable=False)


class Product(db.Model):
    __tablename__ = 'Product'
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_name = db.Column(db.String(100), nullable=False)
    manufacture_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    rate_per_unit = db.Column(db.Float, nullable=False)
    avail_qty = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('Category.category_id'), nullable=False)
    p_bg_image = db.Column(db.String(255),nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    cart_items = db.relationship('CartItem', backref='cart_product', primaryjoin='Product.product_id == CartItem.product_id', cascade='all, delete-orphan', passive_deletes=True)
    cart_items_related = db.relationship('CartItem', back_populates='cart_product', overlaps='cart_items,cart_product')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('Product.product_id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('cart_items_rel', lazy=True, cascade='all, delete-orphan'))

def get_expired_products():
    # Get the current date
    current_date = date.today()

    # Query the database to get the expired products and their expiry dates
    query_result = db.session.query(Product.p_name, Product.expiry_date) \
        .filter(Product.expiry_date < current_date) \
        .all()

    # Convert the query result to a list of dictionaries
    expired_products = [{'name': item[0], 'expiry_date': item[1]} for item in query_result]

    return expired_products


def get_expiring_products():

    current_date = date.today()

    query_result = db.session.query(Product.p_name, Product.expiry_date) \
        .filter(Product.expiry_date >= current_date) \
        .filter(Product.expiry_date <= (current_date + timedelta(days=30))) \
        .all()

    
    expiring_products = [{'name': item[0], 'expiry_date': item[1]} for item in query_result]

    return expiring_products

    
@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        error_messages = []

        # Validate password complexity
        if len(password) < 8:
            error_messages.append('Password must be at least 8 characters long')
            return render_template('signup.html', error_messages=error_messages)
        if not re.search(r'\d', password):
            error_messages.append('Password must contain at least one digit')
            return render_template('signup.html', error_messages=error_messages)
        if not re.search(r'[A-Z]', password):
            error_messages.append('Password must contain at least one uppercase letter')
            return render_template('signup.html', error_messages=error_messages)
        if not re.search(r'[@#$%^&+=]', password):
            error_messages.append('Password must contain at least one special character (@, #, $, %, ^, &, +, =)')
            return render_template('signup.html', error_messages=error_messages)

        if password != confirm_password:
            error_messages.append('Passwords do not match. Please try again.')
            return render_template('signup.html', error_messages=error_messages)


        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.user_id
        return redirect(url_for('dashboard'))
    

@app.route('/login',methods=['GET','POST'])
def login():
    
    if request.method=='GET':
        return render_template('login.html')
    elif request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        user=db.session.query(User).filter(User.username==username).first()

        if not user:
            error_message = 'Invalid username'
            return render_template('login.html', error_message=error_message)
        if user.password==password:
            session['user_id'] = user.user_id
            return redirect(url_for('dashboard'))
        
        else:
            error_message = 'Invalid password'
            return render_template('login.html', error_message=error_message)
        
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    categories = Category.query.all()
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    search_query = request.form.get('search_query')

    if user:
        cart_items_count = len(user.cart_items)
    else:
        cart_items_count = 0

    if search_query:
        # If a search query is provided, filter products based on the query
        search_results = Product.query.filter(
            or_(
                Product.p_name.ilike(f'%{search_query}%'),
            )
        ).all()
        return render_template('dashboard.html', categories=categories, user=user.username, cart_items_count=cart_items_count, search_results=search_results, search_query=search_query)

    return render_template('dashboard.html', categories=categories, user=user.username, cart_items_count=cart_items_count)


def create_default_admin():
    default_admin_username = "Admin_"
    default_admin_password = "Admin@123"

    # Check if the admin account already exists
    admin = Admin.query.filter_by(username_a=default_admin_username).first()

    if not admin:
        try:
            # Create the default admin account
            admin = Admin(username_a=default_admin_username, password_a=default_admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Default admin account created successfully.")
        except IntegrityError:
            db.session.rollback()
            print("Error: Default admin account creation failed.")

        
@app.route('/adminlogin',methods=['GET','POST'])
def admin_login():
    if request.method=='GET':
        return render_template('admin_login.html')
    elif request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        user=db.session.query(Admin).filter(Admin.username_a==username).first()

        if not user:
            error_message = 'Invalid username'
            return render_template('admin_login.html', error_message=error_message)
        if user.password_a==password:
            return redirect(url_for('adminpage',param='success'))
        
        else:
            error_message = 'Invalid password'
            return render_template('admin_login.html', error_message=error_message)

        
@app.route('/adminpage',methods=['GET','POST'])
def adminpage():
    categories = Category.query.all()
    return render_template('admin_page.html',categories=categories)

@app.route('/admin/add_category',methods=['GET','POST'])
def add_category():
    categories = Category.query.all()
        
    if request.method=='GET':
        return render_template('add_category.html',category=categories)
    
    elif request.method=='POST':
        category_name=request.form['category_name']
        
        existing_category=db.session.query(Category).filter(Category.c_name==category_name).first()
        if existing_category:
            return render_template('add_category.html', error_message='Category already exists!',category=categories)
        
        if 'category_image' in request.files:
            category_image = request.files['category_image']
            if category_image.filename != '':
                # Save the uploaded file to the static/images folder
                filename = secure_filename(category_image.filename)
                category_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Save the category with the image filename
                newly_added_category = Category(c_name=category_name, c_bg_image=filename)
            else:
                newly_added_category = Category(c_name=category_name)
        else:
            newly_added_category = Category(c_name=category_name)

        db.session.add(newly_added_category)
        db.session.commit()
        success_message='New category added successfully1'
        return redirect(url_for('adminpage', param=success_message))
        
    
@app.route('/admin/remove_category/<int:category_id>', methods=['POST'])
def remove_category(category_id):
    category = Category.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
        success_message = 'Category removed successfully.'
        return redirect(url_for('adminpage', param=success_message))
    else:
        error_message = 'Category not found.'
        return redirect(url_for('adminpage', param=error_message))

@app.route('/admin/edit_category/<int:category_id>', methods=['GET','POST'])
def edit_category(category_id):
    category = Category.query.get(category_id)

    if request.method=='GET':
        return render_template('edit_category.html', category=category)
    
    if request.method == 'POST':

        if category:
            new_category_name = request.form['new_category_name']
            existing_category = Category.query.filter(Category.c_name == new_category_name).first()

            if existing_category and existing_category.category_id != category.category_id:
                error_message = 'Category name already exists!'
                return redirect(url_for('adminpage', param=error_message))

            category.c_name = new_category_name

            if 'category_image' in request.files:
                file = request.files['category_image']
                if file and allowed_file(file.filename):
                    if category.c_bg_image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], category.c_bg_image.split('/')[-1])
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    category.c_bg_image = f'{filename}'

            db.session.commit()
            success_message = 'Category updated successfully.'
            return redirect(url_for('adminpage', param=success_message))
        else:
            error_message = 'Category not found.'
            return redirect(url_for('adminpage', param=error_message))

#products

@app.route('/admin/category_products/<int:category_id>', methods=['POST','GET'])
def category_products(category_id):
    category = Category.query.get(category_id)
    if category:
        products = category.products
        return render_template('category_products.html', category_id=category_id, products=products)

@app.route('/admin/add_product/<int:category_id>', methods=['GET', 'POST'])
def add_product(category_id):
    category = Category.query.get(category_id)
    products = category.products
    if request.method == 'GET':
        return render_template('add_product.html',category=category, products=products)
    elif request.method == 'POST':
        p_name = request.form['p_name']
        manufacture_date = request.form['manufacture_date']
        expiry_date = request.form['expiry_date']
        rate_per_unit = request.form['rate_per_unit']
        quantity_available = request.form['quantity_available']

        manufacture_date = datetime.strptime(manufacture_date, '%Y-%m-%d').date()
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        if expiry_date < manufacture_date:
            error_message = 'Expiry date must be greater than or equal to the manufacture date.'
            return render_template('add_product.html',category=category, products=products,error_message=error_message)

        existing_product=db.session.query(Product).filter(Product.p_name==p_name).first()
        if existing_product:
            return render_template('add_product.html', error_message='Category already exists!',category=category, products=products)
        

        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Save the image path to the database
                product = Product(p_name=p_name, manufacture_date=manufacture_date,
                                      expiry_date=expiry_date, rate_per_unit=rate_per_unit,
                                      avail_qty=quantity_available, p_bg_image=filename,
                                      category_id=category_id)

            else:
                error_message = 'Invalid file type. Only jpg, jpeg, png, and gif images are allowed.'
                category = Category.query.get(category_id)
                return render_template('add_product.html', error_message=error_message, category=category, products=products)

        else:
            error_message = 'No file uploaded. Please select a valid image file.'
            category = Category.query.get(category_id)
            return render_template('add_product.html', error_message=error_message, category=category,products=products)
        
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('category_products', category_id=category_id))
    

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        error_message = 'Invalid product.'
        return render_template('admin_page.html', error_message=error_message)

    if request.method == 'GET':
        return render_template('edit_product.html', product=product)
    elif request.method == 'POST':
        # Update the product with the edited information from the form
        
        product.p_name = request.form['product_name']
        manufacture_date = request.form['manufacture_date']
        manufacture_date = datetime.strptime(manufacture_date, '%Y-%m-%d').date()
        product.manufacture_date=manufacture_date
        expiry_date = request.form['expiry_date']
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        product.expiry_Date=expiry_date
        product.rate_per_unit = request.form['rate_per_unit']
        product.avail_qty = request.form['quantity_available']

        

        if 'product_images' in request.files:
                file = request.files['product_images']
                if file and allowed_file(file.filename):
                    # Delete the old image if it exists
                    if product.p_bg_image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.p_bg_image.split('/')[-1])
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    # Save the new image to the database
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    product.p_bg_image = f'{filename}'
                
        
        db.session.commit()

        return redirect(url_for('category_products', category_id=product.category_id))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        error_message = 'Invalid product.'
        return render_template('error.html', error_message=error_message)

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('category_products', category_id=product.category_id))

@app.route('/buy_product/<int:product_id>', methods=['GET', 'POST'])
def add_cart(product_id):
    product = Product.query.get(product_id)

    if request.method == 'GET':
        return render_template('buy_product.html', product=product)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        if quantity <= product.avail_qty:
            # Add the selected product to the user's cart
            user_id = session.get('user_id')
            cart_item = CartItem.query.filter_by(product_id=product_id, user_id=user_id).first()
            if cart_item:
                # If the product is already in the cart, update the quantity
                new_quantity = cart_item.quantity + quantity
                if new_quantity <= product.avail_qty:
                    cart_item.quantity = new_quantity
                else:
                    flash("The quantity exceeds the available stock for this product.")
            else:
                # If the product is not in the cart, add it as a new entry
                cart_item = CartItem(product_id=product_id, quantity=quantity, user_id=user_id)
                print(cart_item)
                db.session.add(cart_item)
            
            db.session.commit()

            return redirect(url_for('view_cart'))
        

@app.route('/cart', methods=['GET'])
def view_cart():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if user is None:
        return redirect(url_for('login'))
    cart_items = user.cart_items
    grand_total = sum(cart_item.product.rate_per_unit * cart_item.quantity for cart_item in cart_items)

    return render_template('cart.html', cart_items=cart_items, grand_total=grand_total)

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    # Find the cart item based on the product_id and the current user_id
    user_id = session.get('user_id')
    cart_item = CartItem.query.filter_by(product_id=product_id, user_id=user_id).first()
    print(cart_item)
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for('view_cart'))


@app.route('/update_cart', methods=['POST'])
def update_cart():
    # Retrieve the cart items from the database
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    cart_items = user.cart_items

    for cart_item in cart_items:
        new_quantity = int(request.form['quantity'])
        cart_item.quantity = new_quantity

    db.session.commit()
    return redirect(url_for('view_cart'))

@app.route('/purchase_confirmation', methods=['GET', 'POST'])
def purchase_confirmation():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    # if request.method=='GET':
    #     return r  ender_template('purchase_confirmation.html', cart_items=user.cart_items, user=user.username)

    if request.method == 'POST':

        cart_items = CartItem.query.filter_by(user_id=user_id).all() 
        for cart_item in cart_items:
            avail_qty = cart_item.product.avail_qty
            cart_qty = cart_item.quantity
            if cart_qty > avail_qty:
                # Redirect back to cart with an error message
                error_message = f"Available Quantity of {cart_item.product.p_name} : {avail_qty}."
                user_id = session.get('user_id')
                user = User.query.get(user_id)
                if user is None:
                    return redirect(url_for('login'))
                cart_items = user.cart_items
                grand_total = sum(cart_item.product.rate_per_unit * cart_item.quantity for cart_item in cart_items)

                return render_template('cart.html', cart_items=cart_items, grand_total=grand_total,error_message=error_message)
        # Get the current user's ID from the session
        user_id = session.get('user_id')
        if user_id is None:
            # When the user is not found
            return redirect(url_for('login'))

        # Get the cart items from the database for the current user
        cart_items = CartItem.query.filter_by(user_id=user_id).all()

        # Update the product availability quantities based on purchased quantities
        for cart_item in cart_items:
            product = cart_item.product
            product.avail_qty -= cart_item.quantity

        # Save the changes to the database
        db.session.commit()

        # Clear the cart items for the current user after the purchase
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return render_template('successful_buy.html')

@app.route('/admin/product_statistics')
def product_statistics():
    expiring_products = get_expiring_products()
    expired_products = get_expired_products()

    return render_template('statistics.html',expiring_products=expiring_products ,expired_products=expired_products)

if __name__=='__main__':
    with app.app_context():
        db.create_all() 
        create_default_admin() 
    app.run(debug=True) 