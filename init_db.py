from app import app, db
from models import User, Institute
from werkzeug.security import generate_password_hash

def initialize_data():
    # Sample data for institutes
    institutes = ['Institute A', 'Institute B']

    with app.app_context():
        # Create the necessary tables if they do not exist
        db.create_all()

        # Prepopulate the Institute table
        for institute_name in institutes:
            institute = Institute.query.filter_by(name=institute_name).first()
            if not institute:
                new_institute = Institute(name=institute_name)
                db.session.add(new_institute)

        # Example for creating a master admin user for each institute
        for institute_name in institutes:
            institute = Institute.query.filter_by(name=institute_name).first()
            if institute:
                master_admin = User.query.filter_by(username=f'master_{institute_name}').first()
                if not master_admin:
                    master_admin = User(
                        username=f'master_{institute_name}',
                        password=generate_password_hash('securepassword'),  # Hash the password
                        user_type='master_admin',
                        institute=institute
                    )
                    db.session.add(master_admin)

        db.session.commit()  # Commit all changes

if __name__ == '__main__':
    initialize_data()  # Call the initialization function
