# instrumented_app.py

from prometheus_fastapi_instrumentator import Instrumentator
from main import app   # tu FastAPI original

# Configuramos la instrumentación
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
).instrument(app).expose(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "instrumented_app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # anyio_backend="uvloop"  # opcional
    )
