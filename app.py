import os

import click
from flask import Flask, abort, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import URL, text
from prometheus_client import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics

db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("DB_HOST", "db"),
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True
    }

    db.init_app(app)
    CSRFProtect(app)
     PrometheusMetrics(
        app,
        registry=CollectorRegistry(),
        group_by="endpoint",
    )

    @app.cli.command("init-db")
    def init_db():
        with app.app_context():
            db.create_all()
        click.echo("Database tables created.")

    @app.get("/")
    def index():
        tasks = db.session.execute(
            db.select(Task).order_by(Task.id.desc())
        ).scalars().all()
        return render_template("index.html", tasks=tasks)

    @app.post("/tasks")
    def add_task():
        title = request.form.get("title", "").strip()

        if not title or len(title) > 200:
            abort(400, description="Enter a task between 1 and 200 characters.")

        db.session.add(Task(title=title))
        db.session.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        task = db.get_or_404(Task, task_id)
        task.completed = not task.completed
        db.session.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        task = db.get_or_404(Task, task_id)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy"}, 200
        except Exception:
            db.session.rollback()
            app.logger.exception("Database health check failed")
            return {"status": "unhealthy"}, 503

    return app