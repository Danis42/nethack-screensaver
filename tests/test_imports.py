def test_autoascend_agent_imports():
    from autoascend import agent

    assert hasattr(agent, "Agent")
    assert hasattr(agent, "BLStats")


def test_no_heavy_deps_loaded():
    import sys

    import autoascend.agent  # noqa: F401

    for mod in ("torch", "ray", "matplotlib", "seaborn", "pandas", "nltk", "gym"):
        assert mod not in sys.modules, f"{mod} must not be imported"
