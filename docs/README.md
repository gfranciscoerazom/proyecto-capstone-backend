# Proyecto Integrador

For a AI generated documentation, please visit [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/gfranciscoerazom/proyecto-capstone-backend)

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
    python3.11 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Add the `.env` file:**

    Create a `.env` file in the root directory with the following content:

    ```properties
    # Type of environment: production, development, testing
    ENVIRONMENT=production

    # to get a secret key run:
    # openssl rand -hex 32
    SECRET_KEY="your_secret_key"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # URL to connect to the database
    DATABASE_URL="sqlite:///data/database.db"

    # Email configuration
    # Email that will send the emails
    EMAIL_SENDER="user@example.com"
    # App password of the email
    EMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"

    # Write token of logfire
    LOGS_TOKEN="xxxx_xx_xx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # Face recognition configuration
    # "VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib", "SFace", "GhostFaceNet", "Buffalo_L",
    FACE_RECOGNITION_AI_MODEL=Facenet
    # FACE_RECOGNITION_AI_THRESHOLD=0.5
    ```

## Running the Application

1. **Start the FastAPI server:**

    ```sh
    fastapi dev # In production use fastapi run
    ```

2. **Access the application:**
    Open your browser and navigate to `http://127.0.0.1:8000/docs`.

## Running the Application with Docker

1. Create this file structure:

    ```sh
    📁 .
    ├── 📁 data
    │   ├── 📁 events_imgs
    │   └── 📁 people_imgs
    └── 🐳 docker-compose.yml
    ```

2. Create the .env file in the root (see the point 4 of the installation section).

3. Add this YAML code to the `docker-compose.yml` file:

    ```yaml
    version: "3.8"

    services:
        backend:
            image: gfranciscoerazom/capstone-backend
            container_name: capstone-backend-container
            ports:
                - "8000:8000"
            volumes:
                - ./data/events_imgs:/code/data/events_imgs
                - ./data/people_imgs:/code/data/people_imgs
            env_file:
                - .env

        frontend:
            image: gfranciscoerazom/capstone-frontend
            container_name: capstone-frontend-container
            ports:
                - "8080:8080"
    ```

4. Run the following command to start the application:

    ```sh
    docker-compose up -d
    ```

5. Access the application:
    Open your browser and navigate to `http://127.0.0.1:8080/home`.

## Running Tests

1. **Run the tests using pytest:**

    ```sh
    pytest -n logical
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

## Documentation

The project documentation is available in the [wiki](https://github.com/gfranciscoerazom/proyecto-capstone-backend/wiki) tab of the repository.
