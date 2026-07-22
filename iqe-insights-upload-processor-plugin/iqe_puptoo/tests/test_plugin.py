"""Test plugin is accessible."""


def test_plugin_accessible(application):
    """Test plugin is accessible from application.

    metadata:
        requirements: not_applicable
        assignee: nobody
        importance: low
    """
    assert hasattr(application, "puptoo")
