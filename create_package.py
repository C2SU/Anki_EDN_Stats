import os
import zipfile

# Configuration
SOURCE_DIR = r"C:\Users\Pipou\AppData\Roaming\Anki2\addons21\Anki_EDN_Stats"
DEST_PATH = os.path.join(os.environ["USERPROFILE"], "OneDrive - Education", "Bureau", "edn_stat_v1.0.0.ankiaddon")
EXCLUDES = [
    "__pycache__",
    "user_state.json",
    "tests",
    "debug_",
    "manual_",
    "INSTRUCTIONS_DEBUG",
    ".git",
    ".vscode"
]

def should_exclude(rel_path):
    parts = rel_path.split(os.sep)
    for part in parts:
        for exclude in EXCLUDES:
            if exclude in part or (exclude.startswith("*") and part.endswith(exclude.replace("*", ""))):
                return True
    return False

def create_addon_package():
    print(f"Packaging addon from: {SOURCE_DIR}")
    print(f"Destination: {DEST_PATH}")
    
    with zipfile.ZipFile(DEST_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory
        for root, dirs, files in os.walk(SOURCE_DIR):
            # Modify dirs in-place to skip excluded directories during walk
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            
            for file in files:
                if should_exclude(file):
                    continue
                
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, SOURCE_DIR)
                
                # Verify web/index.html is included specifically
                if "web" in rel_path and "index.html" in rel_path:
                    print(f"-> Found critical file: {rel_path}")
                
                print(f"Adding: {rel_path}")
                zipf.write(abs_path, rel_path)

    print("\nPackage created successfully!")

if __name__ == "__main__":
    try:
        create_addon_package()
    except Exception as e:
        print(f"Error: {e}")
