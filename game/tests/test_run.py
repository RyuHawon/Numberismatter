from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RunSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", nickname="유저", password="pw-long-1234")
        self.start_url = reverse("game:start_run")
        self.abandon_url = reverse("game:abandon_run")

    def test_login_required(self):
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_get_not_allowed(self):
        # 런 시작/포기는 상태 변경이라 POST만 허용한다
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.start_url).status_code, 405)
        self.assertEqual(self.client.get(self.abandon_url).status_code, 405)

    def test_start_creates_run_with_default_state(self):
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        run = self.client.session["run"]
        self.assertEqual(run["phase"], "roll")
        self.assertEqual(run["current_act"], 1)
        self.assertEqual(run["current_stage"], 1)
        self.assertEqual(run["hp"], self.user.character.max_hp)
        self.assertEqual(run["pending_gold"], 0)
        self.assertEqual(run["skills"], {})

    def test_start_does_not_overwrite_existing_run(self):
        # 이미 진행 중인 런이 있으면 다시 시작해도 덮어쓰지 않는다
        self.client.force_login(self.user)
        session = self.client.session
        session["run"] = {"current_act": 2, "hp": 50}
        session.save()
        self.client.post(self.start_url)
        self.assertEqual(self.client.session["run"]["current_act"], 2)
        self.assertEqual(self.client.session["run"]["hp"], 50)

    def test_abandon_removes_run(self):
        self.client.force_login(self.user)
        self.client.post(self.start_url)
        self.client.post(self.abandon_url)
        self.assertNotIn("run", self.client.session)
