from insights.specs import Specs
from insights.tests import InputData, run_test

from src.puptoo.process.profile import system_profile


DATA_0 = """
    {
    "deployments" : [
        {
        "base-commit-meta" : {
            "rpmostree.inputhash" : "d272136f0a700a049da30520591205fec5474125474a58a4c9a63ecc8243f227"
        },
        "requested-local-packages" : [
        ],
        "base-removals" : [
        ],
        "unlocked" : "none",
        "booted" : true,
        "initramfs-etc" : [
        ],
        "id" : "rhel-f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267.0",
        "osname" : "rhel",
        "origin" : "edge:rhel/8/x86_64/edge",
        "pinned" : false,
        "regenerate-initramfs" : false,
        "base-local-replacements" : [
        ],
        "checksum" : "f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267",
        "requested-base-local-replacements" : [
        ],
        "timestamp" : 1614717652,
        "requested-packages" : [
        ],
        "serial" : 0,
        "packages" : [
        ],
        "gpg-enabled" : false,
        "requested-base-removals" : [
        ]
        }
    ],
    "transaction" : null,
    "cached-update" : null
    }
""".strip()

DATA_1 = """
    {
    "deployments" : [
        {
        "base-commit-meta" : {
            "rpmostree.inputhash" : "d272136f0a700a049da30520591205fec5474125474a58a4c9a63ecc8243f227"
        },
        "requested-local-packages" : [
        ],
        "base-removals" : [
        ],
        "unlocked" : "none",
        "booted" : true,
        "initramfs-etc" : [
        ],
        "id" : "rhel-f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267.0",
        "osname" : "rhel",
        "origin" : "edge:rhel/8/x86_64/edge",
        "pinned" : false,
        "regenerate-initramfs" : false,
        "base-local-replacements" : [
        ],
        "checksum" : "f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267",
        "requested-base-local-replacements" : [
        ],
        "timestamp" : 1614717652,
        "requested-packages" : [
        ],
        "serial" : 0,
        "packages" : [
        ],
        "gpg-enabled" : false,
        "requested-base-removals" : [
        ]
        },
        {
        "base-commit-meta" : {
            "rpmostree.inputhash" : "d272136f0a700a049da30520591205fec5474125474a58a4c9a63ecc8243f227"
        },
        "requested-local-packages" : [
        ],
        "base-removals" : [
        ],
        "unlocked" : "none",
        "booted" : true,
        "initramfs-etc" : [
        ],
        "id" : "rhel-f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267.0",
        "osname" : "rhel",
        "origin" : "edge:rhel/8/x86_64/edge",
        "pinned" : false,
        "regenerate-initramfs" : false,
        "base-local-replacements" : [
        ],
        "checksum" : "f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267",
        "requested-base-local-replacements" : [
        ],
        "timestamp" : 1614717652,
        "requested-packages" : [
        ],
        "serial" : 0,
        "packages" : [
        ],
        "gpg-enabled" : false,
        "requested-base-removals" : [
        ]
        }
    ],
    "transaction" : null,
    "cached-update" : null
    }
""".strip()


def test_rpmostree_status_simple():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_0)
    result = run_test(system_profile, input_data)
    assert result["host_type"] == "edge"


def test_rpmostree_status_full():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_1)
    result = run_test(system_profile, input_data)
    assert result["host_type"] == "edge"
