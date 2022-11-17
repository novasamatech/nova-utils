#!/bin/bash
SCRIPT_PATH=$(dirname "$0")
MAIN_DIRECTORY=${SCRIPT_PATH%/*}

folders=($(ls ${MAIN_DIRECTORY}/../$1))

echo ${folders[-1]}
