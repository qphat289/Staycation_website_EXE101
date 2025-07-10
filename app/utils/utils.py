import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags

def get_rank_info(xp_current):
    # Define rank thresholds and names
    rank_thresholds = {
        'Bronze': 0,
        'Silver': 1000,
        'Gold': 5000,
        'Platium': 10000,
        'Diamond': 20000
    }

    # Determine current rank
    current_rank = 'Bronze'
    for rank, threshold in rank_thresholds.items():
        if xp_current >= threshold:
            current_rank = rank

    # Get experience points needed to reach the next rank
    rank_values = list(rank_thresholds.values())
    current_rank_index = list(rank_thresholds.keys()).index(current_rank)
    
    # Calculate how much more xp the user needs for the next rank
    if current_rank_index + 1 < len(rank_values):
        next_rank = list(rank_thresholds.keys())[current_rank_index + 1]
        next_min = rank_values[current_rank_index + 1]
    else:
        next_rank = 'Diamond'
        next_min = 0

    return current_rank, xp_current, next_rank, next_min

def get_location_name(location_code, location_type='city'):
    """
    Convert location code to full name
    Args:
        location_code: code like 'hcm', 'quan5', etc.
        location_type: 'city' or 'district'
    Returns:
        Full location name
    """
    # Mapping for cities/provinces
    city_mapping = {
        'hcm': 'TP. Hồ Chí Minh',
        'hanoi': 'Hà Nội',
        'danang': 'Đà Nẵng',
        'cantho': 'Cần Thơ',
        'haiphong': 'Hải Phòng'
    }
    
    # Mapping for districts in Ho Chi Minh City
    district_mapping = {
        'quan1': 'Quận 1',
        'quan2': 'Quận 2', 
        'quan3': 'Quận 3',
        'quan4': 'Quận 4',
        'quan5': 'Quận 5',
        'quan6': 'Quận 6',
        'quan7': 'Quận 7',
        'quan8': 'Quận 8',
        'quan9': 'Quận 9',
        'quan10': 'Quận 10',
        'quan11': 'Quận 11',
        'quan12': 'Quận 12',
        'quantanbinh': 'Quận Tân Bình',
        'quantanphu': 'Quận Tân Phú',
        'quanbinhtan': 'Quận Bình Tân',
        'quanbinhthanh': 'Quận Bình Thạnh',
        'quangovap': 'Quận Gò Vấp',
        'quanphunhuan': 'Quận Phú Nhuận',
        'quanthuduc': 'Quận Thủ Đức',
        # Hanoi districts
        'quanbadinh': 'Quận Ba Đình',
        'quanhoankieu': 'Quận Hoàn Kiếm',
        'quantayho': 'Quận Tây Hồ',
        'quanlongbien': 'Quận Long Biên',
        'quancaugiay': 'Quận Cầu Giấy',
        'quandongda': 'Quận Đống Đa',
        'quanhaibatrung': 'Quận Hai Bà Trưng',
        'quanhoangmai': 'Quận Hoàng Mai',
        'quanthanxuan': 'Quận Thanh Xuân',
        'quannamtuliem': 'Quận Nam Từ Liêm',
        'quanbactuliem': 'Quận Bắc Từ Liêm'
    }
    
    if location_type == 'city':
        return city_mapping.get(location_code, location_code)
    elif location_type == 'district':
        return district_mapping.get(location_code, location_code)
    
    return location_code

def get_user_upload_path(user_type, user_id, home_id=None):
    """
    Generate upload path for user files
    Structure: static/data/{user_type}/{user_id}/ or static/data/owner/{user_id}/{home_id}/
    
    Args:
        user_type: 'owner', 'renter', or 'admin'
        user_id: ID of the user
        home_id: ID of the home (only for owner home images)
    
    Returns:
        tuple: (relative_path, absolute_path)
    """
    if user_type == 'owner' and home_id:
        # For owner home images: data/owner/{owner_id}/{home_id}/
        relative_path = f"data/owner/{user_id}/{home_id}"
    elif user_type == 'owner':
        # For owner profile images: data/owner/{owner_id}/
        relative_path = f"data/owner/{user_id}"
    elif user_type == 'admin':
        # For admin profile images: data/admin/{admin_id}/
        relative_path = f"data/admin/{user_id}"
    else:
        # For renter images: data/renter/{renter_id}/
        relative_path = f"data/renter/{user_id}"
    
    # Create absolute path
    absolute_path = os.path.join('static', relative_path)
    
    # Create directory if it doesn't exist
    os.makedirs(absolute_path, exist_ok=True)
    
    return relative_path, absolute_path

def generate_unique_filename(original_filename, prefix=""):
    """
    Generate a unique filename with timestamp and UUID
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix for the filename
    
    Returns:
        str: Unique filename
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate short UUID
    unique_id = str(uuid.uuid4())[:8]
    
    # Create filename
    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
    else:
        filename = f"{timestamp}_{unique_id}{ext}"
    
    return secure_filename(filename)

def fix_image_orientation(image_path):
    """
    Fix image orientation based on EXIF data
    
    Args:
        image_path: Path to the image file
    
    Returns:
        bool: True if fixed successfully, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            # Check if image has EXIF data
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif is not None:
                    # Find orientation tag
                    for tag, value in exif.items():
                        if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                            # Rotate image based on orientation value
                            if value == 3:
                                img = img.rotate(180, expand=True)
                            elif value == 6:
                                img = img.rotate(270, expand=True)
                            elif value == 8:
                                img = img.rotate(90, expand=True)
                            
                            # Save the corrected image
                            # Remove EXIF data to prevent future rotation issues
                            img.save(image_path, optimize=True, quality=85)
                            return True
        return False
    except Exception as e:
        print(f"Error fixing image orientation: {e}")
        return False

