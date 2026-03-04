import os
import shutil
import signal
import subprocess
import time
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser_context():
    """Launches Playwright browser with video recording."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a directory for videos
        video_dir = Path(
            "/home/morganrcu/proyectos/venturalitica-integration/packages/venturalitica-sdk/tests/e2e/videos"
        )
        video_dir.mkdir(exist_ok=True)

        context = browser.new_context(record_video_dir=str(video_dir), record_video_size={"width": 1280, "height": 720})
        yield context
        browser.close()


@pytest.fixture(scope="function")
def sandbox_dir(tmp_path):
    """Creates a temporary sandbox directory for the dashboard test."""
    sandbox = tmp_path / "sandbox_dashboard"
    sandbox.mkdir()

    # Store original CWD
    cwd = os.getcwd()
    os.chdir(sandbox)
    yield sandbox
    # Cleanup
    os.chdir(cwd)
    # shutil.rmtree(sandbox) # Optional cleanup


@pytest.fixture(scope="function")
def dashboard_process(sandbox_dir):
    """Launches the Streamlit dashboard in the sandbox."""
    import sys
    import socket

    # Ensure env vars
    env = os.environ.copy()
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
    env["PYTHONPATH"] = src_path

    # Path to main.py
    main_py_path = os.path.join(src_path, "venturalitica/dashboard/main.py")

    if not os.path.exists(main_py_path):
        raise FileNotFoundError(f"Dashboard main.py not found at {main_py_path}")

    # Use sys.executable to ensure we use the same python env
    full_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        main_py_path,
        "--server.headless=true",
        "--server.port=8599",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]

    print(f"Launching Streamlit: {' '.join(full_cmd)}")

    # Run without PIPE to see output in pytest -s
    proc = subprocess.Popen(full_cmd, cwd=str(sandbox_dir), env=env)

    # Wait for port to be open
    start_time = time.time()
    api_ready = False
    while time.time() - start_time < 15:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", 8599)) == 0:
                api_ready = True
                break
        time.sleep(1)

    if not api_ready:
        proc.terminate()
        raise TimeoutError("Streamlit failed to start on port 8599 within 15 seconds.")

    yield proc

    # Teardown
    proc.terminate()
    proc.wait()
