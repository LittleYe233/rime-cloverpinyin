#!/usr/bin/env python3

import argparse
import gzip
import io
import os
import sys
from typing import cast

import requests
import opencc

_MINIMUM_LEN = 2
_MAXIMUM_LEN = 6
_LIST_PAGE_ENDINGS = ['列表', '对照表']

URLS = {
    'zhwikisource': "https://dumps.wikimedia.org/zhwikisource/20260301/zhwikisource-20260301-all-titles-in-ns0.gz",
    'zhwiktionary': "https://dumps.wikimedia.org/zhwiktionary/20260301/zhwiktionary-20260301-all-titles-in-ns0.gz",
    'zhwiki': "https://dumps.wikimedia.org/zhwiki/20260301/zhwiki-20260301-all-titles-in-ns0.gz"
}

def is_all_chinese(text: str) -> bool:
    """Check if all characters in the text are Chinese Hanzi."""
    for char in text:
        if not ('\u4e00' <= char <= '\u9fff'):
            return False
    return True

def fetch_and_extract(url: str) -> list[str]:
    """Fetch a GZip file from a URL and extract its text content."""
    _ = sys.stderr.write(f"Fetching {url}...\n")
    response = requests.get(url)
    response.raise_for_status()
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
        content = f.read().decode('utf-8')
    return content.splitlines()

def read_local_gz_file(filepath: str) -> list[str]:
    """Read a local GZip file."""
    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
        return f.read().splitlines()

def process_file(phrases: list[str], converter: opencc.OpenCC) -> list[str]:
    """Filter phrases according to the specified rules."""
    filtered: list[str] = []
    previous_phrase: str | None = None
    
    for phrase in phrases:
        phrase = cast(str, converter.convert(phrase))
        
        if not is_all_chinese(phrase):
            continue
        if len(phrase) < _MINIMUM_LEN:
            continue
        if len(phrase) > _MAXIMUM_LEN:
            continue
        if any(phrase.endswith(ending) for ending in _LIST_PAGE_ENDINGS):
            continue
            
        if previous_phrase is not None and len(previous_phrase) >= 4 and phrase.startswith(previous_phrase):
            continue
            
        filtered.append(phrase)
        previous_phrase = phrase
        
    return filtered

def main():
    parser = argparse.ArgumentParser(description="Convert Wikipedia titles to Rime dictionary format.")
    _ = parser.add_argument('--dir', type=str, help="Directory containing extracted files (zhwikisource, zhwiktionary, zhwiki).")
    _ = parser.add_argument('--dest', type=str, help="Destination file path. If not set, prints to stdout.")
    args = parser.parse_args()
    
    args_dir = cast(str | None, args.dir)
    args_dest = cast(str | None, args.dest)

    converter = opencc.OpenCC('t2s.json')
    all_filtered_phrases: set[str] = set()

    for name, url in URLS.items():
        phrases: list[str] = []
        if args_dir:
            filename = url.split('/')[-1]
            filepath = os.path.join(args_dir, filename)
            if not os.path.exists(filepath):
                filepath = os.path.join(args_dir, f"{name}.gz")
                
            if os.path.exists(filepath):
                _ = sys.stderr.write(f"Reading local GZip file {filepath}...\n")
                phrases = read_local_gz_file(filepath)
            else:
                phrases = fetch_and_extract(url)
        else:
            phrases = fetch_and_extract(url)
            
        filtered = process_file(phrases, converter)
        all_filtered_phrases.update(filtered)

    sorted_phrases = sorted(list(all_filtered_phrases))

    _ = sys.stderr.write(f"Writing ...\n")
    if args_dest:
        with open(args_dest, 'w', encoding='utf-8') as f:
            for phrase in sorted_phrases:
                _ = f.write(f"{phrase}\tnz\t100\n")
    else:
        for phrase in sorted_phrases:
            _ = sys.stdout.write(f"{phrase}\tnz\t100\n")

if __name__ == '__main__':
    main()