def save_user_image(file, user_type, user_id, home_id=None, prefix=""):
    """
    Save user uploaded image to the organized folder structure
    
    Args:
        file: Uploaded file object
        user_type: 'owner', 'renter', or 'admin'
        user_id: ID of the user
        home_id: ID of the home (only for owner home images)
        prefix: Optional prefix for filename (e.g., 'avatar', 'main', 'home')
    
    Returns:
        str: Relative path to saved image
    """
    if not file or not file.filename:
        return None
    
    # Get upload path
    relative_path, absolute_path = get_user_upload_path(user_type, user_id, home_id)
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename, prefix)
    
    # Full file path
    file_path = os.path.join(absolute_path, filename)
    
    # Save file
    file.save(file_path)
    
    # Return relative path for database storage
    return f"{relative_path}/{filename}"

def delete_user_image(image_path):
    """
    Delete user image file
    
    Args:
        image_path: Relative path to the image
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        if image_path:
            full_path = os.path.join('static', image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
    except Exception as e:
        print(f"Error deleting image {image_path}: {e}")
    return False

def cleanup_old_temp_files():
    """
    Clean up old temporary files (older than 1 day)
    """
    try:
        temp_dir = 'static/temp'
        if os.path.exists(temp_dir):
            current_time = datetime.now()
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    # Get file creation time
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    # Delete if older than 1 day
                    if (current_time - file_time).days > 1:
                        os.remove(file_path)
                        print(f"Deleted old temp file: {filename}")
    except Exception as e:
        print(f"Error cleaning up temp files: {e}")

def migrate_old_images():
    """
    Migrate images from old structure to new structure
    This should be run once to move existing images
    """
    try:
        # Import here to avoid circular imports
        from app.models.models import Admin, Owner, Renter, Home, HomeImage
        from app import db
        
        print("Starting image migration...")
        
        # Migrate admin avatars
        admins = Admin.query.all()
        for admin in admins:
            if admin.avatar and (admin.avatar.startswith('uploads/') or not admin.avatar.startswith('data/')):
                old_path = f"static/uploads/{admin.avatar}" if not admin.avatar.startswith('uploads/') else f"static/{admin.avatar}"
                if os.path.exists(old_path):
                    # Create new path
                    new_relative_path, new_absolute_path = get_user_upload_path('admin', admin.id)
                    new_filename = generate_unique_filename(os.path.basename(admin.avatar), 'avatar')
                    new_full_path = os.path.join(new_absolute_path, new_filename)
                    
                    # Move file
                    os.rename(old_path, new_full_path)
                    
                    # Update database
                    admin.avatar = f"{new_relative_path}/{new_filename}"
                    print(f"Migrated admin {admin.id} avatar: {admin.avatar}")
        
        # Migrate owner avatars
        owners = Owner.query.all()
        for owner in owners:
            if owner.avatar and owner.avatar.startswith('uploads/'):
                old_path = f"static/{owner.avatar}"
                if os.path.exists(old_path):
                    # Create new path
                    new_relative_path, new_absolute_path = get_user_upload_path('owner', owner.id)
                    new_filename = generate_unique_filename(os.path.basename(owner.avatar), 'avatar')
                    new_full_path = os.path.join(new_absolute_path, new_filename)
                    
                    # Move file
                    os.rename(old_path, new_full_path)
                    
                    # Update database
                    owner.avatar = f"{new_relative_path}/{new_filename}"
                    print(f"Migrated owner {owner.id} avatar: {owner.avatar}")
        
        # Migrate renter avatars
        renters = Renter.query.all()
        for renter in renters:
            if renter.avatar and renter.avatar.startswith('uploads/'):
                old_path = f"static/{renter.avatar}"
                if os.path.exists(old_path):
                    # Create new path
                    new_relative_path, new_absolute_path = get_user_upload_path('renter', renter.id)
                    new_filename = generate_unique_filename(os.path.basename(renter.avatar), 'avatar')
                    new_full_path = os.path.join(new_absolute_path, new_filename)
                    
                    # Move file
                    os.rename(old_path, new_full_path)
                    
                    # Update database
                    renter.avatar = f"{new_relative_path}/{new_filename}"
                    print(f"Migrated renter {renter.id} avatar: {renter.avatar}")
        
        # Migrate home images
        home_images = HomeImage.query.all()
        for home_image in home_images:
            if home_image.image_path and home_image.image_path.startswith('uploads/'):
                old_path = f"static/{home_image.image_path}"
                if os.path.exists(old_path):
                    home = home_image.home
                    if home:
                        # Create new path
                        new_relative_path, new_absolute_path = get_user_upload_path('owner', home.owner_id, home.id)
                        prefix = 'main' if home_image.is_featured else 'home'
                        new_filename = generate_unique_filename(os.path.basename(home_image.image_path), prefix)
                        new_full_path = os.path.join(new_absolute_path, new_filename)
                        
                        # Move file
                        os.rename(old_path, new_full_path)
                        
                        # Update database
                        home_image.image_path = f"{new_relative_path}/{new_filename}"
                        print(f"Migrated home {home.id} image: {home_image.image_path}")
        
        # Commit all changes
        db.session.commit()
        print("Image migration completed successfully!")
        
    except Exception as e:
        print(f"Error during image migration: {e}")
        db.session.rollback()

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension
    
    Args:
        filename: Name of the uploaded file
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    if not filename:
        return False
    
    # Get file extension and check if it's allowed
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
