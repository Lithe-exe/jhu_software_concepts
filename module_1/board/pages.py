from flask import Blueprint, render_template
# This file defines the routes for the web pages and is imported in __init__.py for blueprint registration
bp = Blueprint("pages", __name__)

@bp.route("/")#Renders home.html when home page is accessed
def home():
    return render_template("pages/home.html")

@bp.route("/biotech")#Renders biotech.html when about page is accessed
def about():
    return render_template("pages/biotech.html")

@bp.route("/contact")#Renders contact.html when contact page is accessed
def contact():
    return render_template("pages/contact.html")

@bp.route("/projects")#Renders projects.html when projects page is accessed
def projects():
    return render_template("pages/projects.html")