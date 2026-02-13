import json
import os
import copy

from src.puptoo.upload import get_yum_updates_checksum, normalize_yum_updates


def load_yum_update_test_data():
    """Load test data from tests/yum_update.json"""
    test_file = os.path.join(os.path.dirname(__file__), "yum_update.json")
    with open(test_file, "r") as f:
        return json.load(f)


def test_checksum_deterministic():
    """Test that the same data always produces the same checksum"""
    yum_updates = load_yum_update_test_data()
    
    checksum1 = get_yum_updates_checksum(yum_updates)
    checksum2 = get_yum_updates_checksum(yum_updates)
    
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 hex digest is 64 characters
    assert isinstance(checksum1, str)


def test_checksum_normalization():
    """Test that reordered data produces the same checksum (normalization works)"""
    yum_updates = load_yum_update_test_data()
    
    # Create a reordered version by reversing available_updates lists
    # This tests that normalization properly sorts the arrays
    reordered = copy.deepcopy(yum_updates)
    
    # Find a package with multiple available_updates to test reordering
    test_pkg = None
    for pkg_name, pkg_data in reordered["update_list"].items():
        if isinstance(pkg_data, dict) and "available_updates" in pkg_data:
            if len(pkg_data["available_updates"]) > 1:
                test_pkg = pkg_name
                # Reverse the available_updates list
                original_list = pkg_data["available_updates"]
                reordered["update_list"][pkg_name]["available_updates"] = list(reversed(original_list))
                break
    
    assert yum_updates != reordered
    checksum_original = get_yum_updates_checksum(yum_updates)
    checksum_reordered = get_yum_updates_checksum(reordered)
    assert checksum_original == checksum_reordered


def test_checksum_dictionary_key_order():
    """Test that reordering update_list dictionary keys produces the same checksum"""
    yum_updates = load_yum_update_test_data()
    
    # Create a reordered version by reversing the order of keys in update_list
    reordered = copy.deepcopy(yum_updates)
    
    # Get original key order
    original_keys = list(yum_updates["update_list"].keys())
    
    # Reorder update_list dictionary keys in reverse order
    reordered["update_list"] = {}
    for key in reversed(original_keys):
        reordered["update_list"][key] = yum_updates["update_list"][key]
    
    # Verify the key order is actually different before normalization
    reordered_keys = list(reordered["update_list"].keys())
    assert original_keys != reordered_keys, "Dictionary keys should be in different order"
    assert len(original_keys) == len(reordered_keys), "Should have same number of keys"
    
    checksum_original = get_yum_updates_checksum(yum_updates)
    checksum_reordered = get_yum_updates_checksum(reordered)
    
    assert checksum_original == checksum_reordered


def test_checksum_different_data():
    """Test that different data produces different checksums"""
    yum_updates = load_yum_update_test_data()
    
    # Create modified version
    modified = yum_updates.copy()
    modified["releasever"] = "10"  # Change releasever
    
    checksum_original = get_yum_updates_checksum(yum_updates)
    checksum_modified = get_yum_updates_checksum(modified)
    
    assert checksum_original != checksum_modified


def test_normalize_yum_updates():
    """Test that normalization properly sorts keys and lists"""
    yum_updates = load_yum_update_test_data()
    
    normalized = normalize_yum_updates(yum_updates)
    
    # Check that top-level keys are sorted
    keys = list(normalized.keys())
    assert keys == sorted(keys)
    
    # Check that update_list keys are sorted
    if "update_list" in normalized:
        update_list_keys = list(normalized["update_list"].keys())
        assert update_list_keys == sorted(update_list_keys)
        
        # Check that available_updates lists are sorted
        for pkg_name, pkg_data in normalized["update_list"].items():
            if isinstance(pkg_data, dict) and "available_updates" in pkg_data:
                updates = pkg_data["available_updates"]
                # Verify sorting by checking adjacent items
                for i in range(len(updates) - 1):
                    curr = updates[i]
                    next_item = updates[i + 1]
                    curr_key = (
                        curr.get("package", ""),
                        curr.get("erratum", ""),
                        curr.get("repository", ""),
                    )
                    next_key = (
                        next_item.get("package", ""),
                        next_item.get("erratum", ""),
                        next_item.get("repository", ""),
                    )
                    assert curr_key <= next_key


def test_checksum_with_empty_update_list():
    """Test checksum calculation with empty update_list"""
    yum_updates = {
        "releasever": "9",
        "basearch": "x86_64",
        "update_list": {},
        "build_pkgcache": False,
    }
    
    checksum = get_yum_updates_checksum(yum_updates)
    assert len(checksum) == 64
    assert isinstance(checksum, str)


def test_checksum_with_single_package():
    """Test checksum with a single package in update_list"""
    yum_updates = {
        "releasever": "9",
        "basearch": "x86_64",
        "update_list": {
            "kernel-0:5.14.0-427.13.1.el9_4.x86_64": {
                "available_updates": [
                    {
                        "package": "kernel-0:5.14.0-427.16.1.el9_4.x86_64",
                        "repository": "rhel-9-for-x86_64-baseos-rpms",
                        "basearch": "x86_64",
                        "releasever": "9",
                        "erratum": "RHSA-2024:2758",
                    }
                ]
            }
        },
    }
    
    checksum = get_yum_updates_checksum(yum_updates)
    assert len(checksum) == 64
    assert isinstance(checksum, str)

