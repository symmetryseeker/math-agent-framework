"""
Friendly error/warning messages for optional engine unavailability.
Instead of cryptic tracebacks, users get clear, actionable messages.
"""

import sys
from typing import Optional, Callable


class EngineStatus:
    """Tracks the status of an optional engine and provides friendly messages."""

    def __init__(self, name: str, install_hint: str, impact: str, pip_package: str = ""):
        self.name = name
        self.install_hint = install_hint
        self.impact = impact
        self.pip_package = pip_package
        self._available: Optional[bool] = None
        self._check_fn: Optional[Callable] = None

    def set_check(self, fn: Callable[[], bool]):
        self._check_fn = fn

    def is_available(self) -> bool:
        if self._available is None and self._check_fn:
            self._available = self._check_fn()
        return self._available or False

    def get_message(self) -> str:
        if self.is_available():
            return f"  {self.name}: available"
        return (
            f"  {self.name}: not installed (optional)\n"
            f"    Impact: {self.impact}\n"
            f"    Install: {self.install_hint}"
        )


# Registry of all optional engines
OPTIONAL_ENGINES = {
    "sagemath": EngineStatus(
        name="SageMath Cross-Validation",
        install_hint="npm install -g @justice8096/sagemath-mcp-server",
        impact="Cross-engine verification unavailable. SymPy + Monte Carlo still validate results.",
        pip_package="",
    ),
    "quantecon": EngineStatus(
        name="QuantEcon Dynamic Optimization",
        install_hint="pip install quantecon",
        impact="Riccati/LQ/Markov chain/Nash equilibrium solvers unavailable.",
        pip_package="quantecon",
    ),
    "python-docx": EngineStatus(
        name="Word Document Output",
        install_hint="pip install python-docx",
        impact="DOCX export unavailable. Markdown and JSON formats still work.",
        pip_package="python-docx",
    ),
    "matplotlib": EngineStatus(
        name="Matplotlib Visualization",
        install_hint="pip install matplotlib",
        impact="2D/3D/GIF export unavailable. Text-based output still works.",
        pip_package="matplotlib",
    ),
    "manim": EngineStatus(
        name="Manim Mathematical Animation",
        install_hint="pip install manim",
        impact="High-quality 3Blue1Brown-style animations unavailable. Matplotlib GIFs still work.",
        pip_package="manim",
    ),
}


def check_all_engines() -> dict:
    """Check availability of all optional engines."""
    results = {}
    for key, engine in OPTIONAL_ENGINES.items():
        if engine._check_fn is None:
            if key == "sagemath":
                engine.set_check(lambda: False)  # default: assume not installed
            else:
                pkg = engine.pip_package
                engine.set_check(lambda p=pkg: __import__(p) or True if p else False)
        try:
            available = engine.is_available()
        except Exception:
            available = False
        results[key] = {"name": engine.name, "available": available, "message": engine.get_message()}
    return results


def print_status_banner():
    """Print a friendly status banner showing which engines are available."""
    lines = ["", "=" * 60, "  Engine Status", "=" * 60]
    available_count = 0
    total = len(OPTIONAL_ENGINES)

    for key, engine in OPTIONAL_ENGINES.items():
        status = engine.get_message()
        lines.append(status)
        if engine.is_available():
            available_count += 1

    lines.append("")
    lines.append(f"  Core engines (SymPy/NumPy/SciPy): always available")
    lines.append(f"  Optional engines: {available_count}/{total} available")
    lines.append("=" * 60)
    return "\n".join(lines)


def friendly_import_error(package: str, feature: str, install_cmd: str = "") -> str:
    """Generate a friendly message when an optional import fails."""
    cmd = install_cmd or f"pip install {package}"
    return (
        f"\n  Feature '{feature}' requires '{package}' (not installed).\n"
        f"  Install: {cmd}\n"
        f"  All other features continue to work.\n"
    )
