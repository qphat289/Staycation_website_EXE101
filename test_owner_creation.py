#!/usr/bin/env python3
"""
Script test để kiểm tra việc tạo owner
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from app.models.models import db, Owner, Admin
from app.utils.password_validator import PasswordValidator
from app.utils.email_validator import process_email

def test_owner_creation():
    """Test việc tạo owner"""
    with app.app_context():
        print("🔧 Testing owner creation...")
        
        # Test data
        test_data = {
            'first_name': 'Test',
            'last_name': 'Owner',
            'username': 'testowner',
            'email': 'testowner@example.com',
            'phone': '0123456789',
            'password': 'Test123!',
            'confirm_password': 'Test123!'
        }
        
        # Validate password
        password_evaluation = PasswordValidator.evaluate_password(test_data['password'])
        print(f"Password evaluation: {password_evaluation}")
        
        # Validate email
        cleaned_email, is_valid_email = process_email(test_data['email'])
        print(f"Email validation: {cleaned_email}, {is_valid_email}")
        
        # Check if username exists
        existing_owner = Owner.query.filter_by(username=test_data['username']).first()
        print(f"Existing owner with username: {existing_owner}")
        
        # Check if email exists
        existing_email = Owner.query.filter_by(email=cleaned_email).first()
        print(f"Existing owner with email: {existing_email}")
        
        # Check if phone exists
        existing_phone = Owner.query.filter_by(phone=test_data['phone']).first()
        print(f"Existing owner with phone: {existing_phone}")
        
        # Try to create owner
        try:
            new_owner = Owner(
                username=test_data['username'],
                email=cleaned_email,
                phone=test_data['phone'],
                first_name=test_data['first_name'],
                last_name=test_data['last_name'],
                full_name=f"{test_data['first_name']} {test_data['last_name']}",
                email_verified=False,
                first_login=True
            )
            new_owner.set_password(test_data['password'])
            
            db.session.add(new_owner)
            db.session.commit()
            
            print(f"✅ Owner created successfully: {new_owner.username}")
            
            # Clean up - delete test owner
            db.session.delete(new_owner)
            db.session.commit()
            print("✅ Test owner deleted")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating owner: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    success = test_owner_creation()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")