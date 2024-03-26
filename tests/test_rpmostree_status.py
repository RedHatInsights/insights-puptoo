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
    "deployments": [
        {
            "unlocked": "none",
            "base-commit-meta": {
                "coreos-assembler.config-gitrev": "80966f951c766846da070b4c168b9170c61513e2",
                "coreos-assembler.config-dirty": "false",
                "rpmostree.inputhash": "06539cc4a4265eec2045a349fe80de451a61628c1b117e171d80663d3e3f42eb",
                "coreos-assembler.basearch": "x86_64",
                "version": "33.21",
                "rpmostree.initramfs-args": [
                    "--add=ignition",
                    "--no-hostonly",
                    "--omit=nfs",
                    "--omit=lvm",
                    "--omit=iscsi"
                ],
                "rpmostree.rpmmd-repos": [
                    {
                        "id": "fedora-coreos-pool",
                        "timestamp": 1053029086517002240
                    },
                    {
                        "id": "fedora",
                        "timestamp": -2945197617627267072
                    },
                    {
                        "id": "fedora-updates",
                        "timestamp": -389530169125109760
                    }
                ]
            },
            "requested-local-packages": [],
            "base-removals": [],
            "gpg-enabled": false,
            "origin": "fedora/33/x86_64/silverblue",
            "osname": "fedora-silverblue",
            "pinned": false,
            "requested-base-local-replacements": [
                "rpm-ostree-2021.1-2.fc33.x86_64",
                "rpm-ostree-libs-2021.1-2.fc33.x86_64"
            ],
            "checksum": "63335a77f9853618ba1a5f139c5805e82176a2a040ef5e34d7402e12263af5bb",
            "regenerate-initramfs": false,
            "id": "fedora-silverblue-63335a77f9853618ba1a5f139c5805e82176a2a040ef5e34d7402e12263af5bb.0",
            "version": "33.21",
            "base-version": "33.21",
            "requested-base-removals": [],
            "base-checksum": "229387d3c0bb8ad698228ca5702eca72aed8b298a7c800be1dc72bab160a9f7f",
            "requested-packages": [
                "xsel",
                "gdb",
                "ykclient",
                "krb5-workstation",
                "ykpers",
                "git-evtag",
                "fish",
                "qemu-system-aarch64",
                "strace",
                "qemu-kvm",
                "virt-manager",
                "opensc",
                "tmux",
                "pcsc-lite-ccid",
                "tilix",
                "libvirt"
            ],
            "base-timestamp": 1612554510,
            "serial": 0,
            "layered-commit-meta": {
                "rpmostree.clientlayer": true,
                "rpmostree.removed-base-packages": [],
                "version": "33.21",
                "rpmostree.packages": [
                    "fish",
                    "gdb",
                    "git-evtag",
                    "krb5-workstation",
                    "libvirt",
                    "opensc",
                    "pcsc-lite-ccid",
                    "qemu-kvm",
                    "qemu-system-aarch64",
                    "strace",
                    "tilix",
                    "tmux",
                    "virt-manager",
                    "xsel",
                    "ykclient",
                    "ykpers"
                ],
                "rpmostree.clientlayer_version": 4,
                "rpmostree.replaced-base-packages": [
                    [
                        [
                            "rpm-ostree-2021.1-2.fc33.x86_64",
                            "rpm-ostree",
                            0,
                            "2021.1",
                            "2.fc33",
                            "x86_64"
                        ],
                        [
                            "rpm-ostree-2021.1-3.fc33.x86_64",
                            "rpm-ostree",
                            0,
                            "2021.1",
                            "3.fc33",
                            "x86_64"
                        ]
                    ],
                    [
                        [
                            "rpm-ostree-libs-2021.1-2.fc33.x86_64",
                            "rpm-ostree-libs",
                            0,
                            "2021.1",
                            "2.fc33",
                            "x86_64"
                        ],
                        [
                            "rpm-ostree-libs-2021.1-3.fc33.x86_64",
                            "rpm-ostree-libs",
                            0,
                            "2021.1",
                            "3.fc33",
                            "x86_64"
                        ]
                    ]
                ],
                "rpmostree.state-sha512": "8b037fba282e3773ef17d4c396ee958765c01e85c7a6a29ec9df1bb2213022cf599da15ec4df982c4f0904012b165c4370a9f14b12c48d0684a66928c4f34b34",
                "rpmostree.rpmmd-repos": [
                    {
                        "id": "fedora-cisco-openh264",
                        "timestamp": 1598382634
                    },
                    {
                        "id": "updates",
                        "timestamp": 1612486906
                    },
                    {
                        "id": "fedora",
                        "timestamp": 1603150039
                    }
                ]
            },
            "base-local-replacements": [
                [
                    [
                        "rpm-ostree-2021.1-2.fc33.x86_64",
                        "rpm-ostree",
                        0,
                        "2021.1",
                        "2.fc33",
                        "x86_64"
                    ],
                    [
                        "rpm-ostree-2021.1-3.fc33.x86_64",
                        "rpm-ostree",
                        0,
                        "2021.1",
                        "3.fc33",
                        "x86_64"
                    ]
                ],
                [
                    [
                        "rpm-ostree-libs-2021.1-2.fc33.x86_64",
                        "rpm-ostree-libs",
                        0,
                        "2021.1",
                        "2.fc33",
                        "x86_64"
                    ],
                    [
                        "rpm-ostree-libs-2021.1-3.fc33.x86_64",
                        "rpm-ostree-libs",
                        0,
                        "2021.1",
                        "3.fc33",
                        "x86_64"
                    ]
                ]
            ],
            "timestamp": 1612555369,
            "packages": [
                "fish",
                "gdb",
                "git-evtag",
                "krb5-workstation",
                "libvirt",
                "opensc",
                "pcsc-lite-ccid",
                "qemu-kvm",
                "qemu-system-aarch64",
                "strace",
                "tilix",
                "tmux",
                "virt-manager",
                "xsel",
                "ykclient",
                "ykpers"
            ],
            "booted": true,
            "initramfs-etc": []
        },
        {
            "unlocked": "none",
            "pending-base-version": "33.21",
            "base-commit-meta": {
                "coreos-assembler.config-gitrev": "bbd5282b507c5b29e3a5f12e9da21f3aaa0f0e00",
                "coreos-assembler.config-dirty": "false",
                "rpmostree.inputhash": "f33469d0f6c5d5ce5e30345fa5b002a8e4ebf5ea397caad000bdc32cd74897a6",
                "coreos-assembler.basearch": "x86_64",
                "version": "33.17",
                "rpmostree.initramfs-args": [
                    "--add=ignition",
                    "--no-hostonly",
                    "--omit=nfs",
                    "--omit=lvm",
                    "--omit=iscsi"
                ],
                "rpmostree.rpmmd-repos": [
                    {
                        "id": "fedora-coreos-pool",
                        "timestamp": 7926905303512121344
                    },
                    {
                        "id": "fedora",
                        "timestamp": -2945197617627267072
                    },
                    {
                        "id": "fedora-updates",
                        "timestamp": -6611277243593261056
                    }
                ]
            },
            "requested-local-packages": [],
            "base-removals": [],
            "gpg-enabled": false,
            "osname": "fedora-silverblue",
            "origin": "fedora/33/x86_64/silverblue",
            "packages": [
                "fish",
                "gdb",
                "git-evtag",
                "krb5-workstation",
                "libvirt",
                "opensc",
                "pcsc-lite-ccid",
                "qemu-kvm",
                "qemu-system-aarch64",
                "strace",
                "tilix",
                "tmux",
                "virt-manager",
                "xsel",
                "ykclient",
                "ykpers"
            ],
            "pinned": false,
            "requested-base-local-replacements": [
                "rpm-ostree-2021.1-2.fc33.x86_64",
                "rpm-ostree-libs-2021.1-2.fc33.x86_64"
            ],
            "checksum": "775d54e89bc74731ec27db04f12510c0269c8cbab3ad5e39e0a4d693231ef072",
            "regenerate-initramfs": false,
            "id": "fedora-silverblue-775d54e89bc74731ec27db04f12510c0269c8cbab3ad5e39e0a4d693231ef072.0",
            "version": "33.17",
            "base-version": "33.17",
            "base-checksum": "deea0555cb7d3eb042df9a85d4efcbb9f70d778a9a9557715c0e398978233cd7",
            "requested-base-removals": [],
            "requested-packages": [
                "xsel",
                "gdb",
                "ykclient",
                "krb5-workstation",
                "ykpers",
                "git-evtag",
                "fish",
                "qemu-system-aarch64",
                "strace",
                "qemu-kvm",
                "virt-manager",
                "opensc",
                "tmux",
                "pcsc-lite-ccid",
                "tilix",
                "libvirt"
            ],
            "base-timestamp": 1611079148,
            "serial": 0,
            "layered-commit-meta": {
                "rpmostree.clientlayer": true,
                "rpmostree.removed-base-packages": [],
                "version": "33.17",
                "rpmostree.packages": [
                    "fish",
                    "gdb",
                    "git-evtag",
                    "krb5-workstation",
                    "libvirt",
                    "opensc",
                    "pcsc-lite-ccid",
                    "qemu-kvm",
                    "qemu-system-aarch64",
                    "strace",
                    "tilix",
                    "tmux",
                    "virt-manager",
                    "xsel",
                    "ykclient",
                    "ykpers"
                ],
                "rpmostree.clientlayer_version": 4,
                "rpmostree.replaced-base-packages": [
                    [
                        [
                            "rpm-ostree-2021.1-2.fc33.x86_64",
                            "rpm-ostree",
                            0,
                            "2021.1",
                            "2.fc33",
                            "x86_64"
                        ],
                        [
                            "rpm-ostree-2020.10-1.fc33.x86_64",
                            "rpm-ostree",
                            0,
                            "2020.10",
                            "1.fc33",
                            "x86_64"
                        ]
                    ],
                    [
                        [
                            "rpm-ostree-libs-2021.1-2.fc33.x86_64",
                            "rpm-ostree-libs",
                            0,
                            "2021.1",
                            "2.fc33",
                            "x86_64"
                        ],
                        [
                            "rpm-ostree-libs-2020.10-1.fc33.x86_64",
                            "rpm-ostree-libs",
                            0,
                            "2020.10",
                            "1.fc33",
                            "x86_64"
                        ]
                    ]
                ],
                "rpmostree.state-sha512": "684f72c2b63379ee17a8f3055ccdfb3d54d255ed5bf1965788be21e804a0aff9e08620519dacaa34cc8cbad038474e8b0abbc68ee98988c547ad599f93ddcfa1",
                "rpmostree.rpmmd-repos": [
                    {
                        "id": "fedora-cisco-openh264",
                        "timestamp": 1598382634
                    },
                    {
                        "id": "updates",
                        "timestamp": 1611022500
                    },
                    {
                        "id": "fedora",
                        "timestamp": 1603150039
                    }
                ]
            },
            "base-local-replacements": [
                [
                    [
                        "rpm-ostree-2021.1-2.fc33.x86_64",
                        "rpm-ostree",
                        0,
                        "2021.1",
                        "2.fc33",
                        "x86_64"
                    ],
                    [
                        "rpm-ostree-2020.10-1.fc33.x86_64",
                        "rpm-ostree",
                        0,
                        "2020.10",
                        "1.fc33",
                        "x86_64"
                    ]
                ],
                [
                    [
                        "rpm-ostree-libs-2021.1-2.fc33.x86_64",
                        "rpm-ostree-libs",
                        0,
                        "2021.1",
                        "2.fc33",
                        "x86_64"
                    ],
                    [
                        "rpm-ostree-libs-2020.10-1.fc33.x86_64",
                        "rpm-ostree-libs",
                        0,
                        "2020.10",
                        "1.fc33",
                        "x86_64"
                    ]
                ]
            ],
            "timestamp": 1611081986,
            "pending-base-timestamp": 1612554510,
            "booted": false,
            "pending-base-checksum": "229387d3c0bb8ad698228ca5702eca72aed8b298a7c800be1dc72bab160a9f7f",
            "initramfs-etc": []
        }
    ],
    "transaction": null,
    "cached-update": null
}
""".strip()


# Missing "origin" iside deployments item
DATA_2 = """
{
    "deployments" : [{
      "base-removals" : [],
      "requested-modules" : [],
      "requested-modules-enabled" : [],
      "pinned" : false,
      "osname" : "default",
      "base-remote-replacements" : {      },
      "regenerate-initramfs" : false,
      "checksum" : "a7b1b7f5cc436ccb0a2a70da7c04db9e15be58efe2a4dcb9a1bddf2c703e2a46",
      "container-image-reference-digest" : "sha256:758216cb799c79a25bdcb21046b3283dd267fe4f29392bd125a20981e092006b",
      "requested-base-local-replacements" : [],
      "id" : "default-a7b1b7f5cc436ccb0a2a70da7c04db9e15be58efe2a4dcb9a1bddf2c703e2a46.0",
      "version" : "9.20240207.0",
      "requested-local-fileoverride-packages" : [],
      "requested-base-removals" : [],
      "modules" : [],
      "requested-packages" : [],
      "serial" : 0,
      "timestamp" : 1709068966,
      "staged" : true,
      "booted" : false,
      "container-image-reference" : "ostree-unverified-registry:192.168.122.1:5000/bootc-insights:latest",
      "packages" : [],
      "base-local-replacements" : []
    }],
    "transaction" : null,
    "cached-update" : null
}
""".strip()


def test_rpmostree_status_simple():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_0)
    result = run_test(system_profile, input_data)
    deployments = result["rpm_ostree_deployments"]
    assert len(deployments) == 1
    dep = deployments[0]
    assert dep == {
        "id": "rhel-f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267.0",
        "checksum": "f0c0294860db563e5906db8c9f257d2bfebe40c93e0320b0e380b879f545e267",
        "origin": "edge:rhel/8/x86_64/edge",
        "osname": "rhel",
        "booted": True,
        "pinned": False
    }


def test_rpmostree_status_full():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_1)
    result = run_test(system_profile, input_data)
    deployments = result["rpm_ostree_deployments"]
    assert len(deployments) == 2

    dep = deployments[0]
    assert dep == {
        "id": "fedora-silverblue-63335a77f9853618ba1a5f139c5805e82176a2a040ef5e34d7402e12263af5bb.0",
        "checksum": "63335a77f9853618ba1a5f139c5805e82176a2a040ef5e34d7402e12263af5bb",
        "origin": "fedora/33/x86_64/silverblue",
        "osname": "fedora-silverblue",
        "version": "33.21",
        "booted": True,
        "pinned": False,
    }

    dep = deployments[1]
    assert dep == {
        "id": "fedora-silverblue-775d54e89bc74731ec27db04f12510c0269c8cbab3ad5e39e0a4d693231ef072.0",
        "checksum": "775d54e89bc74731ec27db04f12510c0269c8cbab3ad5e39e0a4d693231ef072",
        "origin": "fedora/33/x86_64/silverblue",
        "osname": "fedora-silverblue",
        "version": "33.17",
        "booted": False,
        "pinned": False,
    }


def test_rpmostree_status_missing_origin():
    input_data = InputData().add(Specs.rpm_ostree_status, DATA_2)
    result = run_test(system_profile, input_data)
    deployments = result["rpm_ostree_deployments"]
    assert len(deployments) == 1
    dep = deployments[0]
    assert dep == {
        "id": "default-a7b1b7f5cc436ccb0a2a70da7c04db9e15be58efe2a4dcb9a1bddf2c703e2a46.0",
        "checksum": "a7b1b7f5cc436ccb0a2a70da7c04db9e15be58efe2a4dcb9a1bddf2c703e2a46",
        "origin": "",
        "osname": "default",
        "booted": False,
        "pinned": False,
        "version": "9.20240207.0",
    }
