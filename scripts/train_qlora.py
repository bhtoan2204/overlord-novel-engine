#!/usr/bin/env python3
"""Refuse to start training unless both switches are on. Does not launch a job."""

import argparse

from app.core.config import get_settings
from app.training.qlora import run_training


def main() -> None:
    parser = argparse.ArgumentParser(description="QLoRA is optional and disabled by default.")
    parser.add_argument("--enable-training", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    run_training(settings.training_enabled, args.enable_training)


if __name__ == "__main__":
    main()
