import tkinter as tk

import pytest


@pytest.fixture(scope="session")
def tk_root():
    """Share one Tk interpreter across GUI unit and integration tests."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
