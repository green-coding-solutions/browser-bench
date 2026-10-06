#!/usr/bin/env bash
# Submit browser-bench scenarios to the GMT cluster.
#
# usage: ./submit-cluster.sh [-y] [-m machine] [-b browsers] [-n repetitions] [-e email] [folder ...]
#
#   folder   speedometer2, speedometer3 and/or web-usage. Default: all three.
#   -b       Browsers, comma separated, e.g. chrome,firefox. Default: all eleven.
#   -m       Machine id. Default: 12, the GUI machine whose :0 is a Wayland desktop.
#   -n       Submit every scenario this many times. Default: 1.
#   -e       Mail address for the completion notice of each run. Default: none.
#   -y       Really submit. Without it the script only prints what it would submit.
#
# Example, one run first to see that the machine's display works, then everything:
#
#   ./submit-cluster.sh -y -b chrome speedometer3
#   ./submit-cluster.sh -y -n 3
#
# The cluster clones the branch from GitHub, not this folder. So the script
# refuses to submit while there are uncommitted changes or the current commit
# is not on the remote branch. Repetitions are submitted round by round, so the
# runs of one scenario are spread over the whole batch.
#
# It uses gmt-helpers' submit_software.py with the Python of the Green Metrics
# Tool, which has requests. Set GMT_PYTHON and SUBMIT_SOFTWARE to use others.
# The token comes from GMT_AUTH_TOKEN or ~/.gmt/token, as in submit_software.py.
set -euo pipefail

GMT_PYTHON=${GMT_PYTHON:-$HOME/code/green-metrics-tool/venv/bin/python}
SUBMIT_SOFTWARE=${SUBMIT_SOFTWARE:-$HOME/code/gmt-helpers/api/submit_software.py}
ALL_BROWSERS=brave,chrome,chromium,ecosia,edge,falkon,firefox,nyxt,opera,vivaldi,waterfox
declare -A NAMES=([brave]=Brave [chrome]="Google Chrome" [chromium]=Chromium [ecosia]=Ecosia [edge]="Microsoft Edge"
                  [falkon]=Falkon [firefox]=Firefox [nyxt]=Nyxt [opera]=Opera [vivaldi]=Vivaldi [waterfox]=Waterfox)
declare -A BENCHMARKS=([speedometer2]="Speedometer 2.1" [speedometer3]="Speedometer 3.1" [web-usage]="Web usage")

machine=12 browsers=$ALL_BROWSERS repetitions=1 email="" really=no
while getopts "m:b:n:e:y" opt; do
    case $opt in
        m) machine=$OPTARG ;;
        b) browsers=$OPTARG ;;
        n) repetitions=$OPTARG ;;
        e) email=$OPTARG ;;
        y) really=yes ;;
        *) sed -n '2,13p' "$0"; exit 1 ;;
    esac
done
shift $((OPTIND - 1))
folders=("$@")
[ ${#folders[@]} -eq 0 ] && folders=(speedometer2 speedometer3 web-usage)

cd "$(dirname "$0")"

# What the cluster will clone: the remote as https without .git, and the branch.
remote=$(git remote get-url origin)
repo_url=$(echo "$remote" | sed -E 's#^git@([^:]+):#https://\1/#; s#\.git$##')
branch=$(git rev-parse --abbrev-ref HEAD)

if [ -n "$(git status --porcelain)" ]; then
    echo "There are uncommitted changes. The cluster would not see them, so commit and push first." >&2
    [ $really = yes ] && exit 1
fi
git fetch -q origin "$branch" 2>/dev/null || true
if [ "$(git rev-parse HEAD)" != "$(git rev-parse "origin/$branch" 2>/dev/null || echo none)" ]; then
    echo "The current commit is not on origin/$branch. The cluster would run another version, so push first." >&2
    [ $really = yes ] && exit 1
fi

jobs=()
for round in $(seq 1 "$repetitions"); do
    for folder in "${folders[@]}"; do
        [ -n "${BENCHMARKS[$folder]:-}" ] || { echo "Unknown folder $folder" >&2; exit 1; }
        for b in ${browsers//,/ }; do
            [ -n "${NAMES[$b]:-}" ] || { echo "Unknown browser $b" >&2; exit 1; }
            [ -f "$folder/usage_scenario_$b.yml" ] || { echo "Missing $folder/usage_scenario_$b.yml" >&2; exit 1; }
            name="browser-bench ${BENCHMARKS[$folder]} - ${NAMES[$b]}"
            [ "$repetitions" -gt 1 ] && name="$name (run $round of $repetitions)"
            jobs+=("$folder/usage_scenario_$b.yml|$name")
        done
    done
done

echo "Repository $repo_url, branch $branch, commit $(git rev-parse --short HEAD), machine $machine, ${#jobs[@]} runs"
for job in "${jobs[@]}"; do
    file=${job%%|*} name=${job#*|}
    args=(submit --name "$name" --repo-url "$repo_url" --branch "$branch" --filename "$file"
          --machine-id "$machine" --schedule-mode one-off)
    [ -n "$email" ] && args+=(--email "$email")
    if [ $really = yes ]; then
        echo "Submitting $name"
        "$GMT_PYTHON" "$SUBMIT_SOFTWARE" "${args[@]}"
    else
        echo "Would submit: $name  ($file)"
    fi
done
[ $really = yes ] || echo "Nothing was submitted. Add -y to submit."
