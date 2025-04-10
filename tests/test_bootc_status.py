from insights.specs import Specs
from insights.tests import InputData, run_test
from src.puptoo.process.profile import system_profile

BOOTC_STATUS = """
{
   "apiVersion":"org.containers.bootc/v1alpha1",
   "kind":"BootcHost",
   "metadata":{
      "name":"host"
   },
   "spec":{
      "image":{
         "image":"192.168.124.1:5000/bootc-insights:latest",
         "transport":"registry"
      }
   },
   "status":{
      "staged":null,
      "booted":{
         "image":{
            "image":{
               "image":"192.168.124.1:5000/bootc-insights:latest",
               "transport":"registry"
            },
            "version":"stream9.20231213.0",
            "timestamp":null,
            "imageDigest":"sha256:806d77394f96e47cf99b1233561ce970c94521244a2d8f2affa12c3261961223"
         },
         "incompatible":false,
         "pinned":false,
         "ostree":{
            "checksum":"6aa32a312c832e32a2dbfe006f05e5972d9f2b86df54e747128c24e6c1fb129a",
            "deploySerial":0
         }
      },
      "rollback":{
         "image":{
            "image":{
               "image":"quay.io/centos-boot/fedora-boot-cloud:eln",
               "transport":"registry"
            },
            "version":"39.20231109.3",
            "timestamp":null,
            "imageDigest":"sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0"
         },
         "incompatible":false,
         "pinned":false,
         "ostree":{
            "checksum":"56612a5982b7f12530988c970d750f89b0489f1f9bebf9c2a54244757e184dd8",
            "deploySerial":0
         }
      },
      "type":"bootcHost"
   }
}
""".strip()

BOOTC_STATUS_WITH_CACHEDUPDATE_1 = """
{
  "apiVersion": "org.containers.bootc/v1alpha1",
  "kind": "BootcHost",
  "metadata": {
    "name": "host"
  },
  "spec": {
    "image": {
      "image": "192.168.122.1:5000/bootc-insights:latest",
      "transport": "registry"
    }
  },
  "status": {
    "staged": {
      "image": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778"
      },
      "cachedUpdate": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:3c1cea8218e4331641020c59e0877ae20ec058e34a346fa424bbe726daab294e"
      },
      "incompatible": false,
      "pinned": false,
      "ostree": {
        "checksum": "91aeb5bdff14917ff7e6b525d2253b40c0ab632e3aa16de72592603acffe592d",
        "deploySerial": 0
      }
    },
    "booted": {
      "image": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e"
      },
      "cachedUpdate": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778"
      },
      "incompatible": false,
      "pinned": false,
      "ostree": {
        "checksum": "759c97c3b3f7e9198b0f6e6f2b0fcd3c668bb39810742f207f85cfb0b2b398fd",
        "deploySerial": 0
      }
    },
    "rollback": null,
    "type": "bootcHost"
  }
}
""".strip()

BOOTC_STATUS_WITH_CACHEDUPDATE_2 = """
{
  "apiVersion": "org.containers.bootc/v1alpha1",
  "kind": "BootcHost",
  "metadata": {
    "name": "host"
  },
  "spec": {
    "image": {
      "image": "192.168.122.1:5000/bootc-insights:latest",
      "transport": "registry"
    }
  },
  "status": {
    "staged": {
      "image": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778"
      },
      "incompatible": false,
      "pinned": false,
      "ostree": {
        "checksum": "91aeb5bdff14917ff7e6b525d2253b40c0ab632e3aa16de72592603acffe592d",
        "deploySerial": 0
      }
    },
    "booted": {
      "image": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e"
      },
      "cachedUpdate": {
        "image": {
          "image": "192.168.122.1:5000/bootc-insights:latest",
          "transport": "registry"
        },
        "version": "9.20240325.0",
        "timestamp": null,
        "imageDigest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778"
      },
      "incompatible": false,
      "pinned": false,
      "ostree": {
        "checksum": "759c97c3b3f7e9198b0f6e6f2b0fcd3c668bb39810742f207f85cfb0b2b398fd",
        "deploySerial": 0
      }
    },
    "rollback": null,
    "type": "bootcHost"
  }
}
""".strip()

