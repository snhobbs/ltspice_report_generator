import tomllib
from pathlib import Path

CONFIG_PATH = Path.cwd() / "project.toml"
PROJECT_ROOT = CONFIG_PATH.parent
PACKAGE_DIR = Path(__file__).parent


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def resolve(path_str: str) -> Path:
    return (PROJECT_ROOT / path_str).resolve()


def filter_circuits(circuits: list[dict], slug: str | None) -> list[dict]:
    if slug is None:
        return circuits
    matches = [c for c in circuits if c["slug"] == slug]
    if not matches:
        raise ValueError(f"No circuit with slug '{slug}'")
    return matches
