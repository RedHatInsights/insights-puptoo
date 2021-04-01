import pytest

from insights.parsers.installed_rpms import InstalledRpm, InstalledRpms
from insights.tests import context_wrap

from src.puptoo.process.profile import (
    _get_gpg_pubkey_packages,
    _get_latest_packages,
    _get_stale_packages,
)

RPM_DATA = """
{"name": "util-linux","version": "2.23.2","epoch": "(none)","release": "26.el7_2.2","arch": "x86_64","installtime": "Fri 24 Jun 2016 04:17:58 PM EDT","buildtime": "1458159298","rsaheader": "RSA/SHA256, Sun 20 Mar 2016 10:00:45 PM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "util-linux-2.23.2-26.el7_2.2.src.rpm"}
{"name": "libestr","version": "0.1.9","epoch": "(none)","release": "2.el7","arch": "x86_64","installtime": "Fri 06 May 2016 03:53:26 PM EDT","buildtime": "1390734694","rsaheader": "RSA/SHA256, Tue 01 Apr 2014 04:49:20 PM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "libestr-0.1.9-2.el7.src.rpm"}
{"name": "log4j","version": "1.2.17","epoch": "0","release": "15.el7","arch": "noarch","installtime": "Thu 02 Jun 2016 05:10:29 PM EDT","buildtime": "1388247429","rsaheader": "RSA/SHA256, Wed 02 Apr 2014 11:25:59 AM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "log4j-1.2.17-15.el7.src.rpm"}
{"name": "kbd-misc","version": "1.15.5","epoch": "(none)","release": "11.el7","arch": "noarch","installtime": "Fri 06 May 2016 03:52:06 PM EDT","buildtime": "1412004323","rsaheader": "RSA/SHA256, Tue 16 Dec 2014 10:02:15 AM EST, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "kbd-1.15.5-11.el7.src.rpm"}
{"name": "grub2-tools","version": "2.02","epoch": "1","release": "0.34.el7_2","arch": "x86_64","installtime": "Fri 24 Jun 2016 04:18:01 PM EDT","buildtime": "1450199819","rsaheader": "RSA/SHA256, Wed 23 Dec 2015 04:22:27 AM EST, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "grub2-2.02-0.34.el7_2.src.rpm"}
{"name": "kbd-legacy","version": "1.15.5","epoch": "(none)","release": "11.el7","arch": "noarch","installtime": "Fri 06 May 2016 03:53:32 PM EDT","buildtime": "1412004323","rsaheader": "RSA/SHA256, Tue 16 Dec 2014 10:02:14 AM EST, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "kbd-1.15.5-11.el7.src.rpm"}
{"name": "jboss-servlet-3.0-api","version": "1.0.1","epoch": "(none)","release": "9.el7","arch": "noarch","installtime": "Thu 02 Jun 2016 05:10:30 PM EDT","buildtime": "1388211302","rsaheader": "RSA/SHA256, Tue 01 Apr 2014 02:51:30 PM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "jboss-servlet-3.0-api-1.0.1-9.el7.src.rpm"}
{"name": "bash","version": "4.2.46","epoch": "(none)","release": "19.el7","arch": "x86_64","installtime": "Fri 06 May 2016 03:52:13 PM EDT","buildtime": "1436354006","rsaheader": "RSA/SHA256, Wed 07 Oct 2015 01:14:10 PM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "bash-4.2.46-19.el7.src.rpm"}
{"name": "ca-certificates","version": "2015.2.6","epoch": "(none)","release": "70.1.el7_2","arch": "noarch","installtime": "Fri 24 Jun 2016 04:18:04 PM EDT","buildtime": "1453976868","rsaheader": "RSA/SHA256, Tue 02 Feb 2016 09:45:04 AM EST, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "ca-certificates-2015.2.6-70.1.el7_2.src.rpm"}
{"name": "jline","version": "1.0","epoch": "(none)","release": "8.el7","arch": "noarch","installtime": "Thu 02 Jun 2016 05:10:32 PM EDT","buildtime": "1388212830","rsaheader": "RSA/SHA256, Tue 01 Apr 2014 02:54:16 PM EDT, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "jline-1.0-8.el7.src.rpm"}
{"name": "libteam","version": "1.17","epoch": "(none)","release": "6.el7_2","arch": "x86_64","installtime": "Fri 24 Jun 2016 04:18:17 PM EDT","buildtime": "1454604485","rsaheader": "RSA/SHA256, Wed 17 Feb 2016 02:25:16 AM EST, Key ID 199e2f91fd431d51","dsaheader": "(none)","srpm": "libteam-1.17-6.el7_2.src.rpm"}
{"name": "crash","epoch":"(none)","version":"7.1.0","release":"8.el6","arch":"x86_64","installtime":"Fri Jul 13 06:53:28 2018","buildtime":"1524061059","vendor":"Red Hat, Inc.","buildhost":"x86-032.build.eng.bos.redhat.com","sigpgp":"RSA/8, Wed Apr 18 10:40:59 2018, Key ID 199e2f91fd431d51"}
{"name": "xorg-x11-drv-vmmouse","epoch":"(none)","version":"13.1.0","release":"1.el6","arch":"x86_64","installtime":"Thu Aug  4 12:23:32 2016","buildtime":"1447274489","vendor":"Red Hat, Inc.","buildhost":"x86-028.build.eng.bos.redhat.com","sigpgp":"RSA/8, Mon Apr 4 11:35:36 2016, Key ID 199e2f91fd431d51"}
{"name": "libnl","epoch":"(none)","version":"1.1.4","release":"2.el6","arch":"x86_64","installtime":"Mon Jun 16 13:21:21 2014","buildtime":"1378459378","vendor":"(none)","buildhost":"x86-007.build.bos.redhat.com","sigpgp":"RSA/8, Mon Sep 23 07:25:47 2013, Key ID 199e2f91fd431d51"}
{"name": "libnl","epoch":"(none)","version":"1.1.5","release":"2.el6","arch":"x86_64","installtime":"Mon Jun 16 13:21:21 2014","buildtime":"1378459378","vendor":"(none)","buildhost":"x86-007.build.bos.redhat.com","sigpgp":"RSA/8, Mon Sep 23 07:25:47 2013, Key ID 199e2f91fd431d51"}
{"name":"gpg-pubkey","epoch":"(none)","version":"2fa658e0","release":"45700c69","arch":"(none)","installtime":"Thu Apr 25 08:21:00 2019","buildtime":"1556194860","vendor":"(none)","buildhost":"localhost","sigpgp":"(none)"}
""".strip().splitlines()


@pytest.fixture
def rpms():
    return InstalledRpms(context_wrap(RPM_DATA))


def test_get_gpg_pubkey_packages(rpms):
    pkgs = _get_gpg_pubkey_packages(rpms)
    gpg_pubkey = InstalledRpm.from_json(RPM_DATA[-1])
    assert gpg_pubkey in pkgs
    assert len(pkgs) == 1


def test_get_latest_packages(rpms):
    pkgs = _get_latest_packages(rpms)
    gpg_pubkey = InstalledRpm.from_json(RPM_DATA[-1])
    libnl = InstalledRpm.from_json(RPM_DATA[-3])
    assert gpg_pubkey not in pkgs
    assert libnl not in pkgs
    assert len(pkgs) == len(RPM_DATA) - 2


def test_get_stale_packages(rpms):
    stale = _get_stale_packages(rpms)
    assert InstalledRpm.from_package("libnl-0:1.1.4-2.el6.x86_64") in stale
    assert len(stale) == 1
