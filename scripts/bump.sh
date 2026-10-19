#!/bin/sh
set -e

# The current version is pyproject.toml's, never a tag's: git describe and svu
# read whichever tag is nearest, which need not be this package's release.
version=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
major=$(echo "$version" | cut -d. -f1)
minor=$(echo "$version" | cut -d. -f2)
patch=$(echo "$version" | cut -d. -f3)
case "$1" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
  *) echo "Usage: $0 {major|minor|patch}"; exit 1 ;;
esac
new_version="$major.$minor.$patch"
new_tag="v$new_version"

# Update pyproject.toml
sed -i "s/^version = \".*\"/version = \"${new_version}\"/" pyproject.toml

# Refresh the editable install so importlib metadata (User-Agent, version test)
# reports the new version without a manual `make install`.
if [ -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python .venv/bin/python -e . --no-deps
  else
    .venv/bin/python -m pip install -q -e . --no-deps
  fi
fi

git add pyproject.toml
git commit -m "chore: bump version to $new_tag"
git tag "$new_tag"
echo "Tagged $new_tag (run make release to publish)"
