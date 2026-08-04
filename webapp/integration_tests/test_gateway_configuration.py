import importlib

from webapp.gateway import main


def test_gateway_uses_local_service_defaults(monkeypatch):
    with monkeypatch.context() as environment:
        environment.delenv("STATIC_ANALYSIS_SERVICE", raising=False)
        environment.delenv("REPORT_SERVICE", raising=False)

        gateway = importlib.reload(main)

        assert gateway.STATIC_ANALYSIS_SERVICE == "http://localhost:8002"
        assert gateway.REPORT_SERVICE == "http://localhost:8003"

    importlib.reload(main)


def test_gateway_uses_configured_service_urls(monkeypatch):
    with monkeypatch.context() as environment:
        environment.setenv(
            "STATIC_ANALYSIS_SERVICE", "http://static_analysis_service:8002"
        )
        environment.setenv("REPORT_SERVICE", "http://report_service:8003")

        gateway = importlib.reload(main)

        assert (
            gateway.STATIC_ANALYSIS_SERVICE
            == "http://static_analysis_service:8002"
        )
        assert gateway.REPORT_SERVICE == "http://report_service:8003"

    importlib.reload(main)
