#!/bin/bash

# Copyright (c) 2025 Rbel12b
# Licensed under the MIT License. See LICENSE file in the project root for details.

set -euo pipefail

# Config
OUTDIR="$HOME/Downloads/Music"
VIDEO_OUTDIR="$HOME/Videos"
VENVDIR="$OUTDIR/.venv"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <URL|video|delete-config|beet|update ...>"
    exit 1
fi

if [ "$1" != "beet" ]; then
    URL="$1"
else
    URL=""
fi

mkdir -p "$OUTDIR"

if [ ! -d "$VENVDIR" ]; then
    python3.12 -m venv "$VENVDIR"
    source "$VENVDIR/bin/activate"
    pip install --upgrade pip
    pip install "beets[fetchart,lyrics,mbsubmit,embedart,chroma]" mutagen
    pip install yt-dlp
else
    source "$VENVDIR/bin/activate"
fi
    
if [ "$1" == "update" ]; then
    pip install --upgrade pip
    pip install --upgrade "beets[fetchart,lyrics,mbsubmit,embedart,chroma]" mutagen yt-dlp
    echo "Updated beets and yt-dlp."
    exit 0
fi

download() {
    if [ "$1" == "video" ]; then
        shift
        yt-dlp \
        --cookies-from-browser chrome:Default \
        --download-archive "$OUTDIR/yt-dlp-archive.txt" \
        -N 10 \
        -o "$VIDEO_OUTDIR/%(title)s [%(id)s].%(ext)s" \
        $@
    else
        yt-dlp \
        --cookies-from-browser chrome:Default \
        --extract-audio --audio-format mp3 \
        --embed-thumbnail --add-metadata \
        --metadata-from-title "%(artist)s - %(title)s" \
        --download-archive "$OUTDIR/yt-dlp-archive.txt" \
        -N 10\
        -o "$OUTDIR/%(title)s [%(id)s].%(ext)s" \
        $@
    fi
}

CONFIG_DIR="$HOME/.config/beets"
CONFIG_FILE="$CONFIG_DIR/config.yaml"

if [ "$URL" == "delete-config" ]; then
    rm -rf "$CONFIG_DIR"
    echo "Deleted beets config directory."
    exit 0
fi

if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" <<EOF
directory: $HOME/Music
library: $HOME/.local/share/beets/library.db

import:
    move: yes
    write: yes
    copy: no
    autotag: yes
    quiet_fallback: asis

plugins: fetchart lyrics mbsync embedart chroma

fetchart:
    auto: yes
    maxwidth: 1200
    quality: 90
    sources: spotify itunes coverart albumart

embedart:
    auto: yes                 # embed art automatically after fetching
    remove_art_file: yes      # delete external cover image after embedding
    ifempty: no               # overwrite existing embedded art (optional)
    compare_threshold: 0      # skip similarity check; set >0 to avoid embedding drastically different images
    maxwidth: 1200            # downscale images before embedding
    quality: 80               # JPEG quality for embedding

lyrics:
    auto: yes
    sources: [lrclib, genius, tekstowo]
    synced: yes
    force: yes
EOF
fi

if [ "$1" == "video" ]; then
    download $@
    exit 0
fi

if [ "$URL" != "" ]; then
    download $@
    echo "Download complete. Importing into beets library..."
    beet import -a -s "$OUTDIR"
else
    $@
fi

beet list -f '$path' > ~/Music/vlc_library.m3u
