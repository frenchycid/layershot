from core.config import Config


def test_default_flux_url():
    cfg = Config()
    assert cfg.flux_url == "http://localhost:8190"


def test_default_data_paths():
    cfg = Config()
    assert cfg.moodboards_dir.name == "moodboards"
    assert cfg.outputs_dir.name == "outputs"
    assert cfg.prompts_dir.name == "prompts"


def test_default_views():
    cfg = Config()
    assert set(cfg.views) == {"wide", "closeup", "medium", "interior"}


def test_default_variants_per_view():
    cfg = Config()
    assert cfg.variants_per_view == 3


def test_custom_flux_url():
    cfg = Config(flux_url="http://myhost:9999")
    assert cfg.flux_url == "http://myhost:9999"
