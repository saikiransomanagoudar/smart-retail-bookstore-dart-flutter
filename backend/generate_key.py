import secrets

def generate_jwt_secret():
    # Generate a 32-byte (256-bit) random key
    jwt_secret = secrets.token_hex(32)
    print("\nYour JWT Secret Key:")
    print(jwt_secret)
    print("\nAdd this to your .env file as:")
    print(f"JWT_SECRET_KEY={jwt_secret}")

if __name__ == "__main__":
    generate_jwt_secret()