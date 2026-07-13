from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_command_launcher_uses_hidden_local_startup_without_bypassing_execution_policy() -> None:
    script = (ROOT / "scripts" / "Start-TalentAdvisor.cmd").read_text(encoding="utf-8")

    assert "powershell.exe" in script
    assert "Start-TalentAdvisor.ps1" in script
    assert "-WindowStyle Hidden" in script
    assert "ExecutionPolicy Bypass" not in script
    assert "wscript" not in script.lower()


def test_first_run_launcher_configures_local_model_without_collecting_or_printing_a_key() -> None:
    script = (ROOT / "scripts" / "Start-TalentAdvisor.ps1").read_text(encoding="utf-8")

    assert "RandomNumberGenerator" in script
    assert "Get-OpenAIKey" not in script
    assert "OPENAI_API_KEY=$apiKey" not in script
    assert "MODEL_PROVIDER=ollama" in script
    assert "LOCAL_MODEL_NAME=qwen3:8b" in script


def test_launcher_has_graphical_prerequisite_and_repeat_run_safeguards() -> None:
    script = (ROOT / "scripts" / "Start-TalentAdvisor.ps1").read_text(encoding="utf-8")

    assert "Confirm-Action" in script
    assert "Require-Command 'node'" in script
    assert "Require-Command 'pnpm'" in script
    assert "& $node --version" in script
    assert "& $pnpm --version" in script
    assert "Docker Desktop" in script
    assert "Test-ConfiguredPort" in script
    assert "No data was reset" in script
    assert "Add-EnvironmentValue" in script
    assert "Test-LocalModelReadiness" in script
    assert "Invoke-RestMethod" in script
    assert "about 5.2 GB" in script
    assert "Confirm-Action 'Talent Advisor needs to download qwen3:8b" in script
    assert "& $ollama pull qwen3:8b" in script
