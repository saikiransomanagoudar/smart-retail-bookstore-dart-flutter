# Smart Retail Bookstore 📚

A modern bookstore application built with Flutter, FastAPI, and AI-powered recommendations.

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
- **Styling:** TailwindCSS

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
DATABASE_URL=postgresql://username:password@localhost/smart_retail_bookstore
OPENAI_API_KEY=your_openai_api_key
HARDCOVER_API_URL=your_hardcover_api_url
HARDCOVER_API_TOKEN=your_hardcover_api_token
```

#### Start Backend Server
```bash
cd root/backend/app
python app.py
```

### 2. Frontend Setup

#### Install Dart SDK (Windows)
```powershell
choco install dart-sdk
```

#### Project Dependencies
Update your `pubspec.yaml` with the following dependencies:
```yaml
environment:
  sdk: ^3.4.0

dependencies:
  flutter:
    sdk: flutter
  file_picker: ^5.0.0
  go_router: ^6.0.0
  http: ^1.2.2
  provider: ^6.1.2
  shared_preferences: ^2.3.3
  url_launcher: ^6.1.14
  carousel_slider: ^4.2.1
  flip_card: ^0.6.0
  font_awesome_flutter: ^10.1.0

dev_dependencies:
  lints: ^3.0.0
  test: ^1.24.0

flutter:
  uses-material-design: true
  assets:
    - assets/images/
  fonts:
    - family: NotoSans
      fonts:
        - asset: assets/fonts/NotoSans-Regular.ttf
        - asset: assets/fonts/NotoSans-Bold.ttf
    - family: MaterialIcons
      fonts:
        - asset: assets/fonts/MaterialIcons-Regular.otf
```

#### Start Frontend Application
```bash
flutter clean
flutter pub get
flutter run -d chrome web-port 55117
```

