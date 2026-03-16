from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(self, config_dir: Path, version: str = "v1") -> None:
        self._version = version
        prompt_file = config_dir / f"prompts_{version}.yaml"
        with open(prompt_file) as f:
            self._prompts = yaml.safe_load(f)
        logger.info(f"Loaded prompts version {self._prompts.get('version', version)}")

    @property
    def version(self) -> str:
        return self._prompts.get("version", self._version)

    def get_system_instruction(self, stage: str, **kwargs: str) -> str:
        template = self._prompts[stage]["system"]
        return template.format(**kwargs)

    def get_user_prompt(self, stage: str, prompt_key: str = "user", **kwargs: str) -> str:
        template = self._prompts[stage][prompt_key]
        return template.format(**kwargs)
