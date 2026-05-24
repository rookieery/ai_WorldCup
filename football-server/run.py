"""Convenience entry point for running the API with uvicorn.

Usage::

    python run.py                  # development (reload enabled)
    python run.py --prod           # production (single worker, no reload)
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Football World Cup 2026 API server")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode (no reload, optimized settings)",
    )
    args = parser.parse_args()

    import uvicorn

    if args.prod:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info",
        )
    else:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug",
        )


if __name__ == "__main__":
    main()
