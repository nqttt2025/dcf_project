#!/bin/bash
# Script to run DCF analysis for all stocks in the config folder

echo "======================================"
echo "DCF ANALYSIS - ALL STOCKS"
echo "======================================"
echo ""

# Get all .cfg files in config folder
cd /home/eenitug/dcf_project

echo "Found config files:"
for cfg_file in config/*.cfg; do
    if [ -f "$cfg_file" ]; then
        echo "  - $(basename $cfg_file)"
    fi
done
echo ""

# Run DCF for each config file
echo "Running DCF analysis..."
echo "======================================"
echo ""

for cfg_file in config/*.cfg; do
    if [ -f "$cfg_file" ]; then
        config_name=$(basename "$cfg_file")
        echo "Processing: $config_name"
        python3 -c "import sys; sys.path.insert(0, '.'); from src.core.dcf_calculator import calculate_dcf_from_config; import asyncio; asyncio.run(calculate_dcf_from_config('$cfg_file'))"
        echo ""
    fi
done

echo "======================================"
echo "Analysis completed!"
echo "Results saved in: results/"
echo "======================================"

# List generated result files
echo ""
echo "Generated files:"
for result_file in data/results/*.text; do
    if [ -f "$result_file" ]; then
        echo "  ✓ $(basename $result_file)"
    fi
done
