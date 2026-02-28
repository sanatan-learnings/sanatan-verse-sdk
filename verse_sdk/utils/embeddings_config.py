"""Embeddings configuration utilities."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml


@dataclass
class EmbeddingsConfig:
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    output_dir: Optional[Path] = None
    index_path: Optional[Path] = None
    puranic_embeddings_dir: Optional[Path] = None
    max_input_chars: Optional[int] = None
    truncate_policy: Optional[str] = None


def _to_path(value: Optional[str], project_dir: Path) -> Optional[Path]:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = project_dir / path
    return path


def load_embeddings_config(project_dir: Path, config_path: Optional[Path]) -> Tuple[EmbeddingsConfig, Optional[Path]]:
    if config_path is None:
        candidate = project_dir / "_data" / "embeddings.yml"
        if not candidate.exists():
            return EmbeddingsConfig(), None
        config_path = candidate

    if not config_path.exists():
        raise FileNotFoundError(f"Embeddings config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    allowed_keys = {
        "active_provider",
        "active_model",
        "output_dir",
        "index_path",
        "puranic_embeddings_dir",
        "max_input_chars",
        "truncate_policy",
    }
    unknown = set(raw.keys()) - allowed_keys
    if unknown:
        raise ValueError(f"Unknown embeddings config keys: {', '.join(sorted(unknown))}")

    config = EmbeddingsConfig(
        active_provider=raw.get("active_provider"),
        active_model=raw.get("active_model"),
        output_dir=_to_path(raw.get("output_dir"), project_dir),
        index_path=_to_path(raw.get("index_path"), project_dir),
        puranic_embeddings_dir=_to_path(raw.get("puranic_embeddings_dir"), project_dir),
        max_input_chars=raw.get("max_input_chars"),
        truncate_policy=raw.get("truncate_policy"),
    )
    return config, config_path


def resolve_with_precedence(
    key: str,
    cli_value: Optional[Any],
    config_value: Optional[Any],
    env_value: Optional[Any],
    default_value: Optional[Any],
) -> Tuple[Optional[Any], Optional[str]]:
    if cli_value is not None:
        if config_value is not None:
            return cli_value, f"Using {key}={cli_value} from CLI flag (overrides config: {config_value})."
        if env_value is not None:
            return cli_value, f"Using {key}={cli_value} from CLI flag (overrides env: {env_value})."
        return cli_value, f"Using {key}={cli_value} from CLI flag."

    if config_value is not None:
        if env_value is not None:
            return config_value, f"Using {key}={config_value} from config (overrides env: {env_value})."
        return config_value, f"Using {key}={config_value} from config."

    if env_value is not None:
        return env_value, f"Using {key}={env_value} from environment."

    return default_value, None
