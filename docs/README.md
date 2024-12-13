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
    pip install -r requirements.txt
    ```

    or

    ```sh
    pip install "fastapi[all]"
    pip install PyJWT
    pip install bcrypt
    pip install Faker
    pip install sqlmodel
    pip install deepface
    pip install ipykernel
    pip install pytest
    pip install isort
    ```

## Running the Application

1. **Start the FastAPI server:**

    ```sh
    fastapi run main # In development mode use fastapi dev main
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
