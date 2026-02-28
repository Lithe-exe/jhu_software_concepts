"""Compatibility wrapper exposing DataAnalyzer under board.query_data."""

from worker.etl.query_data import DataAnalyzer

__all__ = ["DataAnalyzer"]
