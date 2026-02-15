# DI.fm Likes Updater

A small desktop utility that exports and maintains a local CSV archive of your **DI.fm liked tracks**.

Instead of manually scrolling through your likes, this tool connects to the official AudioAddict API and keeps an up-to-date list automatically.

---

## Features

- ✅ One-click desktop GUI
- ✅ Incremental update mode (fast — checks only newest likes)
- ✅ Full rebuild mode (re-download entire library)
- ✅ Newest tracks always appear at the top
- ✅ Exports to a portable CSV file
- ✅ No data stored remotely

---

## Download

Prebuilt Windows executable available under:

**Releases → Assets → di-fm-likes-updater.exe**

No Python installation required.

---

## Usage

1. Launch the application.
2. Enter your DI.fm username/email and password.
3. Choose a mode:

**A) Check / Update (Fast)**  
Checks only recent likes and adds new tracks to your CSV.

**B) Rebuild Full List**  
Re-downloads your entire likes library from scratch.

4. Click **Update Likes**.

Your file will appear as:

```
di_likes.csv
```

in the same folder as the program.

---

## CSV Output

Columns:

```
TrackID | Artist | Track | Source | Duration | Liked
```

The file is ordered newest → oldest.

---

## Security & Privacy

- Credentials are sent **only** to `api.audioaddict.com` over HTTPS.
- Login information is **not stored** locally.
- No analytics, tracking, or external uploads occur.
- The application simply requests your liked tracks and writes a local CSV file.
- Full source code is available in this repository.

---

## Running From Source (Optional)

Requirements:

- Python 3.10+
- `requests`

Install dependencies:

```bash
py -m pip install requests
```

Run GUI:

```bash
py di_likes_gui.py
```

---

## Building the Executable

```bash
py -m PyInstaller --onefile --windowed --icon=di_icon.ico di_likes_gui.py
```

The compiled application will appear in:

```
dist/
```

---

## Notes

This project is unofficial and not affiliated with DI.fm or AudioAddict.

---

## License

MIT License
