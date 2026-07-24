SYSTEMCTL_STATUS_CASES = [
    # Case 1: Normal systemctl output with full fields
    (
        """
        State: degraded
        Jobs: 0 queued
        Failed: 2 units
           | |-1234 chronyd.service loaded failed failed Chrony NTP daemon
           | |-5678 sshd.service loaded active running OpenSSH Daemon
        """,
        {
            "failed": 2,
            "jobs_queued": 0,
            "state": "degraded",
        },
    ),
    # # Case 2: Only Failed field present
    # (
    #     """
    #     Failed: 1 units
    #        | |-2345 chronyd.service loaded failed failed Chrony NTP daemon
    #     """,
    #     {
    #         "failed": 1,
    #     },
    # ),
    # Case 3: Invalid Failed value should skip systemd entirely
    (
        """
        State: degraded
        Jobs: 0 queued
        Failed: units
           | |-3456 chronyd.service loaded failed failed Chrony NTP daemon
        """,
        None,  # systemd should be dropped
    ),
    # Case 4: Whitespace / leading zero edge case
    (
        """
        State:   degraded
        Jobs:    00    queued
        Failed:    01    units
           | |-4567 chronyd.service loaded failed failed Chrony NTP daemon
        """,
        {
            "failed": 1,
            "jobs_queued": 0,
            "state": "degraded",
        },
    ),
    # # Case 5: No Failed field (systemd exists, empty failed_services)
    # (
    #     """
    #     State: running
    #     Jobs: 0 queued
    #     """,
    #     {
    #         "jobs_queued": 0,
    #         "state": "running"
    #     },
    # ),
]
