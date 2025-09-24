# yt-dlp-scripts

A script to integrate **yt-dlp** in a GUI, with beets

## Requirements

- Python 3.x (tested on **3.13**)  
- `ffmpeg` (for media processing)

## Installation & Setup

### Install Requirements

#### Windows

1. Ensure Python 3.x is installed, and is available on `PATH`.  
2. Install ffmpeg — e.g. via **winget**:
   ```powershell
   winget install ffmpeg
(Alternatively, you could use a manually downloaded build and add it to your PATH.)

#### Arch Linux (or Arch-based distros)

1. Update your system:

```bash
sudo pacman -Syu
```

2. Install Python and ffmpeg:

```bash
sudo pacman -S python ffmpeg
```

### Download the code

1. Clone the repo:

```bash
git clone https://github.com/Rbel12b/yt-dlp-scripts.git
cd yt-dlp-scripts
```

2. Run the GUI:

```bash
./yt-dlp-gui.pyw # Or use a file Explorer and open the file
```

## First use

When running the script the first time(or after deleting the config directory), it will create a python venv in ~/.config/beets/.venv
It will also install yt-dlp and beets inside that venv automatically (The script will open separate terminals on windows).
*Important* the script will create a new beets config in ~/.config/beets/config.yaml if it doesn't exist. If you already have a beets config you might have to modify the script.

## Usage

Just launching yt-dlp-gui.pyw will bring up a GUI that wraps yt-dlp functionality.
You can pass “normal” flags inside the GUI wrapper to yt-dlp.
After downloading audio files it will try to import them to the beets library.
You also have an additional option to import a folder into the beets library.

## License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

## Contributing
You’re welcome to submit pull requests or modifications. Please keep attribution intact and note any changes in your PR description.
