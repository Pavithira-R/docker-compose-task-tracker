import re
import unittest
import uuid

from app import Task, create_app, db


class TaskTrackerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.title = "Automated test " + uuid.uuid4().hex

    def tearDown(self):
        # Remove only this test's task, preserving other saved tasks.
        with self.app.app_context():
            task = db.session.execute(
                db.select(Task).where(Task.title == self.title)
            ).scalar_one_or_none()

            if task is not None:
                db.session.delete(task)
                db.session.commit()

            db.session.remove()

    def csrf_token(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.get_data(as_text=True),
        )
        self.assertIsNotNone(match, "CSRF token missing from page")
        return match.group(1)
     
        def test_metrics(self):
        self.client.get("/")
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "flask_http_request_total",
            response.get_data(as_text=True),
        )

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "healthy")

    def test_task_lifecycle(self):
        token = self.csrf_token()

        response = self.client.post(
            "/tasks",
            data={"title": self.title, "csrf_token": token},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.title, response.get_data(as_text=True))

        with self.app.app_context():
            task = db.session.execute(
                db.select(Task).where(Task.title == self.title)
            ).scalar_one()
            task_id = task.id
            self.assertFalse(task.completed)

        for expected in (True, False):
            response = self.client.post(
                f"/tasks/{task_id}/toggle",
                data={"csrf_token": token},
            )
            self.assertEqual(response.status_code, 302)

            with self.app.app_context():
                task = db.session.get(Task, task_id)
                self.assertEqual(task.completed, expected)

        response = self.client.post(
            f"/tasks/{task_id}/delete",
            data={"csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Task, task_id))

    def test_empty_task_rejected(self):
        response = self.client.post(
            "/tasks",
            data={"title": "   ", "csrf_token": self.csrf_token()},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_csrf_rejected(self):
        response = self.client.post(
            "/tasks",
            data={"title": self.title},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()