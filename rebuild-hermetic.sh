#!/bin/bash

#
# A script to run a series of build commands in sequence.
# It accepts an optional BASE_IMAGE argument, pulls it, inspects it,
# and then passes it to each command.
# If no argument is provided, a default value is used.
# It checks the return code of each command and exits immediately
# if a command fails, printing an error message.
#

# --- Configuration ---
# Set 'e' option to exit immediately if a command exits with a non-zero status.
# This provides a safety net, although the script also has explicit checks.
set -e

# --- Commands Definitions ---
# Define the commands to be run in arrays for easy looping.
# Note: Each command is a single string within the array.
RPM_COMMANDS=(
  "make generate-repo-file"
  "make generate-rpms-in-yaml"
  "make generate-rpm-lockfile"
)

PYTHON_COMMANDS=(
  "make generate-py-pkg-lock"
  "make generate-requirements-build-in"
  "make generate-requirements-build-txt"
)

# --- Argument Handling ---
# Define the default value for BASE_IMAGE.
DEFAULT_BASE_IMAGE="registry.access.redhat.com/ubi9/ubi-minimal:latest"
DEFAULT_IMAGE_ARCH="x86_64"

# Use the first argument ($1) as BASE_IMAGE if it's provided.
# Otherwise, use the DEFAULT_BASE_IMAGE.
# The :- syntax is a standard shell parameter expansion.
BASE_IMAGE="${1:-$DEFAULT_BASE_IMAGE}"
IMAGE_ARCH="${2:-$DEFAULT_IMAGE_ARCH}"

echo "ℹ️ Using BASE_IMAGE(ARCH): $BASE_IMAGE ($IMAGE_ARCH)"
echo

# --- Helper Function ---
# This function executes any command passed to it, checks the exit code,
# and prints a status message.
#
# Arguments:
#   $@ - All arguments passed to the function are treated as the command to execute.
#
run_command() {
  # Print the command we are about to run for clarity.
  echo "🚀 Executing: $@"

  # Execute the command. The "$@" syntax ensures all arguments are passed correctly,
  # even if they contain spaces.
  "$@"

  # Check the exit code of the last command.
  # $? is a special variable in bash that holds the exit status of the most recently executed command.
  # A value of 0 means success; any other value indicates an error.
  local exit_code=$?

  if [ $exit_code -ne 0 ]; then
    # If the exit code is not 0, print a detailed error message.
    # >&2 redirects the output to Standard Error.
    echo "❌ ERROR: Command '$@' failed with exit code $exit_code." >&2
    # Exit the script with the same error code as the failed command.
    exit $exit_code
  else
    # If the command was successful, print a success message.
    echo "✅ SUCCESS: Command '$@' finished."
  fi
  # Print a blank line for better readability between commands.
  echo
}

# --- Image Preparation ---
echo "--- Preparing Base Image ---"
echo

# 1. Pull the base image
run_command podman pull "$BASE_IMAGE" --arch "$IMAGE_ARCH"

# 2. Inspect the image to find all its tags
echo "🔍 Inspecting image for all associated tags..."
echo "🚀 Executing: podman inspect --format '{{.RepoTags}}' $BASE_IMAGE"
# The output of inspect is a space-separated list inside brackets, e.g., "[tag1 tag2]"
tags_output=$(podman inspect --format '{{.RepoTags}}' "$BASE_IMAGE")
# Remove the brackets using parameter expansion
# tags_list=${tags_output//[\[\]]/}

# Remove the leading '[' and trailing ']' from the tags_output string
#    - ${1#\[} removes the first character if it's a '['.
#    - ${...%\]} removes the last character if it's a ']'.
tags_list=${tags_output#\[}
tags_list=${tags_list%\]}

if [ -z "$tags_list" ]; then
    echo "⚠️ No tags found for $BASE_IMAGE"
else
    echo "Found the following tags:"
    # Loop through the tags and print them as a list
    for tag in $tags_list; do
      echo "  - $tag"
    done
fi
echo


# --- Main Script Logic ---
echo "--- Starting Build Process ---"
echo

