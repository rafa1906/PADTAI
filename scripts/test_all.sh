#!/usr/bin/env bash

# Store call site and cd to PADTAI directory
prev_dir=$PWD
cd "$(dirname "$0")/.."

# Default values for the options
max_timeout=1200
grounded="lt:LTOperator"

# Parse the arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --max-timeout)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                max_timeout="$2"
                shift
            else
                echo "Error: --max-timeout requires a numeric argument."
                exit 1
            fi
            ;;
        --grounded)
            if [[ -n "$2" ]]; then
                grounded="$2"
                shift
            else
                echo "Error: --grounded requires a string argument."
                exit 1
            fi
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
    shift
done

out_dir="scripts/results"
mkdir -p $out_dir

# Loop through datasets
find datasets -type d -links 2 -print0 | while read -d $'\0' dir
do
    echo "[+] Testing $dir..."
    out_path="$(echo "$dir" | sed 's/[[:space:]]//g; s#^datasets/##; s#/#-#g').out"

    # If testing Credit Card dataset, use tuned parameters to avoid memory leak
    if [[ "$dir" == *"Credit Card"* ]]; then
        python3 scripts/test_dataset.py "$dir" --max-timeout $max_timeout --grounded $grounded --intcols 0,1 | tee "$out_dir/$out_path"
    else
        python3 scripts/test_dataset.py "$dir" --max-timeout $max_timeout --grounded $grounded | tee "$out_dir/$out_path"
    fi

    # Remove debug information
    sed -i '/^\[+\]/d' "$out_dir/$out_path"
    sed -i '1d' "$out_dir/$out_path"
done

# Restore call site
cd $prev_dir