BOOTC_STATUS_BAD_DATA = """
{
   "apiVersion":"org.containers.bootc/v1alpha1",
   "kind":"BootcHost",
   "metadata":{
      "name":"host"
   },
   "spec":{
      "image":{
         "image":"192.168.124.1:5000/bootc-insights:latest",
         "transport":"registry"
      }
   },
   "status":{
      "staged":null,
      "booted":{
         "image":{
            "image":{
               "transport":"registry"
            },
            "version":"stream9.20231213.0",
            "timestamp":null,
            "imageDigest":"sha256:806d77394f96e47cf99b1233561ce970c94521244a2d8f2affa12c3261961223"
         },
         "incompatible":false,
         "pinned":false,
         "ostree":{
            "checksum":"6aa32a312c832e32a2dbfe006f05e5972d9f2b86df54e747128c24e6c1fb129a",
            "deploySerial":0
         }
      },
      "type":"bootcHost"
   }
}
""".strip()

BOOTC_STATUS_SPECIAL_DATA = """
{
   "apiVersion":"org.containers.bootc/v1alpha1",
   "kind":"BootcHost",
   "metadata":{
      "name":"host"
   },
   "spec":{
      "image":{
         "image":"192.168.124.1:5000/bootc-insights:latest",
         "transport":"registry"
      }
   },
   "status":{
      "staged":null,
      "rollback":{
         "image":{
            "image":{
               "image":"quay.io/centos-boot/fedora-boot-cloud:eln",
               "transport":"registry"
            },
            "version":"39.20231109.3",
            "timestamp":null,
            "imageDigest":"sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0"
         },
         "incompatible":false,
         "pinned":false,
         "ostree":{
            "checksum":"56612a5982b7f12530988c970d750f89b0489f1f9bebf9c2a54244757e184dd8",
            "deploySerial":0
         }
      },
      "type":"bootcHost"
   }
}
""".strip()


def test_bootc_status():
    input_data = InputData().add(Specs.bootc_status, BOOTC_STATUS)
    result = run_test(system_profile, input_data)
    assert result["bootc_status"] == {
        "booted": {
            "image": "192.168.124.1:5000/bootc-insights:latest",
            "image_digest": "sha256:806d77394f96e47cf99b1233561ce970c94521244a2d8f2affa12c3261961223",
        },
        "rollback": {
            "image": "quay.io/centos-boot/fedora-boot-cloud:eln",
            "image_digest": "sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0",
        }}

    input_data = InputData().add(Specs.bootc_status, BOOTC_STATUS_WITH_CACHEDUPDATE_1)
    result = run_test(system_profile, input_data)
    assert result["bootc_status"] == {
        "booted": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e",
            "cached_image": "192.168.122.1:5000/bootc-insights:latest",
            "cached_image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
        },
        "staged": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
            "cached_image": "192.168.122.1:5000/bootc-insights:latest",
            "cached_image_digest": "sha256:3c1cea8218e4331641020c59e0877ae20ec058e34a346fa424bbe726daab294e",
        }}

    input_data = InputData().add(Specs.bootc_status, BOOTC_STATUS_WITH_CACHEDUPDATE_2)
    result = run_test(system_profile, input_data)
    assert result["bootc_status"] == {
        "booted": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:5398062d64b501e18b986b43a4f4108cb879fd29d436d793c0bf6947a83ed09e",
            "cached_image": "192.168.122.1:5000/bootc-insights:latest",
            "cached_image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
        },
        "staged": {
            "image": "192.168.122.1:5000/bootc-insights:latest",
            "image_digest": "sha256:654275229d342b2836dcb8e5b851bbb1461b664a9fb9b8c934011e1abf15d778",
        }}

    input_data = InputData().add(Specs.bootc_status, BOOTC_STATUS_BAD_DATA)
    result = run_test(system_profile, input_data)
    assert result["bootc_status"] == {
        "booted": {
            "image": "",
            "image_digest": "sha256:806d77394f96e47cf99b1233561ce970c94521244a2d8f2affa12c3261961223",
        }}

    input_data = InputData().add(Specs.bootc_status, BOOTC_STATUS_SPECIAL_DATA)
    result = run_test(system_profile, input_data)
    assert result["bootc_status"] == {
        "rollback": {
            "image": "quay.io/centos-boot/fedora-boot-cloud:eln",
            "image_digest": "sha256:92e476435ced1c148350c660b09c744717defbd300a15d33deda5b50ad6b21a0",
        }}
