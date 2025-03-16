import pathlib as pl


def safe_path_join(base_dir: pl.Path, add_to_base_dir: str) -> pl.Path:
    full_path: pl.Path = base_dir / pl.Path(add_to_base_dir)
    normalized_full_path: pl.Path = full_path.resolve()
    if not normalized_full_path.is_relative_to(base_dir.resolve()):
        raise ValueError("Path traversal detected")
    return normalized_full_path
