from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel

PACKAGE_DIR = Path(__file__).parent
_project_root: Path = Path.cwd()


class PlotConfig(BaseModel):
    label: str
    title: str = ""
    vars: list[str] = []
    db: bool = False
    description: str = ""


class CircuitConfig(BaseModel):
    slug: str
    name: str
    asc: str
    input_node: str
    output_node: str
    test_suite: str = ""
    existing_sim_dir: str = ""
    plots: list[PlotConfig] = []
    description: str = ""


class PathsConfig(BaseModel):
    build: str
    report: str
    hugo_root: str = ".."
    ltspice_to_svg: str = "ltspice_to_svg"


class ReportConfig(BaseModel):
    template: str = ""   # "hugo", "plain", or a path to a .j2 file
    path: str


class ProjectConfig(BaseModel):
    name: str
    title: str
    paths: PathsConfig
    description: str = ""
    date: str = "2026-01-01"
    part_number: str = ""
    categories: list[str] = ["product"]
    tags: list[str] = ["hardware"]
    template: str = ""
    reports: list[ReportConfig] = []


class Config(BaseModel):
    project: ProjectConfig
    circuits: list[CircuitConfig] = []


def load_config(config_path: Path | None = None) -> Config:
    global _project_root
    if config_path is None:
        config_path = Path.cwd() / "project.toml"
    _project_root = Path(config_path).resolve().parent
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    return Config.model_validate(raw)


def resolve(path_str: str) -> Path:
    return (_project_root / path_str).resolve()


def filter_circuits(circuits: list[CircuitConfig], slug: str | None) -> list[CircuitConfig]:
    if slug is None:
        return circuits
    matches = [c for c in circuits if c.slug == slug]
    if not matches:
        raise ValueError(f"No circuit with slug '{slug}'")
    return matches
