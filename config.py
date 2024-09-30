import os

class Config:
    SECRET_KEY = 'SDE_M23AID007'  # Use a more secure key in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False  # Suitable for local development; change this in production
    SESSION_COOKIE_SAMESITE = 'Lax'  # Helps with cross-site request protection
    SESSION_TYPE = 'filesystem'  # Store session data on the local file system

    # Prefix for tenant-specific database file paths (e.g., tenant_1.db, tenant_2.db, etc.)
    TENANT_DATABASE_PREFIX = 'sqlite:///tenant_'
    DEFAULT_TENANT = 'default'  # Default tenant used if no specific tenant is determined

    # Path to the main database (metadata about tenants or other shared data)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///polling_platform.db'

    # Path to the directory containing CSV files
    CSV_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Database')  # Update this as needed

    # Chrome user data base path for profiles
    CHROME_USER_DATA_BASE_PATH = os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/"

    @classmethod
    def get_tenant_db_uri(cls, tenant_id):
        """
        Returns the database URI for a specific tenant.
        
        Parameters:
            tenant_id (str): The identifier of the tenant (e.g., tenant_1, tenant_2).
        
        Returns:
            str: The database URI for the given tenant.
        """
        if tenant_id:
            return f'{cls.TENANT_DATABASE_PREFIX}{tenant_id}.db'
        else:
            return f'{cls.TENANT_DATABASE_PREFIX}{cls.DEFAULT_TENANT}.db'


class DevelopmentConfig(Config):
    DEBUG = True  # Enable debug mode for local development
