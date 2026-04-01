import os
import sys
import glob

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Dataset, User, PlanetApplication
from init_database import init_categories
from merge_server_data import merge_all_server_data

def clean_sync():
    print("Starting Clean Sync V2...")
    print(f"CWD: {os.getcwd()}")
    
    # Target the known correct file which was renamed
    # We look for the most merged version
    json_file = 'merged_merged_merged_server_full_increment_20260126_2258.json'
    
    if os.path.exists(json_file):
        print(f"Using JSON file: {json_file}")
    else:
        print(f"Could not find the specific data file: {json_file}")
        # Debug list
        print("Files found (merged*.json):")
        for f in glob.glob('merged*.json'):
             print(f" - {f}")
        return
    
    app = create_app('development')
    
    with app.app_context():
        # 1. Clear Database
        print("Dropping all tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
        
        # 2. Init Categories (Only static data)
        # print("Initializing categories...")
        # init_categories()
        
        # 3. Merge Server Data
        print(f"Merging server data...")
        # Start merge
        success = merge_all_server_data(json_file, merge_files=True)
        
        if success:
            print("Merge successful.")
        else:
            print("Merge failed.")
            return

        # 4. Verify Counts
        d_count = Dataset.query.count()
        u_count = User.query.count()
        p_count = PlanetApplication.query.count()
        
        print(f"\nFinal Verification:")
        print(f"  Datasets: {d_count}")
        print(f"  Users:    {u_count}")
        print(f"  Apps:     {p_count}")
        
        if d_count == 430:
            print("Dataset count matches expected (430).")
        else:
            print(f"Dataset count mismatch! Expected 430, got {d_count}.")

if __name__ == '__main__':
    clean_sync()
