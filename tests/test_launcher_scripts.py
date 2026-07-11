from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_launcher_uses_hidden_local_startup_without_bypassing_execution_policy() -> None:
    script = (ROOT / "scripts" / "Start-TalentAdvisor.vbs").read_text(encoding="utf-8")

    assert "-WindowStyle Hidden" in script
    assert "ExecutionPolicy Bypass" not in script


def test_first_run_launcher_collects_key_without_printing_it() -> None:
    script = (ROOT / "scripts" / "Start-TalentAdvisor.ps1").read_text(encoding="utf-8")

    assert "PasswordChar" in script
    assert "RandomNumberGenerator" in script
    assert "Write-Host $apiKey" not in script


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
