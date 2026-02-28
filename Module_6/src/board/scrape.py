"""Compatibility wrapper exposing GradCafeScraper under board.scrape."""

from worker.etl.scrape import GradCafeScraper

__all__ = ["GradCafeScraper"]
