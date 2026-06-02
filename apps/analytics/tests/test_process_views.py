import os
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.analytics.models import Agent, Audio, Process, Typification, WordList
from apps.common.constants import (
    PROCESS_STATE_FINISHED,
    PROCESS_STATE_NO_AUDIOS,
    PROCESS_STATE_READY,
    PROCESS_STATE_TRANSCRIBED,
    PROCESS_STATE_TRANSCRIBING_STOPPED,
    RESTART_EXTRA_FULL,
    RESTART_EXTRA_PARTIAL,
    SCOPE_CAMPAIGN,
    SCOPE_NONE,
    SCOPE_USER,
)
from apps.users.models import Campaign, Role, User


class ProcessViewsBaseTestCase(TestCase):
    """Base test case for Process views with various API actions."""

    fixtures = ["prod/roles.json", "prod/campaigns.json", "prod/users.json"]

    def setUp(self):
        """Set up test data."""
        # Create roles with different permissions
        self.admin_role = Role.objects.create(
            name="TEST ADMIN ROLE",
            is_active=True,
            can_add_process=True,
            can_edit_process=True,
            can_delete_process=True,
            can_history_process=True,
            scope_process=SCOPE_CAMPAIGN,
        )

        self.user_scope_role = Role.objects.create(
            name="TEST USER SCOPE ROLE",
            is_active=True,
            can_add_process=True,
            can_edit_process=True,
            can_delete_process=True,
            can_history_process=True,
            scope_process=SCOPE_USER,
        )

        self.list_only_role = Role.objects.create(
            name="TEST LIST ONLY ROLE",
            is_active=True,
            can_add_process=False,
            can_edit_process=False,
            can_delete_process=False,
            can_history_process=True,
            scope_process=SCOPE_CAMPAIGN,
        )

        self.no_perm_role = Role.objects.create(
            name="TEST NO PERM ROLE",
            is_active=True,
            can_add_process=False,
            can_edit_process=False,
            can_delete_process=False,
            can_history_process=False,
            scope_process=SCOPE_NONE,
        )

        # Create test campaigns
        self.test_campaign = Campaign.objects.create(
            name="TEST CAMPAIGN", description="Campaign for testing", is_active=True
        )

        self.other_campaign = Campaign.objects.create(
            name="OTHER CAMPAIGN", description="Another campaign for testing", is_active=True
        )

        # Create users with different roles
        self.admin_user = User.objects.create(
            username="99999999",
            password=make_password("password"),
            first_name="ADMIN",
            last_name="USER",
            document_type=1,
            document_number="99999999",
            role=self.admin_role,
            campaign=self.test_campaign,
            is_active=True,
        )

        self.user_scope_user = User.objects.create(
            username="66666666",
            password=make_password("password"),
            first_name="USER SCOPE",
            last_name="USER",
            document_type=1,
            document_number="66666666",
            role=self.user_scope_role,
            campaign=self.test_campaign,
            is_active=True,
        )

        self.list_only_user = User.objects.create(
            username="88888888",
            password=make_password("password"),
            first_name="LIST ONLY",
            last_name="USER",
            document_type=1,
            document_number="88888888",
            role=self.list_only_role,
            campaign=self.test_campaign,
            is_active=True,
        )

        self.no_perm_user = User.objects.create(
            username="77777777",
            password=make_password("password"),
            first_name="NO PERM",
            last_name="USER",
            document_type=1,
            document_number="77777777",
            role=self.no_perm_role,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test agent
        self.test_agent = Agent.objects.create(
            name="TEST AGENT",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test wordlist
        self.test_wordlist = WordList.objects.create(
            name="TEST WORDLIST",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test typification
        self.test_typification = Typification.objects.create(
            name="TEST TYPIFICATION",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test process owned by admin_user
        self.admin_process = Process.objects.create(
            name="ADMIN PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_READY,
        )
        self.admin_process.typifications.add(self.test_typification)

        # Create a test process owned by user_scope_user
        self.user_process = Process.objects.create(
            name="USER PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.user_scope_user,
            modify_user=self.user_scope_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_READY,
        )
        self.user_process.typifications.add(self.test_typification)

        # Create a running process
        self.running_process = Process.objects.create(
            name="RUNNING PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_READY,
            is_running=True,
        )
        self.running_process.typifications.add(self.test_typification)

        # Create a finished process
        self.finished_process = Process.objects.create(
            name="FINISHED PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_FINISHED,
        )
        self.finished_process.typifications.add(self.test_typification)

        # Create a soft-deleted process
        self.deleted_process = Process.objects.create(
            name="DELETED PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=False,
            state=PROCESS_STATE_READY,
        )
        self.deleted_process.typifications.add(self.test_typification)

        # Create a stopped process
        self.stopped_process = Process.objects.create(
            name="STOPPED PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_TRANSCRIBING_STOPPED,
        )
        self.stopped_process.typifications.add(self.test_typification)

        # Create a transcribed process
        self.transcribed_process = Process.objects.create(
            name="TRANSCRIBED PROCESS",
            wordlist=self.test_wordlist,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
            state=PROCESS_STATE_TRANSCRIBED,
        )
        self.transcribed_process.typifications.add(self.test_typification)

        # Load real test files
        self.mp3_path = os.path.join(
            os.path.dirname(__file__), "audios_for_testing", "demo_reducido.mp3"
        )
        self.zip_path = os.path.join(
            os.path.dirname(__file__), "audios_for_testing", "demo_compressed.zip"
        )

        with open(self.mp3_path, "rb") as f:
            self.real_mp3_content = f.read()

        with open(self.zip_path, "rb") as f:
            self.real_zip_content = f.read()

        self.real_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )

        self.real_zip_file = SimpleUploadedFile(
            "demo_compressed.zip", self.real_zip_content, content_type="application/zip"
        )
        self.admin_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.user_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.deleted_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.deleted_audio_deleted_process_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )

        # Create a test audio for the admin process
        self.admin_audio = Audio.objects.create(
            file=self.admin_audio_mp3_file,
            original_filename="test.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.admin_process,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test audio for the user process
        self.user_audio = Audio.objects.create(
            file=self.user_audio_mp3_file,
            original_filename="user_test.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.user_process,
            create_user=self.user_scope_user,
            modify_user=self.user_scope_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a soft-deleted audio
        self.deleted_audio = Audio.objects.create(
            file=self.deleted_audio_mp3_file,
            original_filename="deleted.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.admin_process,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=False,
        )

        # Create a soft-deleted audio
        self.deleted_audio_deleted_process = Audio.objects.create(
            file=self.deleted_audio_deleted_process_mp3_file,
            original_filename="deleted.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.deleted_process,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=False,
        )

        # Create clients for each user
        self.admin_client = Client()
        self.user_scope_client = Client()
        self.list_only_client = Client()
        self.no_perm_client = Client()
        self.anonymous_client = Client()

        # Log in the clients
        self.admin_client.login(username="99999999", password="password")
        self.user_scope_client.login(username="66666666", password="password")
        self.list_only_client.login(username="88888888", password="password")
        self.no_perm_client.login(username="77777777", password="password")


class ProcessAddViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_ADD action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.add_url = reverse("analytics:process:add")

    def test_get_add_admin_user(self):
        """User with can_add_process permission can access the add form."""
        response = self.admin_client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, "file")  # Check for file upload field

    def test_get_add_user_scope_user(self):
        """User with can_add_process permission and SCOPE_USER can access the add form."""
        response = self.user_scope_client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_get_add_list_only_user(self):
        """User with only list permission cannot access the add form."""
        response = self.list_only_client.get(self.add_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_no_perm_user(self):
        """User with no permissions cannot access the add form."""
        response = self.no_perm_client.get(self.add_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_anonymous_user(self):
        """Test that an anonymous user cannot access the add form."""
        response = self.anonymous_client.get(self.add_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_add_admin_user_success_no_file(self):
        """User with can_add_process permission can add a new process without a file."""
        data = {
            "name": "NEW PROCESS",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was created
        new_process = Process.objects.filter(name="NEW PROCESS").first()
        self.assertIsNotNone(new_process)
        self.assertTrue(new_process.is_active)
        self.assertEqual(new_process.state, PROCESS_STATE_NO_AUDIOS)
        self.assertEqual(new_process.campaign, self.test_campaign)
        self.assertEqual(new_process.create_user, self.admin_user)

    def test_post_add_admin_user_success_with_mp3(self):
        """User with can_add_process permission can add a new process with an mp3 file."""
        data = {
            "name": "NEW PROCESS WITH MP3",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
            "files": self.real_mp3_file,
            "agent": self.test_agent.pk,
            "agent_date": "2023-01-01",
        }
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was created
        new_process = Process.objects.filter(name="NEW PROCESS WITH MP3").first()
        self.assertIsNotNone(new_process)
        self.assertTrue(new_process.is_active)
        self.assertEqual(new_process.state, PROCESS_STATE_READY)
        self.assertEqual(new_process.campaign, self.test_campaign)
        self.assertEqual(new_process.create_user, self.admin_user)

        # Verify audio was created
        self.assertTrue(Audio.objects.filter(process=new_process).exists())

    def test_post_add_admin_user_success_with_zip(self):
        """User with can_add_process permission can add a new process with a zip file."""

        data = {
            "name": "NEW PROCESS WITH ZIP",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
            "files": self.real_zip_file,
            "agent": self.test_agent.pk,
            "agent_date": "2023-01-01",
        }
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was created
        new_process = Process.objects.filter(name="NEW PROCESS WITH ZIP").first()
        self.assertIsNotNone(new_process)
        self.assertTrue(new_process.is_active)
        self.assertEqual(new_process.state, PROCESS_STATE_READY)
        self.assertEqual(new_process.campaign, self.test_campaign)
        self.assertEqual(new_process.create_user, self.admin_user)

        # Verify audios were created
        self.assertTrue(Audio.objects.filter(process=new_process).exists())

    def test_post_add_admin_user_failure_missing_agent(self):
        """User with can_add_process permission gets form errors when missing agent with file."""
        data = {
            "name": "SHOULD NOT BE CREATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
            "files": self.real_mp3_file,
            # Missing agent
            "agent_date": "2023-01-01",
        }
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertContains(response, "invalid-feedback")  # Check for validation error class

        # Verify process was not created
        self.assertFalse(Process.objects.filter(name="SHOULD NOT BE CREATED").exists())

    def test_post_add_admin_user_failure_missing_agent_date(self):
        """User with can_add_process permission gets form errors when missing agent_date
        with file."""
        data = {
            "name": "SHOULD NOT BE CREATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
            "files": self.real_mp3_file,
            "agent": self.test_agent.pk,
            # Missing agent_date
        }
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertContains(response, "invalid-feedback")  # Check for validation error class

        # Verify process was not created
        self.assertFalse(Process.objects.filter(name="SHOULD NOT BE CREATED").exists())

    def test_post_add_user_scope_user_success(self):
        """User with can_add_process permission and SCOPE_USER can add a new process."""
        data = {
            "name": "USER SCOPE PROCESS",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.user_scope_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was created
        new_process = Process.objects.filter(name="USER SCOPE PROCESS").first()
        self.assertIsNotNone(new_process)
        self.assertTrue(new_process.is_active)
        self.assertEqual(new_process.campaign, self.test_campaign)
        self.assertEqual(new_process.create_user, self.user_scope_user)

    def test_post_add_list_only_user_forbidden(self):
        """User with only list permission cannot add a new process."""
        data = {
            "name": "SHOULD NOT BE CREATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.list_only_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not created
        self.assertFalse(Process.objects.filter(name="SHOULD NOT BE CREATED").exists())

    def test_post_add_no_perm_user_forbidden(self):
        """User with no permissions cannot add a new process."""
        data = {
            "name": "SHOULD NOT BE CREATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.no_perm_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not created
        self.assertFalse(Process.objects.filter(name="SHOULD NOT BE CREATED").exists())

    def test_post_add_anonymous_user_redirect(self):
        """Test that an anonymous user cannot add a new process."""
        data = {
            "name": "SHOULD NOT BE CREATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.anonymous_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify process was not created
        self.assertFalse(Process.objects.filter(name="SHOULD NOT BE CREATED").exists())

    def test_delete_add_bad_request(self):
        """Test that DELETE method is not allowed for add."""
        response = self.admin_client.delete(self.add_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessHomeViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_HOME action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_url = reverse("analytics:process:home")

    def test_get_home_admin_user(self):
        """User with can_list_process permission can access the home page."""
        response = self.admin_client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        # Validate template used
        self.assertTemplateUsed(response, "analytics/process/home.html")

    def test_get_home_user_scope_user(self):
        """User with can_list_process permission and SCOPE_USER can access the home page."""
        response = self.user_scope_client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "analytics/process/home.html")

    def test_get_home_list_only_user(self):
        """User with only list permission can access the home page."""
        response = self.list_only_client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "analytics/process/home.html")

    def test_get_home_no_perm_user(self):
        """User with no permissions cannot access the home page."""
        response = self.no_perm_client.get(self.home_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_home_anonymous_user(self):
        """Test that an anonymous user cannot access the home page."""
        response = self.anonymous_client.get(self.home_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_home_bad_request(self):
        """Test that POST method is not allowed for home."""
        response = self.admin_client.post(self.home_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessEditViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_EDIT action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.edit_url = reverse("analytics:process:edit", args=[self.admin_process.pk])
        self.edit_user_url = reverse("analytics:process:edit", args=[self.user_process.pk])
        self.edit_finished_url = reverse("analytics:process:edit", args=[self.finished_process.pk])
        self.edit_running_url = reverse("analytics:process:edit", args=[self.running_process.pk])

    def test_get_edit_admin_user(self):
        """User with can_edit_process permission can access the edit form."""
        response = self.admin_client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, self.admin_process.name)

    def test_get_edit_user_scope_user_own_process(self):
        """User with can_edit_process permission and SCOPE_USER can access the edit form
        for their own process."""
        response = self.user_scope_client.get(self.edit_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, self.user_process.name)

    def test_get_edit_user_scope_user_other_process(self):
        """User with can_edit_process permission and SCOPE_USER cannot access the edit form
        for other users' processes."""
        response = self.user_scope_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_list_only_user(self):
        """User with only list permission cannot access the edit form."""
        response = self.list_only_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_no_perm_user(self):
        """User with no permissions cannot access the edit form."""
        response = self.no_perm_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_anonymous_user(self):
        """Test that an anonymous user cannot access the edit form."""
        response = self.anonymous_client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_edit_finished_process(self):
        """Test that a finished process cannot be edited."""
        response = self.admin_client.get(self.edit_finished_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_running_process(self):
        """Test that a running process cannot be edited."""
        response = self.admin_client.get(self.edit_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_edit_admin_user_success(self):
        """User with can_edit_process permission can edit a process."""
        data = {
            "name": "UPDATED PROCESS",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.admin_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "UPDATED PROCESS")

    def test_post_edit_user_scope_user_own_process_success(self):
        """User with can_edit_process permission and SCOPE_USER can edit their own process."""
        data = {
            "name": "UPDATED USER PROCESS",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.user_scope_client.post(self.edit_user_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was updated
        self.user_process.refresh_from_db()
        self.assertEqual(self.user_process.name, "UPDATED USER PROCESS")

    def test_post_edit_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot edit
        other users' processes."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.user_scope_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "ADMIN PROCESS")

    def test_post_edit_admin_user_failure(self):
        """User with can_edit_process permission gets form errors on invalid data."""
        data = {
            "name": "",  # Empty name should fail validation
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.admin_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertContains(response, "invalid-feedback")  # Check for validation error class

        # Verify process was not updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "ADMIN PROCESS")

    def test_post_edit_list_only_user_forbidden(self):
        """User with only list permission cannot edit a process."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.list_only_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "ADMIN PROCESS")

    def test_post_edit_no_perm_user_forbidden(self):
        """User with no permissions cannot edit a process."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.no_perm_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "ADMIN PROCESS")

    def test_post_edit_anonymous_user_redirect(self):
        """Test that an anonymous user cannot edit a process."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.anonymous_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify process was not updated
        self.admin_process.refresh_from_db()
        self.assertEqual(self.admin_process.name, "ADMIN PROCESS")

    def test_post_edit_finished_process_forbidden(self):
        """Test that a finished process cannot be edited."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.admin_client.post(self.edit_finished_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not updated
        self.finished_process.refresh_from_db()
        self.assertEqual(self.finished_process.name, "FINISHED PROCESS")

    def test_post_edit_running_process_forbidden(self):
        """Test that a running process cannot be edited."""
        data = {
            "name": "SHOULD NOT BE UPDATED",
            "wordlist": self.test_wordlist.pk,
            "typifications": [self.test_typification.pk],
        }
        response = self.admin_client.post(self.edit_running_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not updated
        self.running_process.refresh_from_db()
        self.assertEqual(self.running_process.name, "RUNNING PROCESS")

    def test_delete_edit_bad_request(self):
        """Test that DELETE method is not allowed for edit."""
        response = self.admin_client.delete(self.edit_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessDeleteViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_DELETE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.delete_url = reverse("analytics:process:delete", args=[self.admin_process.pk])
        self.delete_user_url = reverse("analytics:process:delete", args=[self.user_process.pk])
        self.delete_running_url = reverse(
            "analytics:process:delete", args=[self.running_process.pk]
        )

    def test_delete_admin_user_success(self):
        """User with can_delete_process permission can delete a process."""
        response = self.admin_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was soft-deleted
        self.admin_process.refresh_from_db()
        self.assertFalse(self.admin_process.is_active)

        # Verify related audios were also soft-deleted
        self.admin_audio.refresh_from_db()
        self.assertFalse(self.admin_audio.is_active)

    def test_delete_user_scope_user_own_process_success(self):
        """User with can_delete_process permission and SCOPE_USER can delete their own process."""
        response = self.user_scope_client.delete(self.delete_user_url)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was soft-deleted
        self.user_process.refresh_from_db()
        self.assertFalse(self.user_process.is_active)

    def test_delete_user_scope_user_other_process_forbidden(self):
        """User with can_delete_process permission and SCOPE_USER cannot delete
        other users' processes."""
        response = self.user_scope_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not deleted
        self.admin_process.refresh_from_db()
        self.assertTrue(self.admin_process.is_active)

    def test_delete_list_only_user_forbidden(self):
        """User with only list permission cannot delete a process."""
        response = self.list_only_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not deleted
        self.admin_process.refresh_from_db()
        self.assertTrue(self.admin_process.is_active)

    def test_delete_no_perm_user_forbidden(self):
        """User with no permissions cannot delete a process."""
        response = self.no_perm_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not deleted
        self.admin_process.refresh_from_db()
        self.assertTrue(self.admin_process.is_active)

    def test_delete_anonymous_user_redirect(self):
        """Test that an anonymous user cannot delete a process."""
        response = self.anonymous_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify process was not deleted
        self.admin_process.refresh_from_db()
        self.assertTrue(self.admin_process.is_active)

    def test_delete_running_process_forbidden(self):
        """Test that a running process cannot be deleted."""
        response = self.admin_client.delete(self.delete_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not deleted
        self.running_process.refresh_from_db()
        self.assertTrue(self.running_process.is_active)

    def test_get_delete_bad_request(self):
        """Test that GET method is not allowed for delete."""
        response = self.admin_client.get(self.delete_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_post_delete_bad_request(self):
        """Test that POST method is not allowed for delete."""
        response = self.admin_client.post(self.delete_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessReactivateViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_REACTIVATE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.reactivate_url = reverse(
            "analytics:process:reactivate", args=[self.deleted_process.pk]
        )

    def test_post_reactivate_admin_user_own_process_success(self):
        """User with can_delete_process permission can reactivate a process."""
        response = self.admin_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify process was reactivated
        self.deleted_process.refresh_from_db()
        self.assertTrue(self.deleted_process.is_active)

        # Verify related audios were also reactivated
        self.deleted_audio_deleted_process.refresh_from_db()
        self.assertTrue(self.deleted_audio_deleted_process.is_active)

    def test_post_reactivate_user_scope_user_other_process_forbidden_process(self):
        """User with can_delete_process permission and SCOPE_USER cannot reactivate
        other users' processes."""
        response = self.user_scope_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not reactivated
        self.deleted_process.refresh_from_db()
        self.assertFalse(self.deleted_process.is_active)

        # Verify related audios were also reactivated
        self.deleted_audio_deleted_process.refresh_from_db()
        self.assertFalse(self.deleted_audio_deleted_process.is_active)

    def test_post_reactivate_list_only_user_forbidden(self):
        """User with only list permission cannot reactivate a process."""
        response = self.list_only_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not reactivated
        self.deleted_process.refresh_from_db()
        self.assertFalse(self.deleted_process.is_active)

    def test_post_reactivate_no_perm_user_forbidden(self):
        """User with no permissions cannot reactivate a process."""
        response = self.no_perm_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify process was not reactivated
        self.deleted_process.refresh_from_db()
        self.assertFalse(self.deleted_process.is_active)

    def test_post_reactivate_anonymous_user_redirect(self):
        """Test that an anonymous user cannot reactivate a process."""
        response = self.anonymous_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify process was not reactivated
        self.deleted_process.refresh_from_db()
        self.assertFalse(self.deleted_process.is_active)

    def test_get_reactivate_bad_request(self):
        """Test that GET method is not allowed for reactivate."""
        response = self.admin_client.get(self.reactivate_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_reactivate_bad_request(self):
        """Test that DELETE method is not allowed for reactivate."""
        response = self.admin_client.delete(self.reactivate_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessReadViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_READ action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.read_url = reverse("analytics:process:read", args=[self.admin_process.pk])
        self.read_user_url = reverse("analytics:process:read", args=[self.user_process.pk])
        self.read_finished_url = reverse("analytics:process:read", args=[self.finished_process.pk])

    def test_get_read_admin_user(self):
        """User with can_list_process permission can access the read view."""
        response = self.admin_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_process.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_get_read_user_scope_user_own_process(self):
        """User with can_list_process permission and SCOPE_USER can access the read view
        for their own process."""
        response = self.user_scope_client.get(self.read_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_process.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_get_read_user_scope_user_other_process_forbidden(self):
        """User with can_list_process permission and SCOPE_USER cannot access the read view
        for other users' processes."""
        response = self.user_scope_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_list_only_user(self):
        """User with only list permission can access the read view."""
        response = self.list_only_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_process.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_get_read_no_perm_user_forbidden(self):
        """User with no permissions cannot access the read view."""
        response = self.no_perm_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the read view."""
        response = self.anonymous_client.get(self.read_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_read_finished_process(self):
        """Test that a finished process can be read."""
        response = self.admin_client.get(self.read_finished_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.finished_process.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_post_read_bad_request(self):
        """Test that POST method is not allowed for read."""
        response = self.admin_client.post(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_read_bad_request(self):
        """Test that DELETE method is not allowed for read."""
        response = self.admin_client.delete(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessHistoryViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_HISTORY action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.history_url = reverse("analytics:process:history", args=[self.admin_process.pk])
        self.history_user_url = reverse("analytics:process:history", args=[self.user_process.pk])
        self.history_deleted_url = reverse(
            "analytics:process:history", args=[self.deleted_process.pk]
        )

    def test_get_history_admin_user(self):
        """User with can_history_process permission can access the history view."""
        response = self.admin_client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_get_history_user_scope_user_own_process(self):
        """User with can_history_process permission and SCOPE_USER can access the history view
        for their own process."""
        response = self.user_scope_client.get(self.history_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_get_history_user_scope_user_other_process_forbidden(self):
        """User with can_history_process permission and SCOPE_USER cannot access the history view
        for other users' processes."""
        response = self.user_scope_client.get(self.history_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_history_list_only_user(self):
        """User with only list permission can access the history view."""
        response = self.list_only_client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_get_history_no_perm_user_forbidden(self):
        """User with no permissions cannot access the history view."""
        response = self.no_perm_client.get(self.history_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_history_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the history view."""
        response = self.anonymous_client.get(self.history_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_history_deleted_process(self):
        """Test that a deleted process can be viewed in history."""
        response = self.admin_client.get(self.history_deleted_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_post_history_bad_request(self):
        """Test that POST method is not allowed for history."""
        response = self.admin_client.post(self.history_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_history_bad_request(self):
        """Test that DELETE method is not allowed for history."""
        response = self.admin_client.delete(self.history_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessListViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_LIST action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.list_url = reverse("analytics:process:list")

    def test_get_list_admin_user(self):
        """User with can_list_process permission can access the list view."""
        response = self.admin_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the admin process
        self.assertContains(response, self.admin_process.name)
        # Check that the table contains the user process
        self.assertContains(response, self.user_process.name)
        # Check that the table contains the deleted process
        self.assertContains(response, self.deleted_process.name)

    def test_get_list_user_scope_user(self):
        """User with can_list_process permission and SCOPE_USER can access the list view
        but only see their own processes."""
        response = self.user_scope_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the user process
        self.assertContains(response, self.user_process.name)
        # Check that the table does not contain the admin process
        self.assertNotContains(response, self.admin_process.name)

    def test_get_list_list_only_user(self):
        """User with only list permission can access the list view."""
        response = self.list_only_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the admin process
        self.assertContains(response, self.admin_process.name)
        # Check that the table contains the user process
        self.assertContains(response, self.user_process.name)
        # Check that the table contains the deleted process
        self.assertContains(response, self.deleted_process.name)

    def test_get_list_no_perm_user_forbidden(self):
        """User with no permissions cannot access the list view."""
        response = self.no_perm_client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_list_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the list view."""
        response = self.anonymous_client.get(self.list_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_list_bad_request(self):
        """Test that POST method is not allowed for list."""
        response = self.admin_client.post(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_list_bad_request(self):
        """Test that DELETE method is not allowed for list."""
        response = self.admin_client.delete(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessStartViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_START action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.start_url = reverse("analytics:process:start", args=[self.admin_process.pk])
        self.start_user_url = reverse("analytics:process:start", args=[self.user_process.pk])
        self.start_running_url = reverse("analytics:process:start", args=[self.running_process.pk])
        self.start_finished_url = reverse(
            "analytics:process:start", args=[self.finished_process.pk]
        )

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_start_admin_user_success(self, mock_launch_task):
        """User with can_edit_process permission can start a process."""
        response = self.admin_client.post(self.start_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_launch_task.assert_called_once()

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_start_user_scope_user_own_process_success(self, mock_launch_task):
        """User with can_edit_process permission and SCOPE_USER can start their own process."""
        response = self.user_scope_client.post(self.start_user_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_launch_task.assert_called_once()

    def test_post_start_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot start other
        users' processes."""
        response = self.user_scope_client.post(self.start_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_start_list_only_user_forbidden(self):
        """User with only list permission cannot start a process."""
        response = self.list_only_client.post(self.start_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_start_no_perm_user_forbidden(self):
        """User with no permissions cannot start a process."""
        response = self.no_perm_client.post(self.start_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_start_anonymous_user_redirect(self):
        """Test that an anonymous user cannot start a process."""
        response = self.anonymous_client.post(self.start_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_start_running_process_failure(self, mock_launch_task):
        """Test that a running process cannot be started again."""
        response = self.admin_client.post(self.start_running_url)
        self.assertEqual(response.status_code, 403)
        mock_launch_task.assert_not_called()

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_start_finished_process_failure(self, mock_launch_task):
        """Test that a finished process cannot be started again."""
        response = self.admin_client.post(self.start_finished_url)
        self.assertEqual(response.status_code, 403)
        mock_launch_task.assert_not_called()

    def test_get_start_bad_request(self):
        """Test that GET method is not allowed for start."""
        response = self.admin_client.get(self.start_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_start_bad_request(self):
        """Test that DELETE method is not allowed for start."""
        response = self.admin_client.delete(self.start_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessContinueViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_CONTINUE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.continue_url = reverse("analytics:process:continue", args=[self.stopped_process.pk])
        self.continue_user_url = reverse("analytics:process:continue", args=[self.user_process.pk])
        self.continue_running_url = reverse(
            "analytics:process:continue", args=[self.running_process.pk]
        )
        self.continue_finished_url = reverse(
            "analytics:process:continue", args=[self.finished_process.pk]
        )

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_continue_admin_user_success(self, mock_launch_task):
        """User with can_edit_process permission can continue a stopped process."""
        response = self.admin_client.post(self.continue_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_launch_task.assert_called_once()

    def test_post_continue_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot continue other
        users' processes."""
        response = self.user_scope_client.post(self.continue_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_continue_list_only_user_forbidden(self):
        """User with only list permission cannot continue a process."""
        response = self.list_only_client.post(self.continue_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_continue_no_perm_user_forbidden(self):
        """User with no permissions cannot continue a process."""
        response = self.no_perm_client.post(self.continue_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_continue_anonymous_user_redirect(self):
        """Test that an anonymous user cannot continue a process."""
        response = self.anonymous_client.post(self.continue_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_continue_running_process_failure(self, mock_launch_task):
        """Test that a running process cannot be continued."""
        response = self.admin_client.post(self.continue_running_url)
        self.assertEqual(response.status_code, 403)
        mock_launch_task.assert_not_called()

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_continue_finished_process_failure(self, mock_launch_task):
        """Test that a finished process cannot be continued."""
        response = self.admin_client.post(self.continue_finished_url)
        self.assertEqual(response.status_code, 403)
        mock_launch_task.assert_not_called()

    def test_get_continue_bad_request(self):
        """Test that GET method is not allowed for continue."""
        response = self.admin_client.get(self.continue_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_continue_bad_request(self):
        """Test that DELETE method is not allowed for continue."""
        response = self.admin_client.delete(self.continue_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessPauseViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_PAUSE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.pause_url = reverse("analytics:process:pause", args=[self.running_process.pk])
        self.pause_user_url = reverse("analytics:process:pause", args=[self.user_process.pk])
        self.pause_stopped_url = reverse("analytics:process:pause", args=[self.stopped_process.pk])
        self.pause_finished_url = reverse(
            "analytics:process:pause", args=[self.finished_process.pk]
        )

    @patch("apps.analytics.control.Control.set_pause_process")
    def test_post_pause_admin_user_success(self, mock_pause):
        """User with can_edit_process permission can pause a running process."""
        response = self.admin_client.post(self.pause_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_pause.assert_called_once()

    def test_post_pause_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot pause other
        users' processes."""
        response = self.user_scope_client.post(self.pause_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_pause_list_only_user_forbidden(self):
        """User with only list permission cannot pause a process."""
        response = self.list_only_client.post(self.pause_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_pause_no_perm_user_forbidden(self):
        """User with no permissions cannot pause a process."""
        response = self.no_perm_client.post(self.pause_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_pause_anonymous_user_redirect(self):
        """Test that an anonymous user cannot pause a process."""
        response = self.anonymous_client.post(self.pause_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_pause_stopped_process_success(self):
        """A stopped process can be paused (unlike a finished one)."""
        response = self.admin_client.post(self.pause_stopped_url)
        self.assertEqual(response.status_code, 204)

    def test_post_pause_finished_process_failure(self):
        """Test that a finished process cannot be paused."""
        response = self.admin_client.post(self.pause_finished_url)
        self.assertEqual(response.status_code, 403)

    def test_get_pause_bad_request(self):
        """Test that GET method is not allowed for pause."""
        response = self.admin_client.get(self.pause_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_pause_bad_request(self):
        """Test that DELETE method is not allowed for pause."""
        response = self.admin_client.delete(self.pause_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessRestartViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_RESTART action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.restart_full_url = reverse(
            "analytics:process:restart", args=[self.finished_process.pk, RESTART_EXTRA_FULL]
        )
        self.restart_partial_url = reverse(
            "analytics:process:restart", args=[self.finished_process.pk, RESTART_EXTRA_PARTIAL]
        )
        self.restart_user_url = reverse(
            "analytics:process:restart", args=[self.user_process.pk, RESTART_EXTRA_FULL]
        )
        self.restart_running_url = reverse(
            "analytics:process:restart", args=[self.running_process.pk, RESTART_EXTRA_FULL]
        )
        self.restart_invalid_url = reverse(
            "analytics:process:restart", args=[self.finished_process.pk, 999]
        )  # Invalid extra_id

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_restart_full_admin_user_success(self, mock_launch_task):
        """User with can_edit_process permission can fully restart a process."""
        response = self.admin_client.post(self.restart_full_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_launch_task.assert_called_once()

        # Verify process state was reset to READY
        self.finished_process.refresh_from_db()
        self.assertEqual(self.finished_process.state, PROCESS_STATE_READY)

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_restart_partial_admin_user_success(self, mock_launch_task):
        """User with can_edit_process permission can partially restart a process."""
        response = self.admin_client.post(self.restart_partial_url)
        self.assertEqual(response.status_code, 204)  # Success response
        mock_launch_task.assert_called_once()

        # Verify process state was reset to TRANSCRIBED
        self.finished_process.refresh_from_db()
        self.assertEqual(self.finished_process.state, PROCESS_STATE_TRANSCRIBED)

    def test_post_restart_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot restart other
        users' processes."""
        response = self.user_scope_client.post(self.restart_full_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_restart_list_only_user_forbidden(self):
        """User with only list permission cannot restart a process."""
        response = self.list_only_client.post(self.restart_full_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_restart_no_perm_user_forbidden(self):
        """User with no permissions cannot restart a process."""
        response = self.no_perm_client.post(self.restart_full_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_restart_anonymous_user_redirect(self):
        """Test that an anonymous user cannot restart a process."""
        response = self.anonymous_client.post(self.restart_full_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_restart_running_process_failure(self, mock_launch_task):
        """Test that a running process cannot be restarted."""
        response = self.admin_client.post(self.restart_running_url)
        self.assertEqual(response.status_code, 403)  # Success response with failed event
        mock_launch_task.assert_not_called()

    @patch("apps.analytics.tasks.launch_analyzer_task.delay")
    def test_post_restart_invalid_extra_id(self, mock_launch_task):
        """Test that an invalid extra_id results in a failure."""
        response = self.admin_client.post(self.restart_invalid_url)
        self.assertEqual(response.status_code, 204)  # Success response with failed event
        mock_launch_task.assert_not_called()

    def test_get_restart_bad_request(self):
        """Test that GET method is not allowed for restart."""
        response = self.admin_client.get(self.restart_full_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_restart_bad_request(self):
        """Test that DELETE method is not allowed for restart."""
        response = self.admin_client.delete(self.restart_full_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class ProcessMainViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Process views with API_ACTION_MAIN action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.main_url = reverse("analytics:process:main")
        self.main_with_process_url = f"{self.main_url}?selected_process={self.admin_process.pk}"
        self.main_with_user_process_url = f"{self.main_url}?selected_process={self.user_process.pk}"
        self.main_with_invalid_process_url = f"{self.main_url}?selected_process=999999"

    def test_get_main_admin_user(self):
        """User with can_edit_process permission can access the main view."""
        response = self.admin_client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Añadir")  # Check for "Add" button

    def test_get_main_with_process_admin_user(self):
        """User with can_edit_process permission can access the main view with a selected
        process."""
        response = self.admin_client.get(self.main_with_process_url)
        self.assertEqual(response.status_code, 200)
        # Check for appropriate action button based on process state
        if self.admin_process.is_ready:
            self.assertContains(response, "Procesar")  # "Process" button
        elif self.admin_process.is_running:
            self.assertContains(response, "Pausar")  # "Pause" button

    def test_get_main_with_invalid_process_admin_user(self):
        """User with can_edit_process permission gets default button with invalid process ID."""
        response = self.admin_client.get(self.main_with_invalid_process_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Añadir")  # Default "Add" button

    def test_get_main_user_scope_user_own_process(self):
        """User with can_edit_process permission and SCOPE_USER can access the main view
        for their own process."""
        response = self.user_scope_client.get(self.main_with_user_process_url)
        self.assertEqual(response.status_code, 200)
        # Check for appropriate action button based on process state
        if self.user_process.is_ready:
            self.assertContains(response, "Procesar")  # "Process" button

    def test_get_main_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot access the main view
        for other users' processes."""
        response = self.user_scope_client.get(self.main_with_process_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_main_list_only_user_forbidden(self):
        """User with only list permission can not access the main view."""
        response = self.list_only_client.get(self.main_url)
        self.assertEqual(response.status_code, 403)

    def test_get_main_no_perm_user_forbidden(self):
        """User with no permissions cannot access the main view."""
        response = self.no_perm_client.get(self.main_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_main_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the main view."""
        response = self.anonymous_client.get(self.main_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_main_bad_request(self):
        """Test that POST method is not allowed for main."""
        response = self.admin_client.post(self.main_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_main_bad_request(self):
        """Test that DELETE method is not allowed for main."""
        response = self.admin_client.delete(self.main_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedAddViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_ADD action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.add_url = reverse("analytics:process:audio:add", args=[self.admin_process.pk])
        self.add_user_url = reverse("analytics:process:audio:add", args=[self.user_process.pk])
        self.add_running_url = reverse(
            "analytics:process:audio:add", args=[self.running_process.pk]
        )
        self.add_finished_url = reverse(
            "analytics:process:audio:add", args=[self.finished_process.pk]
        )

    def test_get_add_admin_user(self):
        """User with can_add_process permission can access the add form for audio."""
        response = self.admin_client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, "file")  # Check for file upload field

    def test_get_add_user_scope_user_own_process(self):
        """User with can_add_process permission and SCOPE_USER can access the add form for audio
        in their own process."""
        response = self.user_scope_client.get(self.add_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_get_add_user_scope_user_other_process_forbidden(self):
        """User with can_add_process permission and SCOPE_USER cannot access the add form for
        audio in other users' processes."""
        response = self.user_scope_client.get(self.add_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_list_only_user(self):
        """User with only list permission cannot access the add form for audio."""
        response = self.list_only_client.get(self.add_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_no_perm_user(self):
        """User with no permissions cannot access the add form for audio."""
        response = self.no_perm_client.get(self.add_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_anonymous_user(self):
        """Test that an anonymous user cannot access the add form for audio."""
        response = self.anonymous_client.get(self.add_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_add_running_process(self):
        """Test that audio cannot be added to a running process."""
        response = self.admin_client.get(self.add_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_add_finished_process(self):
        """Test that audio cannot be added to a finished process."""
        response = self.admin_client.get(self.add_finished_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_add_admin_user_success(self):
        """User with can_add_process permission can add a new audio to a process."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audio was created
        self.assertTrue(
            Audio.objects.filter(
                process=self.admin_process, original_filename="demo_reducido.mp3"
            ).exists()
        )

    def test_post_add_admin_user_no_file_is_noop(self):
        """Submitting the audio-add form without a file is accepted (files are optional)
        and creates no new audio."""
        before = Audio.objects.filter(process=self.admin_process).count()
        data = {"agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.admin_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 204)  # Accepted, no-op
        self.assertEqual(Audio.objects.filter(process=self.admin_process).count(), before)

    def test_post_add_user_scope_user_own_process_success(self):
        """User with can_add_process permission and SCOPE_USER can add a new audio to
        their own process."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.user_scope_client.post(self.add_user_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audio was created
        self.assertTrue(
            Audio.objects.filter(
                process=self.user_process, original_filename="demo_reducido.mp3"
            ).exists()
        )

    def test_post_add_user_scope_user_other_process_forbidden(self):
        """User with can_add_process permission and SCOPE_USER cannot add audio to
        other users' processes."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.user_scope_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_add_list_only_user_forbidden(self):
        """User with only list permission cannot add a new audio."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.list_only_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_add_no_perm_user_forbidden(self):
        """User with no permissions cannot add a new audio."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.no_perm_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_add_anonymous_user_redirect(self):
        """Test that an anonymous user cannot add a new audio."""
        data = {"file": self.real_mp3_file, "agent": self.test_agent.pk, "agent_date": "2023-01-01"}
        response = self.anonymous_client.post(self.add_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_delete_add_bad_request(self):
        """Test that DELETE method is not allowed for add."""
        response = self.admin_client.delete(self.add_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedEditViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_EDIT action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.edit_url = reverse(
            "analytics:process:audio:edit", args=[self.admin_process.pk, self.admin_audio.pk]
        )
        self.edit_user_url = reverse(
            "analytics:process:audio:edit", args=[self.user_process.pk, self.user_audio.pk]
        )
        self.edit_running_url = reverse(
            "analytics:process:audio:edit", args=[self.running_process.pk, self.admin_audio.pk]
        )
        self.edit_finished_url = reverse(
            "analytics:process:audio:edit", args=[self.finished_process.pk, self.admin_audio.pk]
        )
        self.edit_deleted_url = reverse(
            "analytics:process:audio:edit", args=[self.admin_process.pk, self.deleted_audio.pk]
        )

    def test_get_edit_admin_user(self):
        """User with can_edit_process permission can access the edit form for audio."""
        response = self.admin_client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertNotContains(response, "file")  # Check that file field is not present

    def test_get_edit_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot access the edit form
        for audio in other users' processes."""
        response = self.user_scope_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_list_only_user(self):
        """User with only list permission cannot access the edit form for audio."""
        response = self.list_only_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_no_perm_user(self):
        """User with no permissions cannot access the edit form for audio."""
        response = self.no_perm_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_anonymous_user(self):
        """Test that an anonymous user cannot access the edit form for audio."""
        response = self.anonymous_client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_edit_running_process(self):
        """Test that audio cannot be edited in a running process."""
        response = self.admin_client.get(self.edit_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_finished_process(self):
        """Test that audio cannot be edited in a finished process."""
        response = self.admin_client.get(self.edit_finished_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_deleted_audio(self):
        """Test that a deleted audio cannot be edited."""
        response = self.admin_client.get(self.edit_deleted_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_edit_admin_user_success(self):
        """User with can_edit_process permission can edit an audio."""
        data = {"agent": self.test_agent.pk, "agent_date": "2023-02-01"}  # Changed date
        response = self.admin_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audio was updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-02-01")

    def test_post_edit_admin_user_failure_missing_agent(self):
        """User with can_edit_process permission gets form errors when missing agent."""
        data = {"agent_date": "2023-02-01"}
        response = self.admin_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 200)  # Form with errors
        self.assertContains(response, "invalid-feedback")  # Check for validation error class

        # Verify audio was not updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-01-01")

    def test_post_edit_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot edit audio in
        other users' processes."""
        data = {"agent": self.test_agent.pk, "agent_date": "2023-02-01"}
        response = self.user_scope_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-01-01")

    def test_post_edit_list_only_user_forbidden(self):
        """User with only list permission cannot edit an audio."""
        data = {"agent": self.test_agent.pk, "agent_date": "2023-02-01"}
        response = self.list_only_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-01-01")

    def test_post_edit_no_perm_user_forbidden(self):
        """User with no permissions cannot edit an audio."""
        data = {"agent": self.test_agent.pk, "agent_date": "2023-02-01"}
        response = self.no_perm_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-01-01")

    def test_post_edit_anonymous_user_redirect(self):
        """Test that an anonymous user cannot edit an audio."""
        data = {"agent": self.test_agent.pk, "agent_date": "2023-02-01"}
        response = self.anonymous_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify audio was not updated
        self.admin_audio.refresh_from_db()
        self.assertEqual(str(self.admin_audio.agent_date), "2023-01-01")

    def test_delete_edit_bad_request(self):
        """Test that DELETE method is not allowed for edit."""
        response = self.admin_client.delete(self.edit_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedDeleteViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_DELETE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.delete_url = reverse(
            "analytics:process:audio:delete", args=[self.admin_process.pk, self.admin_audio.pk]
        )
        self.delete_user_url = reverse(
            "analytics:process:audio:delete", args=[self.user_process.pk, self.user_audio.pk]
        )
        self.delete_running_url = reverse(
            "analytics:process:audio:delete", args=[self.running_process.pk, self.admin_audio.pk]
        )
        self.delete_deleted_url = reverse(
            "analytics:process:audio:delete", args=[self.admin_process.pk, self.deleted_audio.pk]
        )

    def test_delete_admin_user_success(self):
        """User with can_delete_process permission can delete an audio."""
        response = self.admin_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audio was soft-deleted
        self.admin_audio.refresh_from_db()
        self.assertFalse(self.admin_audio.is_active)

    def test_delete_user_scope_user_other_process_forbidden(self):
        """User with can_delete_process permission and SCOPE_USER cannot delete audio in
        other users' processes."""
        response = self.user_scope_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not deleted
        self.admin_audio.refresh_from_db()
        self.assertTrue(self.admin_audio.is_active)

    def test_delete_list_only_user_forbidden(self):
        """User with only list permission cannot delete an audio."""
        response = self.list_only_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not deleted
        self.admin_audio.refresh_from_db()
        self.assertTrue(self.admin_audio.is_active)

    def test_delete_no_perm_user_forbidden(self):
        """User with no permissions cannot delete an audio."""
        response = self.no_perm_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not deleted
        self.admin_audio.refresh_from_db()
        self.assertTrue(self.admin_audio.is_active)

    def test_delete_anonymous_user_redirect(self):
        """Test that an anonymous user cannot delete an audio."""
        response = self.anonymous_client.delete(self.delete_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify audio was not deleted
        self.admin_audio.refresh_from_db()
        self.assertTrue(self.admin_audio.is_active)

    def test_delete_running_process(self):
        """Test that audio cannot be deleted in a running process."""
        response = self.admin_client.delete(self.delete_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_delete_bad_request(self):
        """Test that GET method is not allowed for delete."""
        response = self.admin_client.get(self.delete_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_post_delete_bad_request(self):
        """Test that POST method is not allowed for delete."""
        response = self.admin_client.post(self.delete_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedReactivateViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_REACTIVATE action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.reactivate_url = reverse(
            "analytics:process:audio:reactivate",
            args=[self.admin_process.pk, self.deleted_audio.pk],
        )
        self.reactivate_user_url = reverse(
            "analytics:process:audio:reactivate", args=[self.user_process.pk, self.deleted_audio.pk]
        )
        self.reactivate_running_url = reverse(
            "analytics:process:audio:reactivate",
            args=[self.running_process.pk, self.deleted_audio.pk],
        )
        self.reactivate_finished_url = reverse(
            "analytics:process:audio:reactivate",
            args=[self.finished_process.pk, self.deleted_audio.pk],
        )
        self.reactivate_active_url = reverse(
            "analytics:process:audio:reactivate", args=[self.admin_process.pk, self.admin_audio.pk]
        )

    def test_post_reactivate_admin_user_success(self):
        """User with can_delete_process permission can reactivate an audio."""
        response = self.admin_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audio was reactivated
        self.deleted_audio.refresh_from_db()
        self.assertTrue(self.deleted_audio.is_active)

    def test_post_reactivate_user_scope_user_other_process_forbidden(self):
        """User with can_delete_process permission and SCOPE_USER cannot reactivate audio
        in other users' processes."""
        response = self.user_scope_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not reactivated
        self.deleted_audio.refresh_from_db()
        self.assertFalse(self.deleted_audio.is_active)

    def test_post_reactivate_list_only_user_forbidden(self):
        """User with only list permission cannot reactivate an audio."""
        response = self.list_only_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not reactivated
        self.deleted_audio.refresh_from_db()
        self.assertFalse(self.deleted_audio.is_active)

    def test_post_reactivate_no_perm_user_forbidden(self):
        """User with no permissions cannot reactivate an audio."""
        response = self.no_perm_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audio was not reactivated
        self.deleted_audio.refresh_from_db()
        self.assertFalse(self.deleted_audio.is_active)

    def test_post_reactivate_anonymous_user_redirect(self):
        """Test that an anonymous user cannot reactivate an audio."""
        response = self.anonymous_client.post(self.reactivate_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify audio was not reactivated
        self.deleted_audio.refresh_from_db()
        self.assertFalse(self.deleted_audio.is_active)

    def test_post_reactivate_running_process(self):
        """Test that audio cannot be reactivated in a running process."""
        response = self.admin_client.post(self.reactivate_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_reactivate_finished_process(self):
        """Test that audio cannot be reactivated in a finished process."""
        response = self.admin_client.post(self.reactivate_finished_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_reactivate_bad_request(self):
        """Test that GET method is not allowed for reactivate."""
        response = self.admin_client.get(self.reactivate_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_reactivate_bad_request(self):
        """Test that DELETE method is not allowed for reactivate."""
        response = self.admin_client.delete(self.reactivate_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedReadViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_READ action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.read_url = reverse(
            "analytics:process:audio:read", args=[self.admin_process.pk, self.admin_audio.pk]
        )
        self.read_user_url = reverse(
            "analytics:process:audio:read", args=[self.user_process.pk, self.user_audio.pk]
        )
        self.read_deleted_url = reverse(
            "analytics:process:audio:read", args=[self.admin_process.pk, self.deleted_audio.pk]
        )

    def test_get_read_admin_user(self):
        """User with can_list_process permission can access the read view for audio."""
        response = self.admin_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_audio.agent.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_get_read_user_scope_user_other_process_forbidden(self):
        """User with can_list_process permission and SCOPE_USER cannot access the read view for
        audio in other users' processes."""
        response = self.user_scope_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_list_only_user(self):
        """User with only list permission can access the read view for audio."""
        response = self.list_only_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_audio.agent.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_get_read_no_perm_user_forbidden(self):
        """User with no permissions cannot access the read view for audio."""
        response = self.no_perm_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the read view for audio."""
        response = self.anonymous_client.get(self.read_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_read_deleted_audio(self):
        """Test that a deleted audio can be viewed in read mode."""
        response = self.admin_client.get(self.read_deleted_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.deleted_audio.agent.name)
        # Check that the form is read-only (no submit button)
        self.assertContains(response, "disabled")

    def test_post_read_bad_request(self):
        """Test that POST method is not allowed for read."""
        response = self.admin_client.post(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_read_bad_request(self):
        """Test that DELETE method is not allowed for read."""
        response = self.admin_client.delete(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedHistoryViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_HISTORY action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.history_url = reverse(
            "analytics:process:audio:history", args=[self.admin_process.pk, self.admin_audio.pk]
        )
        self.history_user_url = reverse(
            "analytics:process:audio:history", args=[self.user_process.pk, self.user_audio.pk]
        )
        self.history_deleted_url = reverse(
            "analytics:process:audio:history", args=[self.admin_process.pk, self.deleted_audio.pk]
        )

    def test_get_history_admin_user(self):
        """User with can_history_process permission can access the history view for audio."""
        response = self.admin_client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_get_history_user_scope_user_other_process_forbidden(self):
        """User with can_history_process permission and SCOPE_USER cannot access the history view
        for audio in other users' processes."""
        response = self.user_scope_client.get(self.history_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_history_list_only_user(self):
        """User with only list permission can access the history view for audio."""
        response = self.list_only_client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_get_history_no_perm_user_forbidden(self):
        """User with no permissions cannot access the history view for audio."""
        response = self.no_perm_client.get(self.history_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_history_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the history view for audio."""
        response = self.anonymous_client.get(self.history_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_history_deleted_audio(self):
        """Test that a deleted audio can be viewed in history."""
        response = self.admin_client.get(self.history_deleted_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "accordion")  # Check for accordion component

    def test_post_history_bad_request(self):
        """Test that POST method is not allowed for history."""
        response = self.admin_client.post(self.history_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_history_bad_request(self):
        """Test that DELETE method is not allowed for history."""
        response = self.admin_client.delete(self.history_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioRelatedListViewTestCase(ProcessViewsBaseTestCase):
    """Test case for the Audio related views with API_ACTION_LIST action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.list_url = reverse("analytics:process:audio:list", args=[self.admin_process.pk])
        self.list_user_url = reverse("analytics:process:audio:list", args=[self.user_process.pk])

    def test_get_list_admin_user(self):
        """User with can_list_process permission can access the list view for audio."""
        response = self.admin_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the active audio
        self.assertContains(response, self.admin_audio.original_filename)
        # Check that the table contains the deleted audio
        self.assertContains(response, self.deleted_audio.original_filename)

    def test_get_list_user_scope_user_own_process(self):
        """User with can_list_process permission and SCOPE_USER can access the list view
        for audio in their own process."""
        response = self.user_scope_client.get(self.list_user_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the user audio
        self.assertContains(response, self.user_audio.original_filename)

    def test_get_list_user_scope_user_other_process_forbidden(self):
        """User with can_list_process permission and SCOPE_USER cannot access the list view
        for audio in other users' processes."""
        response = self.user_scope_client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_list_list_only_user(self):
        """User with only list permission can access the list view for audio."""
        response = self.list_only_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Check that the table contains the active audio
        self.assertContains(response, self.admin_audio.original_filename)
        # Check that the table contains the deleted audio
        self.assertContains(response, self.deleted_audio.original_filename)

    def test_get_list_no_perm_user_forbidden(self):
        """User with no permissions cannot access the list view for audio."""
        response = self.no_perm_client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_list_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the list view for audio."""
        response = self.anonymous_client.get(self.list_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_list_bad_request(self):
        """Test that POST method is not allowed for list."""
        response = self.admin_client.post(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_list_bad_request(self):
        """Test that DELETE method is not allowed for list."""
        response = self.admin_client.delete(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method
