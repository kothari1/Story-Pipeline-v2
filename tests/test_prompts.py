from src.llm.prompts import PromptManager


def test_load_prompts(config_dir):
    pm = PromptManager(config_dir, version="v1")
    assert pm.version == "v1"


def test_system_instruction_rendering(config_dir):
    pm = PromptManager(config_dir, version="v1")
    system = pm.get_system_instruction("outline", location_type="rural")
    assert "rural" in system
    assert "storyteller" in system.lower()


def test_user_prompt_rendering(config_dir):
    pm = PromptManager(config_dir, version="v1")
    prompt = pm.get_user_prompt(
        "outline",
        prompt_key="user_cot",
        target_grade="4",
        location="a village in Karnataka",
        culture_context="Tulu-speaking fishing community",
    )
    assert "Grade 4" in prompt
    assert "Karnataka" in prompt
    assert "Tulu" in prompt


def test_generation_prompt(config_dir):
    pm = PromptManager(config_dir, version="v1")
    system = pm.get_system_instruction(
        "generation",
        target_grade="4",
        word_count_min="500",
        word_count_max="800",
        age_min="9",
        age_max="10",
    )
    assert "500" in system
    assert "800" in system


def test_critique_prompt(config_dir):
    pm = PromptManager(config_dir, version="v1")
    system = pm.get_system_instruction(
        "critique",
        target_grade="4",
        age_min="9",
        age_max="10",
    )
    assert "reading specialist" in system.lower()
