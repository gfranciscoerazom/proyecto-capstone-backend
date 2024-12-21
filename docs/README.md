# Proyecto Integrador

## Description

This project is a FastAPI-based application that provides user authentication and management functionalities.

## Requirements

- Python 3.11

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/gfranciscoerazom/proyecto-capstone-backend.git
    cd proyecto-capstone-backend
    ```

2. **Create and activate a virtual environment:**

    ```sh
    python -m .venv venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements-[windows|linux].txt
    ```

    or

    ```sh
    pip install "fastapi[all]" PyJWT bcrypt Faker sqlmodel deepface ipykernel pytest isort tf-keras
    ```

4. **Add the `.env` file:**

    Create a `.env` file in the root directory with the following content:

    ```properties
    # to get a secret key run:
    # openssl rand -hex 32
    SECRET_KEY="your_secret_key"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    DATABASE_URL="sqlite:///data/database.db"
    ```

## Running the Application

1. **Start the FastAPI server:**

    ```sh
    fastapi dev main # In production use fastapi run main
    ```

2. **Access the application:**
    Open your browser and navigate to `http://127.0.0.1:8000`.

## Running Tests

1. **Run the tests using pytest:**

    ```sh
    pytest
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Documentation

The project documentation is available in the [wiki](https://github.com/gfranciscoerazom/proyecto-capstone-backend/wiki) tab of the repository.
