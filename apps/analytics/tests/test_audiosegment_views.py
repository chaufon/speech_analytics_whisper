import os

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.analytics.models import Agent, Audio, AudioSegment, Process, Typification, WordList
from apps.common.constants import (
    PROCESS_STATE_FINISHED,
    PROCESS_STATE_READY,
    SCOPE_CAMPAIGN,
    SCOPE_NONE,
    SCOPE_USER,
)
from apps.users.models import Campaign, Role, User


class AudioSegmentViewsBaseTestCase(TestCase):
    """Base test case for AudioSegment views with various API actions."""

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

        # Load real test files
        self.mp3_path = os.path.join(
            os.path.dirname(__file__), "audios_for_testing", "demo_reducido.mp3"
        )

        with open(self.mp3_path, "rb") as f:
            self.real_mp3_content = f.read()

        self.admin_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.user_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.running_audio_mp3_file = SimpleUploadedFile(
            "demo_reducido.mp3", self.real_mp3_content, content_type="audio/mpeg"
        )
        self.finished_audio_mp3_file = SimpleUploadedFile(
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

        # Create a test audio for the running process
        self.running_audio = Audio.objects.create(
            file=self.running_audio_mp3_file,
            original_filename="running_test.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.running_process,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create a test audio for the finished process
        self.finished_audio = Audio.objects.create(
            file=self.finished_audio_mp3_file,
            original_filename="finished_test.mp3",
            agent=self.test_agent,
            agent_date="2023-01-01",
            process=self.finished_process,
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
            is_active=True,
        )

        # Create AudioSegment objects for each audio
        self.admin_audiosegment = AudioSegment.objects.create(
            audio=self.admin_audio,
            order=1,
            text="This is a test segment for admin audio",
            start_time=0.0,
            end_time=5.0,
            speaker_label="spk_0",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
        )

        self.user_audiosegment = AudioSegment.objects.create(
            audio=self.user_audio,
            order=1,
            text="This is a test segment for user audio",
            start_time=0.0,
            end_time=5.0,
            speaker_label="spk_0",
            create_user=self.user_scope_user,
            modify_user=self.user_scope_user,
            campaign=self.test_campaign,
        )

        self.running_audiosegment = AudioSegment.objects.create(
            audio=self.running_audio,
            order=1,
            text="This is a test segment for running audio",
            start_time=0.0,
            end_time=5.0,
            speaker_label="spk_0",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
        )

        self.finished_audiosegment = AudioSegment.objects.create(
            audio=self.finished_audio,
            order=1,
            text="This is a test segment for finished audio",
            start_time=0.0,
            end_time=5.0,
            speaker_label="spk_0",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
        )

        # Create a second AudioSegment for the admin audio with a different minute
        self.admin_audiosegment2 = AudioSegment.objects.create(
            audio=self.admin_audio,
            order=2,
            text="This is another test segment for admin audio",
            start_time=60.0,  # 1 minute
            end_time=65.0,
            speaker_label="spk_1",
            create_user=self.admin_user,
            modify_user=self.admin_user,
            campaign=self.test_campaign,
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


class AudioSegmentEditViewTestCase(AudioSegmentViewsBaseTestCase):
    """Test case for the AudioSegment views with API_ACTION_EDIT action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.edit_url = reverse(
            "analytics:audio:audiosegment:edit",
            args=[self.admin_audio.pk, self.admin_audiosegment.pk],
        )
        self.edit_user_url = reverse(
            "analytics:audio:audiosegment:edit",
            args=[self.user_audio.pk, self.user_audiosegment.pk],
        )
        self.edit_running_url = reverse(
            "analytics:audio:audiosegment:edit",
            args=[self.running_audio.pk, self.running_audiosegment.pk],
        )
        self.edit_finished_url = reverse(
            "analytics:audio:audiosegment:edit",
            args=[self.finished_audio.pk, self.finished_audiosegment.pk],
        )

    def test_get_edit_admin_user(self):
        """User with can_edit_process permission can access the edit form for audiosegment."""
        response = self.admin_client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, self.admin_audiosegment.text)

    def test_get_edit_user_scope_user_own_process(self):
        """User with can_edit_process permission and SCOPE_USER can access the edit form
        for audiosegment in their own process."""
        response = self.user_scope_client.get(self.edit_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertContains(response, self.user_audiosegment.text)

    def test_get_edit_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot access the edit form
        for audiosegment in other users' processes."""
        response = self.user_scope_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_list_only_user(self):
        """User with only list permission cannot access the edit form for audiosegment."""
        response = self.list_only_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_no_perm_user(self):
        """User with no permissions cannot access the edit form for audiosegment."""
        response = self.no_perm_client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_anonymous_user(self):
        """Test that an anonymous user cannot access the edit form for audiosegment."""
        response = self.anonymous_client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_edit_running_process(self):
        """Test that audiosegment cannot be edited in a running process."""
        response = self.admin_client.get(self.edit_running_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_edit_finished_process(self):
        """Test that audiosegment cannot be edited in a finished process."""
        response = self.admin_client.get(self.edit_finished_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_edit_admin_user_success(self):
        """User with can_edit_process permission can edit an audiosegment."""
        data = {"text": "Updated text for admin audiosegment"}
        response = self.admin_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audiosegment was updated
        self.admin_audiosegment.refresh_from_db()
        self.assertEqual(self.admin_audiosegment.text, "Updated text for admin audiosegment")

    def test_post_edit_user_scope_user_own_process_success(self):
        """User with can_edit_process permission and SCOPE_USER can edit an audiosegment in
        their own process."""
        data = {"text": "Updated text for user audiosegment"}
        response = self.user_scope_client.post(self.edit_user_url, data)
        self.assertEqual(response.status_code, 204)  # Success response

        # Verify audiosegment was updated
        self.user_audiosegment.refresh_from_db()
        self.assertEqual(self.user_audiosegment.text, "Updated text for user audiosegment")

    def test_post_edit_user_scope_user_other_process_forbidden(self):
        """User with can_edit_process permission and SCOPE_USER cannot edit audiosegment in
        other users' processes."""
        data = {"text": "Updated text for admin audiosegment"}
        response = self.user_scope_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audiosegment was not updated
        self.admin_audiosegment.refresh_from_db()
        self.assertEqual(self.admin_audiosegment.text, "This is a test segment for admin audio")

    def test_post_edit_list_only_user_forbidden(self):
        """User with only list permission cannot edit an audiosegment."""
        data = {"text": "Updated text for admin audiosegment"}
        response = self.list_only_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audiosegment was not updated
        self.admin_audiosegment.refresh_from_db()
        self.assertEqual(self.admin_audiosegment.text, "This is a test segment for admin audio")

    def test_post_edit_no_perm_user_forbidden(self):
        """User with no permissions cannot edit an audiosegment."""
        data = {"text": "Updated text for admin audiosegment"}
        response = self.no_perm_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audiosegment was not updated
        self.admin_audiosegment.refresh_from_db()
        self.assertEqual(self.admin_audiosegment.text, "This is a test segment for admin audio")

    def test_post_edit_anonymous_user_redirect(self):
        """Test that an anonymous user cannot edit an audiosegment."""
        data = {"text": "Updated text for admin audiosegment"}
        response = self.anonymous_client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Verify audiosegment was not updated
        self.admin_audiosegment.refresh_from_db()
        self.assertEqual(self.admin_audiosegment.text, "This is a test segment for admin audio")

    def test_post_edit_running_process_forbidden(self):
        """Test that audiosegment cannot be edited in a running process."""
        data = {"text": "Updated text for running audiosegment"}
        response = self.admin_client.post(self.edit_running_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audiosegment was not updated
        self.running_audiosegment.refresh_from_db()
        self.assertEqual(self.running_audiosegment.text, "This is a test segment for running audio")

    def test_post_edit_finished_process_forbidden(self):
        """Test that audiosegment cannot be edited in a finished process."""
        data = {"text": "Updated text for finished audiosegment"}
        response = self.admin_client.post(self.edit_finished_url, data)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Verify audiosegment was not updated
        self.finished_audiosegment.refresh_from_db()
        self.assertEqual(
            self.finished_audiosegment.text, "This is a test segment for finished audio"
        )


class AudioSegmentReadViewTestCase(AudioSegmentViewsBaseTestCase):
    """Test case for the AudioSegment views with API_ACTION_READ action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.read_url = reverse(
            "analytics:audio:audiosegment:read",
            args=[self.admin_audio.pk, self.admin_audiosegment.pk],
        )
        self.read_user_url = reverse(
            "analytics:audio:audiosegment:read",
            args=[self.user_audio.pk, self.user_audiosegment.pk],
        )

    def test_get_read_admin_user(self):
        """User with can_list_process permission can access the read view for audiosegment."""
        response = self.admin_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_audiosegment.text)
        self.assertContains(response, self.admin_audiosegment.speaker_label)

    def test_get_read_user_scope_user_own_process(self):
        """User with can_list_process permission and SCOPE_USER can access the read view
        for audiosegment in their own process."""
        response = self.user_scope_client.get(self.read_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_audiosegment.text)
        self.assertContains(response, self.user_audiosegment.speaker_label)

    def test_get_read_user_scope_user_other_process_forbidden(self):
        """User with can_list_process permission and SCOPE_USER cannot access the read view for
        audiosegment in other users' processes."""
        response = self.user_scope_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_list_only_user(self):
        """User with only list permission can access the read view for audiosegment."""
        response = self.list_only_client.get(self.read_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_audiosegment.text)
        self.assertContains(response, self.admin_audiosegment.speaker_label)

    def test_get_read_no_perm_user_forbidden(self):
        """User with no permissions cannot access the read view for audiosegment."""
        response = self.no_perm_client.get(self.read_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_read_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the read view for audiosegment."""
        response = self.anonymous_client.get(self.read_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_read_bad_request(self):
        """Test that POST method is not allowed for read."""
        response = self.admin_client.post(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_read_bad_request(self):
        """Test that DELETE method is not allowed for read."""
        response = self.admin_client.delete(self.read_url)
        self.assertEqual(response.status_code, 400)  # Bad request method


class AudioSegmentListViewTestCase(AudioSegmentViewsBaseTestCase):
    """Test case for the AudioSegment views with API_ACTION_LIST action."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.list_url = reverse("analytics:audio:audiosegment:list", args=[self.admin_audio.pk])
        self.list_user_url = reverse("analytics:audio:audiosegment:list", args=[self.user_audio.pk])
        self.list_running_url = reverse(
            "analytics:audio:audiosegment:list", args=[self.running_audio.pk]
        )
        self.list_finished_url = reverse(
            "analytics:audio:audiosegment:list", args=[self.finished_audio.pk]
        )

    def test_get_list_admin_user(self):
        """User with can_list_process permission can access the list view for audiosegment."""
        response = self.admin_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MINUTO - 0")  # Check for minute 0 accordion
        self.assertContains(response, "MINUTO - 1")  # Check for minute 1 accordion
        self.assertContains(response, self.admin_audiosegment.text)
        self.assertContains(response, self.admin_audiosegment2.text)

    def test_get_list_user_scope_user_own_process(self):
        """User with can_list_process permission and SCOPE_USER can access the list view
        for audiosegment in their own process."""
        response = self.user_scope_client.get(self.list_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MINUTO - 0")  # Check for minute 0 accordion
        self.assertContains(response, self.user_audiosegment.text)

    def test_get_list_user_scope_user_other_process_forbidden(self):
        """User with can_list_process permission and SCOPE_USER cannot access the list view
        for audiosegment in other users' processes."""
        response = self.user_scope_client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_list_list_only_user(self):
        """User with only list permission can access the list view for audiosegment."""
        response = self.list_only_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MINUTO - 0")  # Check for minute 0 accordion
        self.assertContains(response, "MINUTO - 1")  # Check for minute 1 accordion
        self.assertContains(response, self.admin_audiosegment.text)
        self.assertContains(response, self.admin_audiosegment2.text)

    def test_get_list_no_perm_user_forbidden(self):
        """User with no permissions cannot access the list view for audiosegment."""
        response = self.no_perm_client.get(self.list_url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_get_list_anonymous_user_redirect(self):
        """Test that an anonymous user cannot access the list view for audiosegment."""
        response = self.anonymous_client.get(self.list_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_list_running_process(self):
        """Test that audiosegment list can be accessed in a running process."""
        response = self.admin_client.get(self.list_running_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MINUTO - 0")  # Check for minute 0 accordion
        self.assertContains(response, self.running_audiosegment.text)

    def test_post_list_bad_request(self):
        """Test that POST method is not allowed for list."""
        response = self.admin_client.post(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method

    def test_delete_list_bad_request(self):
        """Test that DELETE method is not allowed for list."""
        response = self.admin_client.delete(self.list_url)
        self.assertEqual(response.status_code, 400)  # Bad request method
