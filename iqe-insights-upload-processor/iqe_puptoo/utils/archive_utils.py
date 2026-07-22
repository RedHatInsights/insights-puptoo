"""Utilities to handle insights archives."""

import os

from iqe.base.datafiles import get_data_path_for_plugin


def get_package_path(plugin_name: str) -> str:
    """Return the package path given a plugin name."""
    data_dir = get_data_path_for_plugin(plugin_name)
    return os.path.normpath(str(data_dir) + os.sep + os.pardir)


def get_archive_path(archive_filename: str, archive_base_dir: str) -> str:
    """Return the archive file path."""
    package_path = get_package_path(archive_base_dir)
    return os.path.join(package_path, "resources", "archives", archive_filename)
