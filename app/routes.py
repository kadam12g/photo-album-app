from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from app.models import Image, User
from app import db
from flask_login import login_user, logout_user, login_required, current_user

main = Blueprint('main', __name__)

# Helper functions
def allowed_file(filename):
    """Check if the file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    """Home page with upload form and recent images."""
    images = Image.query.order_by(Image.upload_date.desc()).limit(10).all()
    return render_template('index.html', images=images)

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handle image upload."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    title = request.form.get('title', '')
    if len(title) > 40:
        flash('Title must be less than 40 characters')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = str(uuid.uuid4()) + secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(filepath)
        
        # Create new image record
        new_image = Image(
            filename=filename,
            title=title,
            user_id=current_user.id
        )
        
        # Save image info to database
        db.session.add(new_image)
        db.session.commit()
        
        flash('Image uploaded successfully!')
        return redirect(url_for('main.view_image', image_id=new_image.id))
    
    flash('Invalid file type')
    return redirect(url_for('main.index'))

@main.route('/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Delete an image."""
    image = Image.query.get_or_404(image_id)
    
    # Check if the current user is the owner
    if image.user_id != current_user.id:
        flash('You do not have permission to delete this image')
        return redirect(url_for('main.index'))
    
    # Delete the file
    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
    except Exception as e:
        flash(f'Error deleting file: {str(e)}')
    
    # Delete from database
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully')
    return redirect(url_for('main.index'))

@main.route('/image/<int:image_id>')
def view_image(image_id):
    """Display an image."""
    image = Image.query.get_or_404(image_id)
    return render_template('view.html', image=image)

@main.route('/images')
def list_images():
    """List all uploaded images."""
    sort_by = request.args.get('sort', 'date')  # Default to sorting by date
    
    if sort_by == 'name':
        images = Image.query.order_by(Image.title).all()
    else:  # sort by date
        images = Image.query.order_by(Image.upload_date.desc()).all()
    
    return render_template('list.html', images=images, sort_by=sort_by)

@main.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('main.register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        
        login_user(user)
        flash(f'Welcome, {user.username}!')
        
        return redirect(url_for('main.index'))
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    """Log out a user."""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@main.route('/health')
def health_check():
    """Health check endpoint that verifies database connectivity."""
    try:
        # Execute a simple query to check database connectivity
        db.session.execute('SELECT 1')
        return {
            'status': 'healthy',
            'database': 'connected'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, 500
