#!/usr/bin/env python3
"""
Script to migrate images from old structure to new organized structure
"""

import os
import sys
import shutil

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_images():
    try:
        from app import app
        from app.models.models import Owner, Renter, Home, HomeImage, db
        from app.utils.utils import get_user_upload_path, generate_unique_filename
        
        with app.app_context():
            print("Starting image migration...")
            
            # Migrate owner avatars
            owners = Owner.query.all()
            for owner in owners:
                if owner.avatar and owner.avatar.startswith("uploads/"):
                    old_path = f"static/{owner.avatar}"
                    if os.path.exists(old_path):
                        new_relative_path, new_absolute_path = get_user_upload_path("owner", owner.id)
                        new_filename = generate_unique_filename(os.path.basename(owner.avatar), "avatar")
                        new_full_path = os.path.join(new_absolute_path, new_filename)
                        shutil.move(old_path, new_full_path)
                        owner.avatar = f"{new_relative_path}/{new_filename}"
                        print(f"Migrated owner {owner.id} avatar")
            
            # Migrate renter avatars
            renters = Renter.query.all()
            for renter in renters:
                if renter.avatar and renter.avatar.startswith("uploads/"):
                    old_path = f"static/{renter.avatar}"
                    if os.path.exists(old_path):
                        new_relative_path, new_absolute_path = get_user_upload_path("renter", renter.id)
                        new_filename = generate_unique_filename(os.path.basename(renter.avatar), "avatar")
                        new_full_path = os.path.join(new_absolute_path, new_filename)
                        shutil.move(old_path, new_full_path)
                        renter.avatar = f"{new_relative_path}/{new_filename}"
                        print(f"Migrated renter {renter.id} avatar")
            
            # Migrate home images
            home_images = HomeImage.query.all()
            for home_image in home_images:
                if home_image.image_path and home_image.image_path.startswith("uploads/"):
                    old_path = f"static/{home_image.image_path}"
                    if os.path.exists(old_path):
                        home = home_image.home
                        if home:
                            new_relative_path, new_absolute_path = get_user_upload_path("owner", home.owner_id, home.id)
                            prefix = "main" if home_image.is_featured else "home"
                            new_filename = generate_unique_filename(os.path.basename(home_image.image_path), prefix)
                            new_full_path = os.path.join(new_absolute_path, new_filename)
                            shutil.move(old_path, new_full_path)
                            home_image.image_path = f"{new_relative_path}/{new_filename}"
                            print(f"Migrated home {home.id} image")
            
            db.session.commit()
            print("Migration completed successfully!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        if "db" in locals():
            db.session.rollback()

if __name__ == "__main__":
    migrate_images()

