import hashlib
import base64
import os
import shutil

def create_image_directory(user_email:str): 
    """
    Creates a directory for the user's image objects (charts and tables)
    """
    # Create folder where image objects (charts and tables) will be stored
    dir_name = create_safe_identifier_from_email(user_email)

    # Wipe the directory clean
    full_path = os.path.join('resources/nielsen/imageDump/', dir_name)
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
        #print(f'Deleted existing directory: {full_path}')
    else:
        pass
        #print(f'Directory not found: {full_path}')

    # Create a unique directory for each user
    base_path = 'resources/nielsen/imageDump/'
    full_path = os.path.join(base_path, dir_name)
    if not os.path.exists(full_path):
        os.mkdir(full_path)
        #print(f'Created dir to dump images at: {full_path}')
    else: 
        #print('Imgdump Path already exists.')
        pass

    return full_path + '/'


def create_eml_directory(user_email:str):
    """
    Creates a directory for the user's eml files
    """
    # Create folder where eml files will be stored
    dir_name = create_safe_identifier_from_email(user_email)

    # Wipe the directory clean
    full_path = os.path.join('resources/nielsen/emlDump/', dir_name)
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
        #print(f'Deleted existing directory: {full_path}')
    else:
        pass
        #print(f'Directory not found: {full_path}')
    
    # Create a unique directory for each user
    base_path = 'resources/nielsen/emlDump/'
    full_path = os.path.join(base_path, dir_name)
    if not os.path.exists(full_path):
        os.mkdir(full_path)
        #print(f'Created dir to dump eml files at: {full_path}')
    else: 
        #print('Emldump Path already exists.')
        pass
    
    return full_path + '/'
    


def create_safe_identifier_from_email(email, length=10):
    """
    Converts a user's email to a safe identifier used for the image dump directory. 

    ie. Converts 'jack.driscoll@charter.com' to 'jckdrc0llchtrc'
    """
    # Convert email to lowercase
    email = email.lower()
    
    # Create a SHA-256 hash of the email
    hash_object = hashlib.sha256(email.encode())
    hash_digest = hash_object.digest()
    
    # Convert the hash to a URL-safe base64 string
    safe_id = base64.urlsafe_b64encode(hash_digest).decode('utf-8')
    
    # Remove any padding characters and return the first 'length' characters
    return safe_id.rstrip('=')[:length]


