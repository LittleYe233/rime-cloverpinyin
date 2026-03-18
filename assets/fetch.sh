#!/usr/bin/env bash

set -e

DOWNLOAD_TARGETS=(
    "https://pinyin.sogou.com/d/dict/download_cell.php?id=4&name=%E7%BD%91%E7%BB%9C%E6%B5%81%E8%A1%8C%E6%96%B0%E8%AF%8D%E3%80%90%E5%AE%98%E6%96%B9%E6%8E%A8%E8%8D%90%E3%80%91&f=detail|sogou_new_words.scel"
    "https://dumps.wikimedia.org/zhwikisource/20260301/zhwikisource-20260301-all-titles-in-ns0.gz|zhwikisource.gz"
    "https://dumps.wikimedia.org/zhwiktionary/20260301/zhwiktionary-20260301-all-titles-in-ns0.gz|zhwiktionary.gz"
    "https://dumps.wikimedia.org/zhwiki/20260301/zhwiki-20260301-all-titles-in-ns0.gz|zhwiki.gz"
    "https://github.com/outloudvi/mw2fcitx/releases/download/20260315/moegirl.dict.yaml|moegirl.dict.yaml"
)
TIMESTAMP=$(date +%s)
JSON_ENTRIES=()

cd "$(dirname "$0")"

for entry in "${DOWNLOAD_TARGETS[@]}"; do
    URL="${entry%|*}"
    FILENAME="${entry#*|}"
    echo "Downloading: $FILENAME..."
    if curl -sSL -o "$FILENAME" "$URL"; then
        HASH=$(sha256sum "$FILENAME" | awk '{print $1}')
        JSON_ENTRIES+=("{\"filename\":\"$FILENAME\",\"url\":\"$URL\",\"hash\":\"$HASH\",\"timestamp\":$TIMESTAMP}")
    else
        echo "Error: Failed to download $FILENAME from $URL" >&2
        echo "Workflow aborted. metadata.json will not be written." >&2
        exit 1
    fi
done

echo "All files downloaded successfully! Writing metadata.json..."
{
    echo "["
    NUM_ENTRIES=${#JSON_ENTRIES[@]}
    for (( i=0; i<NUM_ENTRIES; i++ )); do
        if [ $i -lt $((NUM_ENTRIES - 1)) ]; then
            echo "  ${JSON_ENTRIES[$i]},"
        else
            echo "  ${JSON_ENTRIES[$i]}"
        fi
    done
    echo "]"
} > "metadata.json"
