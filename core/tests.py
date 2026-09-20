import io
from PIL import Image
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core.models import User, Event, EventMember, Photo, Gallery


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class PhotoSharingTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Create Admin User
        self.admin_user = User.objects.create_user(
            username="admin@trizen.com",
            email="admin@trizen.com",
            password="AdminPass123!",
            name="Admin Lead",
            role=User.Role.ADMIN,
        )

        # 2. Create Team Member A (Assigned)
        self.team_user_a = User.objects.create_user(
            username="team_a@trizen.com",
            email="team_a@trizen.com",
            password="TeamPass123!",
            name="Team Member A",
            role=User.Role.TEAM_MEMBER,
        )

        # 3. Create Team Member B (Unassigned)
        self.team_user_b = User.objects.create_user(
            username="team_b@trizen.com",
            email="team_b@trizen.com",
            password="TeamPass123!",
            name="Team Member B",
            role=User.Role.TEAM_MEMBER,
        )

        # 4. Create Event and assign Team Member A
        self.event = Event.objects.create(
            title="Arjun & Priya Wedding",
            description="Wedding ceremony photos",
            created_by=self.admin_user,
        )
        EventMember.objects.create(event=self.event, user=self.admin_user)
        EventMember.objects.create(event=self.event, user=self.team_user_a)

        # 5. Create Sample Image for tests
        img = Image.new("RGB", (800, 600), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        self.sample_image = SimpleUploadedFile(
            "sample.jpg", img_bytes.getvalue(), content_type="image/jpeg"
        )

        # 6. Create Published Gallery with PIN 482917
        self.gallery = Gallery.objects.create(
            event=self.event,
            slug="arjun-priya-wedding",
            pin_hash=make_password("482917"),
            title="Arjun & Priya Wedding",
            is_published=True,
            published_at=timezone.now(),
        )

        # 7. Upload Sample Photo
        img_bytes.seek(0)
        self.photo = Photo.objects.create(
            event=self.event,
            uploaded_by=self.team_user_a,
            image=SimpleUploadedFile("test_photo.jpg", img_bytes.getvalue(), content_type="image/jpeg"),
            filename="test_photo.jpg",
            storage_location=f"events/{self.event.id}/photos/",
            file_size=len(img_bytes.getvalue()),
            mime_type="image/jpeg",
            width=800,
            height=600,
            is_selected=True,
        )

    # 1. Authentication Test
    def test_admin_and_team_member_login(self):
        # Login Admin
        login_res_admin = self.client.login(username="admin@trizen.com", password="AdminPass123!")
        self.assertTrue(login_res_admin)

        # Login Team Member
        self.client.logout()
        login_res_team = self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        self.assertTrue(login_res_team)

    # 2. Event Isolation Test
    def test_team_member_event_isolation(self):
        # Team Member A (Assigned) accesses event -> 200 OK
        self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        res_a = self.client.get(reverse("event_detail", kwargs={"pk": self.event.pk}))
        self.assertEqual(res_a.status_code, 200)

        # Team Member B (Unassigned) accesses event -> 403 Forbidden
        self.client.logout()
        self.client.login(username="team_b@trizen.com", password="TeamPass123!")
        res_b = self.client.get(reverse("event_detail", kwargs={"pk": self.event.pk}))
        self.assertEqual(res_b.status_code, 403)

    # 3. Gallery Publishing Authorization Test
    def test_team_member_cannot_publish_gallery(self):
        self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        res = self.client.post(
            reverse("gallery_publish", kwargs={"pk": self.event.pk}),
            {"title": "Hacked Gallery", "pin": "999999", "is_published": "on"}
        )
        self.assertEqual(res.status_code, 403)

    # 4. Photo Upload & Pillow Processing Test
    def test_photo_upload_processing_and_thumbnail(self):
        self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        
        img = Image.new("RGB", (1000, 750), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        upload_file = SimpleUploadedFile("upload_test.jpg", img_bytes.getvalue(), content_type="image/jpeg")

        res = self.client.post(
            reverse("api_photo_upload", kwargs={"event_id": self.event.pk}),
            {"photos": upload_file},
            format="multipart"
        )
        self.assertEqual(res.status_code, 201)

        new_photo = Photo.objects.filter(filename="upload_test.jpg").first()
        self.assertIsNotNone(new_photo)
        self.assertEqual(new_photo.width, 1000)
        self.assertEqual(new_photo.height, 750)
        self.assertIsNotNone(new_photo.thumbnail)

    # 5. PIN Protection Locked State Test
    def test_gallery_pin_protection_locked_state(self):
        # Access public gallery without PIN verification
        res = self.client.get(reverse("public_gallery", kwargs={"slug": self.gallery.slug}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Enter the 6-digit access PIN")

    # 6. PIN Verification Wrong PIN Test
    def test_gallery_pin_verification_wrong_pin(self):
        res = self.client.post(
            reverse("api_gallery_verify_pin", kwargs={"slug": self.gallery.slug}),
            {"pin": "000000"},
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json().get("success"))

    # 7. PIN Verification Correct PIN Test
    def test_gallery_pin_verification_correct_pin(self):
        # Submit correct PIN 482917
        res_verify = self.client.post(
            reverse("api_gallery_verify_pin", kwargs={"slug": self.gallery.slug}),
            {"pin": "482917"},
            content_type="application/json"
        )
        self.assertEqual(res_verify.status_code, 200)
        self.assertTrue(res_verify.json().get("success"))

        # Subsequent GET to gallery renders unlocked photos
        res_unlocked = self.client.get(reverse("public_gallery", kwargs={"slug": self.gallery.slug}))
        self.assertEqual(res_unlocked.status_code, 200)
        self.assertContains(res_unlocked, "test_photo.jpg")

    # 8. Unpublished Gallery Access Test
    def test_unpublished_gallery_returns_404(self):
        self.gallery.is_published = False
        self.gallery.save()

        # Unauthenticated customer accessing unpublished gallery -> 404
        res = self.client.get(reverse("public_gallery", kwargs={"slug": self.gallery.slug}))
        self.assertEqual(res.status_code, 404)

    # 9. Private Direct Access Security Test (Bypass Prevention)
    def test_private_photo_access_cannot_be_bypassed(self):
        # Direct unauthenticated access to private media serve endpoint -> 403 Forbidden
        url = reverse("private_media_serve", kwargs={"photo_id": self.photo.id, "photo_type": "original"})
        res_unauth = self.client.get(url)
        self.assertEqual(res_unauth.status_code, 403)

        # Authenticated assigned team member access -> 200 OK or 302 Redirect to R2 location
        self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        res_auth = self.client.get(url)
        self.assertIn(res_auth.status_code, [200, 302])

    # 10. Photo Deletion Authorization Test (Admin Only)
    def test_admin_can_delete_photo_and_team_member_forbidden(self):
        url = reverse("api_photo_delete", kwargs={"event_id": self.event.id})

        # Team Member attempting to delete photo -> 403 Forbidden
        self.client.login(username="team_a@trizen.com", password="TeamPass123!")
        res_forbidden = self.client.post(url, {"photo_ids": [str(self.photo.id)]}, content_type="application/json")
        self.assertEqual(res_forbidden.status_code, 403)
        self.assertTrue(Photo.objects.filter(id=self.photo.id).exists())

        # Admin attempting to delete photo -> 200 OK and photo removed
        self.client.logout()
        self.client.login(username="admin@trizen.com", password="AdminPass123!")
        res_success = self.client.post(url, {"photo_ids": [str(self.photo.id)]}, content_type="application/json")
        self.assertEqual(res_success.status_code, 200)
        self.assertFalse(Photo.objects.filter(id=self.photo.id).exists())
