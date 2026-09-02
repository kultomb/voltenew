import sys
import build_exe_release

if __name__ == "__main__":
    sys.exit(build_exe_release.main() or 0)
