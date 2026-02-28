"""Compatibility wrapper exposing DataCleaner under board.clean."""

from worker.etl.clean import DataCleaner

__all__ = ["DataCleaner"]
