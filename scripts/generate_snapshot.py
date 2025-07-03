from pathlib import Path

EXCLUDED_SUFFIXES = {".db", ".sqlite", ".toml", ".env", ".pyc"}
EXCLUDED_DIRS = {"venv", "env", "__pycache__", ".git", ".streamlit"}

def get_file_tree(root="."):
    tree_lines = ["📁 Project Structure:"]
    def walk(path: Path, indent=""):
        for child in sorted(path.iterdir()):
            if child.name in EXCLUDED_DIRS or child.name.startswith("."):
                continue
            tree_lines.append(f"{indent}- {child.name}")
            if child.is_dir():
                walk(child, indent + "  ")
    walk(Path(root))
    return "\n".join(tree_lines)

def get_file_contents(root="."):
    snapshot = []
    for path in Path(root).rglob("*"):
        if (
            path.is_file()
            and not any(part in EXCLUDED_DIRS or part.startswith(".") for part in path.parts)
            and path.suffix not in EXCLUDED_SUFFIXES
        ):
            try:
                content = path.read_text(encoding="utf-8")[:8000]  # Trim long files
                snapshot.append(f"\n# ===== {path} =====\n{content}")
            except Exception as e:
                snapshot.append(f"\n# ===== {path} =====\n[Could not read file: {e}]")
    return "\n".join(snapshot)

if __name__ == "__main__":
    with open("project_snapshot.txt", "w", encoding="utf-8") as f:
        f.write(get_file_tree())
        f.write("\n\n")
        f.write(get_file_contents())
    print("✅ Snapshot saved to project_snapshot.txt")
