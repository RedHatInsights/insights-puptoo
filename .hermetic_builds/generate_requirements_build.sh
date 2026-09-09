#!/bin/bash
# Fail fast: without this, a crash in `pybuild-deps compile` is masked by the
# later pip-compile succeeding, so the script exits 0 and leaves a stale
# requirements-build.txt that the Makefile's existence check treats as success.
set -euo pipefail

# Cap pip-tools to <7.6.1: 7.6.1 removed the `generate_hashes` arg from
# OutputWriter, which pybuild-deps 0.5.0 (latest) still passes -> TypeError.
pip3 install "pip-tools<7.6.1" pybuild-deps==0.5.0
# Pin pip to exactly 26.1.2: it is the CVE-2026-8643 floor AND the last pip
# compatible with pip-tools 7.6.0. pip 26.2 removed `stdlib_pkgs` and made
# `allow_editables` a required arg of make_requirement_preparer, breaking
# pip-tools 7.6.0 (which pybuild-deps 0.5.0 pins us below 7.6.1 for). This is
# only the pip that RUNS the generator; the shipped image installs its own
# pip>=26.1.2 in the Dockerfile, independent of this pin.
pip3 install "pip==26.1.2"
cd /var/tmp

pybuild-deps compile --generate-hashes requirements.txt -o requirements-build.txt

# Strip setuptools>=82 build-dep stanzas. pybuild-deps resolves unbounded
# `setuptools>=45` build requirements to the latest release, but setuptools 82+
# removed pkg_resources, which breaks building older packages (e.g. rpm's
# setuptools_scm_git_archive) in the hermetic env. Runtime is pinned <82; keep
# the prefetched build setuptools consistent so isolation can't pick 82+.
awk '
BEGIN { skip=0 }
{
  if (skip) {
    if ($0 ~ /^[[:space:]]/) { next }   # indented continuation (hashes / # via)
    skip=0                               # non-indented line ends the stanza
  }
  if ($0 ~ /^setuptools==/) {
    v=$0; sub(/^setuptools==/,"",v); sub(/[^0-9].*/,"",v);
    if (v+0 >= 82) { skip=1; next }
  }
  print
}
' requirements-build.txt > requirements-build.txt.tmp
mv requirements-build.txt.tmp requirements-build.txt

pip-compile requirements-build.in --allow-unsafe --generate-hashes -o requirements-extras.txt
