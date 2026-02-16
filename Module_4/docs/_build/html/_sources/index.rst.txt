.. Modulo_4 documentation master file, created by
   sphinx-quickstart on Sun Feb 15 18:31:59 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Module_4 documentation
======================

Documentation for the Testing and Documentation Assignment  

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   testing

Overview
--------
This application scrapes, cleans, and analyzes graduate school admission data from GradCafe. 
It consists of a Flask web layer, a PostgreSQL database, and an ETL (Extract, Transform, Load) pipeline.

Architecture
------------
* **Web Layer**: Flask application serving an analysis dashboard.
* **ETL Layer**: 
    * Scraper: Fetches HTML from GradCafe.
    * Cleaner: Normalizes dates, grades, and statuses.
    * Loader: Inserts data into PostgreSQL.
* **Database**: Stores applicant history to allow trend analysis.
