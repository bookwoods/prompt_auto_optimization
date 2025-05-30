import subprocess
import sys
from pathlib import Path


def main():
    # app_path = Path(__file__).parent / "xlsx_parser.py"
    app_path = Path(__file__).parent / "app.py"
    subprocess.run(["streamlit", "run", str(app_path)])


if __name__ == "__main__":
    main()
