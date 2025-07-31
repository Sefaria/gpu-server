#!/bin/bash

cat << EOF > chart/.releaserc
extends:
  - semantic-release-monorepo
tagFormat: helm-\${version}
plugins:
  - - "@semantic-release/commit-analyzer"
    - preset: "conventionalcommits"
      releaseRules:
        - {"type": "feat", "release": "minor"}
        - {"type": "fix", "release": "patch"}
        - {"type": "chore", "release": "patch"}
        - {"type": "docs", "release": "patch"}
        - {"type": "style", "release": "patch"}
        - {"type": "refactor", "release": "patch"}
        - {"type": "perf", "release": "patch"}
        - {"type": "test", "release": "patch"}
        - {"type": "static", "release": "patch"}
      parserOpts:
        noteKeywords:
          - MAJOR RELEASE
  - - "@semantic-release/release-notes-generator"
    - preset: "conventionalcommits"
  - - "@semantic-release/github"
    - "successComment": false
  - - "@semantic-release/exec"
    - "prepareCmd": "./chart-prerelease.sh \${nextRelease.gitTag}"
  - - "@semantic-release/git"
    - assets:
        - Chart.yaml
EOF
export branch=$(git branch --show-current)
export channel=$(echo $branch | awk '{print tolower($0)}' | sed 's|.*/\([^/]*\)/.*|\1|; t; s|.*|\0|' | sed 's/[^a-z0-9\.\-]//g')
if [[ $branch != "main" ]]; then
cat << EOF >> chart/.releaserc
branches: [
    {"name": "main"},
    {"name": "${branch}", "prerelease": "$channel"}
  ]
EOF
else
cat << EOF >> chart/.releaserc
branches: [
    {"name": "main"}
  ]
EOF
fi
