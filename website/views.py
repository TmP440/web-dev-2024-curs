import bleach
import hashlib
import markdown
import os

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app,
)
from flask_login import current_user
from werkzeug.utils import secure_filename

from . import db
from . import decorators
from .models import Music, Style, Cover, Review

views = Blueprint("views", __name__)

ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def commit_music_data(request, id=None):
    title = request.form.get("title")
    style = request.form.getlist("style")
    short_description = bleach.clean(request.form.get("short_description"))
    year = request.form.get("year")
    label = request.form.get("label")
    author = request.form.get("author")
    pages = request.form.get("pages")

    if not all(
        [
            title,
            style,
            year,
            label,
            author,
            pages,
            short_description != "Краткое описание",
        ]
    ):
        flash("Пожалуйста, введите все данные", category="error")
        return redirect(request.url)

    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            flash("Пожалуйста, введите все данные", category="error")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            file_md5 = hashlib.md5(file.read()).hexdigest()
            filename = secure_filename(file.filename)
            try:
                cover = db.session.scalars(
                    db.select(Cover).where(Cover.MD5_hash == file_md5)
                ).one_or_none()
                if cover:
                    cover_id = cover.id
                else:
                    new_cover = Cover(
                        file_name=filename,
                        MIME_type=file.content_type,
                        MD5_hash=file_md5,
                    )
                    db.session.add(new_cover)
                    db.session.flush()
                    cover_id = new_cover.id
                new_music = Music(
                    title=title,
                    short_description=short_description,
                    year=year,
                    label=label,
                    author=author,
                    pages=pages,
                    cover_id=cover_id,
                )
                styles = db.session.scalars(
                    db.select(Style).where(Style.id.in_(style))
                ).all()
                new_music.styles.extend(styles)
                db.session.add(new_music)
                db.session.commit()
                music_id = new_music.id
                file.seek(0)
                file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

                return redirect(url_for("views.view_music", id=music_id))
            except Exception as e:
                db.session.rollback()
                flash(
                    "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                    category="error",
                )
                return redirect(request.url)
    else:
        music = Music.query.get_or_404(id)
        music.title = request.form.get("title")
        music.style = request.form.getlist("style")
        music.short_description = bleach.clean(request.form.get("short_description"))
        music.year = request.form.get("year")
        music.label = request.form.get("label")
        music.author = request.form.get("author")
        music.pages = request.form.get("pages")
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                category="error",
            )
            return redirect(request.url)


@views.route("/")
def home_page():
    musics = Music.query.order_by(Music.year.desc())

    page = request.args.get("page")

    if page and page.isdigit():
        page = int(page)
    else:
        page = 1

    pages = musics.paginate(page=page, per_page=10)

    return render_template("home.html", user=current_user, pages=pages)


@views.route("/add_music", methods=["GET", "POST"])
@decorators.role_required("admin")
def add_music():
    if request.method == "POST":
        return commit_music_data(request)

    styles = db.session.scalars(db.select(Style)).all()

    return render_template("add_music.html", user=current_user, music=None, styles=styles)


@views.route("/view_music/<int:id>", methods=["GET", "POST"])
@decorators.role_required("admin", "mod", "user")
def view_music(id):
    music = Music.query.get_or_404(id)
    music.short_description = markdown.markdown(music.short_description)

    styles = db.session.scalars(db.select(Style)).all()

    reviews = db.session.scalars(db.select(Review).where(Review.music_id == id)).all()
    user_reviewed = False

    for review in reviews:
        review.text = markdown.markdown(review.text)
        if review.user_id == current_user.id:
            user_reviewed = True

    return render_template(
        "view_music.html",
        user=current_user,
        music=music,
        styles=styles,
        reviews=reviews,
        user_reviewed=user_reviewed,
    )


@views.route("/edit_music/<id>", methods=["GET", "POST"])
@decorators.role_required("admin", "mod")
def edit_music(id):
    music = Music.query.get_or_404(id)

    if request.method == "POST":
        commit_music_data(request, id)
        return redirect(url_for("views.home_page"))
    else:
        styles = db.session.scalars(db.select(Style)).all()
        return render_template(
            "edit_music.html", user=current_user, music=music, styles=styles
        )


@views.route("/delete_music/<id>", methods=["GET", "POST"])
@decorators.role_required("admin")
def delete_music(id):
    music = Music.query.get_or_404(id)

    try:
        cover = music.cover
        cover_count = db.session.scalars(
            db.select(Music).where(cover.id == Music.cover_id)
        ).all()
        db.session.delete(music)
        if cover and len(cover_count) == 1:
            file_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], cover.file_name
            )
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(cover)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f"Error occured: {e}", category="error")

    return redirect(url_for("views.home_page"))


@views.route("/add_review/<id>", methods=["GET", "POST"])
@decorators.role_required("admin", "mod", "user")
def add_review(id):
    music = Music.query.get_or_404(id)

    reviews = db.session.scalars(db.select(Review).where(Review.music_id == id)).all()

    for review in reviews:
        if review.user_id == current_user.id:
            flash("Вы уже оставляли отзыв", category="error")
            return redirect(url_for("views.home_page"))

    if request.method == "POST":
        music_id = id
        user_id = current_user.id
        score = request.form.get("score")
        text = bleach.clean(request.form.get("text"))

        if text == "Напишите свой отзыв":
            flash("Пожалуйста, введите все данные", category="error")
            return redirect(request.url)

        try:
            new_review = Review(
                music_id=music_id, user_id=user_id, score=score, text=text
            )
            db.session.add(new_review)
            db.session.commit()
            return redirect(url_for("views.view_music", id=music_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error occured: {e}", category="error")

    return render_template("add_review.html", user=current_user, music=music)
