"""Compatibility wrapper exposing DB loader helpers under board.load_data."""

from db.load_data import clean_date, clean_val, get_db_info, get_val, load_data

__all__ = ["clean_date", "clean_val", "get_db_info", "get_val", "load_data"]