# Loop through and run the first set of commands.
for cmd in "${RPM_COMMANDS[@]}"; do
  run_command $cmd BASE_IMAGE=$BASE_IMAGE
done

# rpm-lockfile-prototype skips packages already in the base image, but
# Cachi2's hermetic solver cannot see installed packages and needs them
# prefetched. Re-inject any such packages after lockfile generation.
# This function queries the base image for the installed version and
# fetches the RPM metadata from the CDN dynamically.
inject_base_image_rpm_if_missing() {
  local pkg_name="$1"
  local lockfile="rpms.lock.yaml"

  if grep -q "name: ${pkg_name}$" "$lockfile"; then
    echo "  ℹ️  ${pkg_name} already in ${lockfile}, skipping injection"
    return
  fi

  echo "  ⚠️  ${pkg_name} missing from ${lockfile}, querying base image..."

  # Query the base image for the installed package details
  local rpm_info
  rpm_info=$(podman run --rm --arch "$IMAGE_ARCH" "$BASE_IMAGE" \
    rpm -q --qf '%{NAME} %{EPOCH} %{VERSION} %{RELEASE} %{ARCH} %{SOURCERPM}\n' "$pkg_name" 2>/dev/null)

  if [ -z "$rpm_info" ]; then
    echo "  ❌ ${pkg_name} not found in base image, skipping"
    return
  fi

  local name epoch version release arch sourcerpm
  read -r name epoch version release arch sourcerpm <<< "$rpm_info"

  # Build EVR (epoch:version-release) — omit epoch if "(none)"
  local evr
  if [ "$epoch" = "(none)" ]; then
    evr="${version}-${release}"
  else
    evr="${epoch}:${version}-${release}"
  fi

  # Derive CDN URL from package metadata
  local first_letter="${name:0:1}"
  local rpm_filename="${name}-${version}-${release}.${arch}.rpm"
  local cdn_base="https://cdn-ubi.redhat.com/content/public/ubi/dist/ubi9/9/${arch}/baseos/os/Packages"
  local url="${cdn_base}/${first_letter}/${rpm_filename}"
  local repoid="ubi-9-for-${arch}-baseos-rpms"

  # Fetch RPM to compute size and checksum
  local tmp_rpm
  tmp_rpm=$(mktemp)
  echo "  📥 Fetching ${rpm_filename} for checksum..."
  if ! curl -sSfL -o "$tmp_rpm" "$url"; then
    echo "  ❌ Failed to download ${url}, skipping"
    rm -f "$tmp_rpm"
    return
  fi

  local size checksum
  size=$(stat -f%z "$tmp_rpm" 2>/dev/null || stat -c%s "$tmp_rpm" 2>/dev/null)
  checksum="sha256:$(sha256sum "$tmp_rpm" | awk '{print $1}')"
  rm -f "$tmp_rpm"

  echo "  📦 Injecting ${pkg_name} (${evr}) into ${lockfile}"

  local entry
  entry=$(cat <<ENTRY
  - url: ${url}
    repoid: ${repoid}
    size: ${size}
    checksum: ${checksum}
    name: ${name}
    evr: ${evr}
    sourcerpm: ${sourcerpm}
ENTRY
)

  # Insert after the 'openssl' binary package entry (before next package)
  local anchor="sourcerpm: openssl-.*\.src\.rpm"
  local tmp="${lockfile}.tmp"
  awk -v entry="$entry" -v anchor="$anchor" '
    { print }
    !injected && $0 ~ anchor && $0 !~ /source\/SRPMS/ {
      print entry
      injected = 1
    }
  ' "$lockfile" > "$tmp" && mv "$tmp" "$lockfile"
}

inject_base_image_rpm_if_missing "openssl-libs"

echo "--- Processing Python Requirements ---"
echo

# Loop through and run the Python-related commands.
for cmd in "${PYTHON_COMMANDS[@]}"; do
  run_command $cmd BASE_IMAGE=$BASE_IMAGE
done


# If the script reaches this point, all commands have succeeded.
echo "🎉 All commands completed successfully!"

# Exit with a success code.
exit 0
