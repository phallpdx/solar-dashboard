#!/bin/bash
# bash tools/engrave/try.sh <slug>
cd "$(dirname "$0")/../.." && python3 tools/engrave/gen.py "$1"; r=$?; node tools/engrave/try.js "$1"; ls tools/engrave/out/$1/*.png; exit $r
