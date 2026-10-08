def test_render_low_resource_settings_are_explicit(monkeypatch):
    from clipdock.api import Settings

    monkeypatch.setenv("CLIPDOCK_CONCURRENCY", "1")
    monkeypatch.setenv("CLIPDOCK_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("CLIPDOCK_MAX_DURATION_SECONDS", "120")
    monkeypatch.setenv("CLIPDOCK_MAX_FILE_BYTES", "16777216")
    monkeypatch.setenv("CLIPDOCK_DISK_BUDGET_BYTES", "134217728")
    settings = Settings.from_env()
    assert (
        settings.concurrency,
        settings.timeout,
        settings.max_duration,
        settings.max_file,
        settings.disk_budget,
    ) == (1, 60, 120, 16777216, 134217728)
