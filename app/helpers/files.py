import pathlib as pl

from werkzeug.utils import secure_filename


def safe_path_join(base_dir: pl.Path, add_to_base_dir: str) -> pl.Path:
    base_dir = base_dir.resolve()

    sanitized_add_to_base_dir = secure_filename(add_to_base_dir)
    full_path: pl.Path = base_dir / pl.Path(sanitized_add_to_base_dir)
    normalized_full_path: pl.Path = full_path.resolve()

    if not str(normalized_full_path).startswith(str(base_dir)):
        raise ValueError("Path traversal detected")

    return normalized_full_path
