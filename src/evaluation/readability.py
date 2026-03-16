from __future__ import annotations

import textstat

from src.schemas.story import ReadabilityScores, StoryOutput


GRADE_TARGETS = {
    3: (3.0, 4.0),
    4: (4.0, 5.0),
    5: (5.0, 6.0),
    6: (6.0, 7.0),
}
TOLERANCE = 1.0


def assess(story: StoryOutput, target_grade: int) -> ReadabilityScores:
    text = story.full_text
    fk = textstat.flesch_kincaid_grade(text)
    dc = textstat.dale_chall_readability_score(text)

    low, high = GRADE_TARGETS.get(target_grade, (target_grade, target_grade + 1))
    within = (low - TOLERANCE) <= fk <= (high + TOLERANCE)

    return ReadabilityScores(
        flesch_kincaid_grade=round(fk, 2),
        dale_chall_grade=round(dc, 2),
        target_grade=target_grade,
        within_tolerance=within,
    )
