import email
from fileinput import filename
import secrets
import os
from PIL import Image
from click import password_option
from flask import render_template, url_for, flash, redirect, request, abort
from cgap.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    PostForm,
    SubmitPostForm,
)
from cgap import app, db, bcrypt
from cgap.models import Submission, User, Post
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.order_by(Post.date_posted.desc())
    return render_template("home.html", posts=posts)


@app.route("/blogs")
def blogs():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("blogs.html", title="Blogs", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check Username and Password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture, title):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    if title == "account":
        picture_path = os.path.join(
            app.root_path, "static/images/profile_pics", picture_fn
        )
    else:
        picture_path = os.path.join(app.root_path, "static/images", picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been successfully updated!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        "static", filename="images/profile_pics/" + current_user.image_file
    )
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, "submit_post")
        else:
            picture_file = "women_default.jpg"
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user,
            image_file=picture_file,
        )
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", "success")
        return redirect(url_for("blogs"))
    return render_template(
        "create_post.html", title="New Post", form=form, legend="New Post"
    )


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your Post has been updated!", "success")
        return redirect(url_for("post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template(
        "create_post.html", title="Update Post", form=form, legend="Update Post"
    )


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your Post has been deleted!", "success")
    return redirect(url_for("blogs"))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=5)
    )
    return render_template("user_posts.html", posts=posts, user=user)


@app.route("/submit_post", methods=["GET", "POST"])
def submit_post():
    form = SubmitPostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, "submit_post")
        else:
            picture_file = url_for("static", filename="images/women_default.jpg")
        submission = Submission(
            title=form.title.data,
            content=form.content.data,
            author=form.author.data,
            image_file=picture_file,
        )
        db.session.add(submission)
        db.session.commit()
        flash("Your post has been submitted!", "success")
        return redirect(url_for("blogs"))
    return render_template(
        "submit_post.html", title="Submit Post", form=form, legend="Submit Post"
    )


@app.route("/submissions")
# @login_required
def submissions():
    page = request.args.get("page", 1, type=int)
    submissions = Submission.query.order_by(Submission.date_posted.desc()).paginate(
        page=page, per_page=5
    )
    return render_template(
        "submissions.html", title="Submissions", submissions=submissions
    )


@app.route("/submission/<int:submission_id>")
# @login_required
def submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return render_template(
        "submission.html", title=submission.title, submission=submission
    )


@app.route("/submission/<int:submission_id>/update", methods=["GET", "POST"])
@login_required
def edit_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    form = SubmitPostForm()
    if form.validate_on_submit():
        submission.title = form.title.data
        submission.content = form.content.data
        submission.image_file = form.picture.data
        db.session.commit()
        flash("This submission has been updated!", "success")
        return redirect(url_for("submission", submission_id=submission.id))
    elif request.method == "GET":
        form.title.data = submission.title
        form.content.data = submission.content
        form.picture.data = submission.image_file
    return render_template(
        "create_post.html", title="Update Post", form=form, legend="Update Post"
    )


@app.route("/submission/<int:submission_id>/delete", methods=["POST"])
@login_required
def delete_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    db.session.delete(submission)
    db.session.commit()
    flash("This submission has been deleted!", "success")
    return redirect(url_for("submissions"))


@app.route("/submission/<int:submission_id>/upload", methods=["GET", "POST"])
@login_required
def upload_as_post(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    post = Post(
        title=submission.title,
        content=submission.content,
        author=current_user,
        image_file=submission.image_file,
    )
    db.session.add(post)
    db.session.commit()
    flash("This submission has been uploaded as a post!", "success")
    return redirect(url_for("blogs"))
