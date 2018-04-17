#!/usr/bin/env bash
set -x
set -e
ROOT_DIR="$(dirname "$(readlink -f "$0")")"
echo ROOT_DIR=$ROOT_DIR
# check mounted directory
TARGET_DIR=/Volumes/books/linux_journal

if [ ! -d ${TARGET_DIR} ]; then
	echo $TARGET_DIR not available
	exit 1
fi
pushd $TARGET_DIR > /dev/null
${ROOT_DIR}/lj_downloader.py --download-all --account-number=LJ088986 --format epub
popd > /dev/null
