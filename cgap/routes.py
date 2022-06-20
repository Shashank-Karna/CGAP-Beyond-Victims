import email
import secrets
import os
from PIL import Image
from click import password_option
from flask import render_template, url_for, flash, redirect, request, abort
from cgap.forms import RegistrationForm, LoginForm
from cgap import app, db
from cgap.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


posts = [
    {
        "author": "Shashank Karna",
        "title": "Blog Post 1",
        "content": "First post content",
        "date_posted": "June 19, 2018",
    },
    {
        "author": "Raghuttam Parvatikar",
        "title": "Blog Post 2",
        "content": "Second post content",
        "date_posted": "June 20, 2018",
    },
]


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash("Your account has been created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == "admin@blog.com" and form.password.data == "password":
            flash("You have been logged in!", "success")
            return redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check username and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))
