from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from src.evaluation.readability import assess
from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.llm.rate_limiter import ModelLimit, RateLimiter
from src.schemas.critique import CritiqueResult
from src.schemas.outline import StoryOutline
from src.schemas.safety import SafetyCheckResult
from src.schemas.story import StoryOutput
from src.utils.io import create_run_dir, generate_run_id, load_json, save_json

from . import (
    critique_stage,
    generation_stage,
    outline_stage,
    revision_stage,
    safety_stage,
)

logger = logging.getLogger(__name__)


class StoryPipeline:
    def __init__(
        self, config_dir: str | Path, api_key: str, fast: bool = False
    ) -> None:
        self.config_dir = Path(config_dir)
        self.fast = fast

        with open(self.config_dir / "models.yaml") as f:
            self._models_cfg = yaml.safe_load(f)
        with open(self.config_dir / "pipeline.yaml") as f:
            self._pipeline_cfg = yaml.safe_load(f)

        prompt_version = self._pipeline_cfg.get("prompt_version", "v1")
        self.prompts = PromptManager(self.config_dir, version=prompt_version)

        # Build rate limiter
        limits: dict[str, ModelLimit] = {}
        for key, mcfg in self._models_cfg["models"].items():
            limits[mcfg["name"]] = ModelLimit(
                rpm=mcfg["rpm"],
                rpd=mcfg["rpd"],
                min_spacing=mcfg["min_call_spacing_seconds"],
            )
        self.rate_limiter = RateLimiter(limits)
        self.client = GeminiClient(api_key, self.rate_limiter)

        self.output_base = Path("output")

    def _model_name(self, stage: str) -> str:
        stage_key = stage
        if stage == "critique" and self.fast:
            stage_key = "critique_fast"
        model_key = self._models_cfg["stage_models"][stage_key]
        return self._models_cfg["models"][model_key]["name"]

    def _fallback_model(self, stage: str) -> str | None:
        model_key = self._models_cfg["stage_models"].get(stage)
        if model_key and model_key in self._models_cfg.get("fallback", {}):
            fb_key = self._models_cfg["fallback"][model_key]
            return self._models_cfg["models"][fb_key]["name"]
        return None

    def _detect_stage(self, run_dir: Path) -> str:
        """Detect which stage to resume from based on existing artifacts."""
        if (run_dir / "final/story_final.json").exists():
            return "done"
        if any((run_dir / "revised").glob("*.json")):
            return "safety"
        if any((run_dir / "critiques").glob("*.json")):
            return "revision"
        if any((run_dir / "versions").glob("*.json")):
            return "critique"
        if (run_dir / "outline_approved.json").exists():
            return "generation"
        if (run_dir / "outline.json").exists():
            return "review"
        return "outline"

    def run(
        self,
        location: str,
        culture_context: str,
        target_grade: int,
        review_callback=None,
        resume_run_id: str | None = None,
    ) -> str:
        if resume_run_id:
            run_id = resume_run_id
            run_dir = self.output_base / run_id
            if not run_dir.exists():
                raise FileNotFoundError(f"Run directory not found: {run_dir}")
            stage = self._detect_stage(run_dir)
            logger.info(f"Resuming pipeline run {run_id} from stage: {stage}")
        else:
            run_id = generate_run_id()
            run_dir = create_run_dir(self.output_base, run_id)
            stage = "outline"
            logger.info(f"Starting pipeline run {run_id}")

        gen_cfg = self._pipeline_cfg["generation"]
        num_versions = gen_cfg["num_versions"]

        # Stage 1: Outline
        if stage == "outline":
            outline = outline_stage.generate_outline(
                client=self.client,
                prompts=self.prompts,
                model=self._model_name("outline"),
                location=location,
                culture_context=culture_context,
                target_grade=target_grade,
            )
            save_json(outline.model_dump(), run_dir / "outline.json")
            stage = "review"

        # HITL Review
        if stage == "review":
            outline = StoryOutline.model_validate(
                load_json(run_dir / "outline.json")
            )
            if review_callback:
                outline = review_callback(outline)
            save_json(outline.model_dump(), run_dir / "outline_approved.json")
            stage = "generation"

        outline = StoryOutline.model_validate(
            load_json(run_dir / "outline_approved.json")
        )

        # Stage 2: Generation
        if stage == "generation":
            stories = generation_stage.generate_stories(
                client=self.client,
                prompts=self.prompts,
                model=self._model_name("generation"),
                outline=outline,
                run_id=run_id,
                temperatures=gen_cfg["temperatures"],
                word_count_min=gen_cfg["word_count_min"],
                word_count_max=gen_cfg["word_count_max"],
                target_grade=target_grade,
            )
            for i, s in enumerate(stories):
                save_json(s.model_dump(), run_dir / f"versions/story_v{i + 1}.json")
            stage = "critique"

        # Load stories from disk
        stories = []
        for i in range(1, num_versions + 1):
            p = run_dir / f"versions/story_v{i}.json"
            if p.exists():
                stories.append(StoryOutput.model_validate(load_json(p)))

        # Stage 3: Critique
        if stage == "critique":
            critiques = critique_stage.critique_stories(
                client=self.client,
                prompts=self.prompts,
                model=self._model_name("critique"),
                stories=stories,
                target_grade=target_grade,
                fallback_model=self._fallback_model("critique"),
            )
            for i, c in enumerate(critiques):
                save_json(c.model_dump(), run_dir / f"critiques/critique_v{i + 1}.json")
            stage = "revision"

        # Load critiques from disk
        critiques = []
        for i in range(1, num_versions + 1):
            p = run_dir / f"critiques/critique_v{i}.json"
            if p.exists():
                critiques.append(CritiqueResult.model_validate(load_json(p)))

        # Stage 4: Revision
        if stage == "revision":
            revised = revision_stage.revise_stories(
                client=self.client,
                prompts=self.prompts,
                model=self._model_name("revision"),
                stories=stories,
                critiques=critiques,
                target_grade=target_grade,
                word_count_min=gen_cfg["word_count_min"],
                word_count_max=gen_cfg["word_count_max"],
            )
            for i, r in enumerate(revised):
                save_json(
                    r.model_dump(), run_dir / f"revised/story_v{i + 1}_revised.json"
                )
            stage = "safety"

        # Load revised stories from disk
        revised = []
        for i in range(1, num_versions + 1):
            p = run_dir / f"revised/story_v{i}_revised.json"
            if p.exists():
                revised.append(StoryOutput.model_validate(load_json(p)))

        # Stage 5: Safety + Readability + Selection
        if stage == "safety":
            sel_cfg = self._pipeline_cfg["selection"]["weights"]
            best_story, best_score = None, -1.0
            safety_results: list[SafetyCheckResult] = []

            for i, story in enumerate(revised):
                # Readability
                readability = assess(story, target_grade)
                story.readability = readability

                # Safety (only check best candidate to save API calls)
                safety = safety_stage.check_safety(
                    client=self.client,
                    prompts=self.prompts,
                    model=self._model_name("safety"),
                    story=story,
                    target_grade=target_grade,
                )
                safety_results.append(safety)

                # Score
                critique_score = critiques[i].overall_score / 5.0
                read_score = 1.0 if readability.within_tolerance else 0.5
                safety_score = 1.0 if safety.passed else 0.0

                weighted = (
                    critique_score * sel_cfg["critique"]
                    + read_score * sel_cfg["readability"]
                    + safety_score * sel_cfg["safety"]
                )

                logger.info(
                    f"Version {i + 1}: critique={critique_score:.2f}, "
                    f"readability={read_score:.2f}, safety={safety_score:.2f}, "
                    f"weighted={weighted:.2f}"
                )

                if weighted > best_score and safety.passed:
                    best_score = weighted
                    best_story = story

            save_json(
                [s.model_dump() for s in safety_results],
                run_dir / "safety/safety_report.json",
            )

            if best_story is None:
                logger.warning(
                    "No story passed safety check — selecting highest-scoring"
                )
                best_idx = max(
                    range(len(critiques)),
                    key=lambda j: critiques[j].overall_score,
                )
                best_story = revised[best_idx]

            save_json(best_story.model_dump(), run_dir / "final/story_final.json")

        logger.info(f"Pipeline complete. Final story saved to {run_dir}/final/")
        return run_id
