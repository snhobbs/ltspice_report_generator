from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field

PACKAGE_DIR = Path(__file__).parent
_project_root: Path = Path.cwd()


class PlotConfig(BaseModel):
    label: str
    title: str = ""
    filename: str = ""  # output PNG stem; defaults to label
    raw: str = ""  # source .raw file stem; defaults to filename/label
    vars: list[str] = []
    right_vars: list[str] = []  # if non-empty, rendered on a twin y-axis
    db: bool = False
    description: str = ""

    @property
    def stem(self) -> str:
        return self.filename or self.label

    @property
    def raw_stem(self) -> str:
        return self.raw or self.label


class CircuitConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asc: str
    slug: str = ""
    name: str = ""
    input_node: str
    input_node_minus: str = "0"
    output_node: str
    input_source: str = "VIN"
    lib_dir: str = ""
    existing_sim_dir: str = ""

    @model_validator(mode="after")
    def _default_lib_dir(self) -> "CircuitConfig":
        if not self.lib_dir:
            self.lib_dir = str(Path(self.asc).parent)
        if not self.slug:
            self.slug = str(Path(self.asc).stem)
        if not self.name:
            self.name = str(Path(self.asc).stem).title()
        return self

    plots: list[PlotConfig] = Field(default_factory=list)
    description: str = ""
    suite_type: str = ""  # TOML-only fallback
    suite_instance: Any = (
        None  # set in Python configs; takes precedence over suite_type
    )

    def suite(self) -> list:
        if self.suite_instance is not None:
            return self.suite_instance.suite(
                self.input_source,
                self.input_node,
                self.output_node,
                input_node_minus=self.input_node_minus,
            )
        if self.suite_type:
            from .suites import _SUITE_REGISTRY

            fn = _SUITE_REGISTRY.get(self.suite_type)
            if fn is None:
                raise ValueError(f"Unknown suite_type '{self.suite_type}'")
            return fn(self.input_source, self.input_node, self.output_node)
        raise NotImplementedError(f"{type(self).__name__} must implement suite()")


class PathsConfig(BaseModel):
    build: str
    report: str
    hugo_root: str = ".."
    ltspice_to_svg: str = "ltspice_to_svg"


class ReportConfig(BaseModel):
    template: str = ""  # "hugo", "plain", or a path to a .j2 file
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


def filter_circuits(
    circuits: list[CircuitConfig], slug: str | None
) -> list[CircuitConfig]:
    if slug is None:
        return circuits
    matches = [c for c in circuits if c.slug == slug]
    if not matches:
        raise ValueError(f"No circuit with slug '{slug}'")
    return matches
