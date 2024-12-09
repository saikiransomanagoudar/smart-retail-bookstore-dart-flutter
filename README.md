# Smart Retail Bookstore 📚

A modern bookstore application built with Flutter, FastAPI, and AI-powered recommendations.

## Architecture
![architecture](https://github.com/user-attachments/assets/92840ea2-3827-41eb-b65e-4f9c939ac47d)


## Technology Stack 🛠️

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **AI Integration:** 
  - LangGraph
  - LangChain
  - OpenAI API

### Frontend
- **Framework:** Flutter/Dart

### External APIs
- Hardcover GraphQL API for book metadata

## Prerequisites 📋

Before you begin, ensure you have the following installed:
- Python 3.8+
- PostgreSQL
- Dart SDK
- Flutter Framework
- Chocolatey (Windows)

## Installation Guide 🚀

### 1. Backend Setup

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup
```sql
-- Create database
CREATE DATABASE smart_retail_bookstore;

-- Create users table
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create user_preferences table
CREATE TABLE user_preferences (
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    order_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    total_quantity INTEGER NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    card_number TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    purchase_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expected_shipping_date TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

-- Create orders table
CREATE TABLE orders (
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    order_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    total_quantity INTEGER NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    card_number TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    purchase_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expected_shipping_date TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
```

#### Environment Configuration
Create a `.env` file in the root directory with the following contents:
```env
DATABASE_URL=postgresql://username:password@localhost/book_recommendations
OPENAI_API_KEY=your_openai_api_key
HARDCOVER_API_URL=your_hardcover_api_url
HARDCOVER_API_TOKEN=Bearer {token}
```

#### Start Backend Server
```bash
cd smart_retail_bookstore/backend/app
python app.py
```

### 2. Frontend Setup

#### Install Dart SDK (Windows)
```powershell
choco install dart-sdk
```

#### Start Frontend Application
```bash
flutter clean
flutter pub get
flutter run -d chrome web-port 55117
```

