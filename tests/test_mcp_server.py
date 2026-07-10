import pytest

from app import mcp_server


def test_widget_resource_requires_built_assets(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mcp_server, "WIDGET_DIST_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="run the widget build first"):
        mcp_server.load_widget_resource()


def test_widget_resource_inlines_local_built_assets(tmp_path, monkeypatch) -> None:
    (tmp_path / "talent-advisor-widget.js").write_text("window.widgetReady = true;", encoding="utf-8")
    (tmp_path / "talent-advisor-widget.css").write_text(":host { display: block; }", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "WIDGET_DIST_DIR", tmp_path)

    resource = mcp_server.load_widget_resource()

    assert "talent-advisor-widget" in resource
    assert "window.widgetReady = true;" in resource
    assert "display: block" in resource
    assert "LOCAL_ACCESS_TOKEN" not in resource
    assert "src=" not in resource


def test_widget_resource_csp_denies_external_domains() -> None:
    csp = mcp_server.WIDGET_RESOURCE_META["ui"]["csp"]

    assert csp == {"connectDomains": [], "frameDomains": [], "resourceDomains": []}
