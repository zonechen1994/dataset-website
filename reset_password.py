import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, User

def reset_password(username, new_password):
    app = create_app('development')
    
    with app.app_context():
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"✅ Found user: {username}")
            user.set_password(new_password)
            db.session.commit()
            print(f"✅ Password for '{username}' has been reset to '{new_password}'")
        else:
            print(f"❌ User '{username}' not found!")
            # List some users to be helpful
            print("  Available users (first 10):")
            users = User.query.limit(10).all()
            for u in users:
                print(f"  - {u.username}")

if __name__ == '__main__':
    # Reset for qiaomaicuicui
    reset_password('qiaomaicuicui', 'qiaomaicuicui')
