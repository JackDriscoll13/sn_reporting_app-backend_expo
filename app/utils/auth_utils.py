import bcrypt

# Passlib is deprecated, switching to raw bcrypt
# from: https://github.com/pyca/bcrypt/issues/684

# Hash a password using bcrypt
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    hashed_password_str = hashed_password.decode('utf-8')
    return hashed_password_str

# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if the provided password matches the stored password (hashed).

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_byte_enc)

if __name__ == "__main__":
    hash_password("Mako1234")