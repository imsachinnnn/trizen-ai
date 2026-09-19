import io
from PIL import Image, ImageDraw
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core.models import User, Event, EventMember, Photo, Gallery


class Command(BaseCommand):
    help = "Seeds demo admin, team member, 'Arjun & Priya Wedding' event, photos, and PIN-protected gallery."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Starting demo data seeding..."))

        # 1. Create Admin User
        admin_user, _ = User.objects.get_or_create(
            email="admin@trizen.com",
            defaults={
                "username": "admin@trizen.com",
                "name": "Arjun Lead (Admin)",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password("AdminPass123!")
        admin_user.role = User.Role.ADMIN
        admin_user.save()

        # 2. Create Team Member User
        team_user, _ = User.objects.get_or_create(
            email="photographer@trizen.com",
            defaults={
                "username": "photographer@trizen.com",
                "name": "Priya Photographer",
                "role": User.Role.TEAM_MEMBER,
            }
        )
        team_user.set_password("TeamPass123!")
        team_user.role = User.Role.TEAM_MEMBER
        team_user.save()

        self.stdout.write(self.style.SUCCESS("Demo users created: admin@trizen.com, photographer@trizen.com"))

        # 3. Create Demo Event
        event, _ = Event.objects.get_or_create(
            title="Arjun & Priya Wedding",
            defaults={
                "description": "Collaborative wedding ceremony and reception photo collection.",
                "event_date": timezone.now().date(),
                "location": "Grand Palace Resort, Udaipur",
                "created_by": admin_user,
            }
        )

        EventMember.objects.get_or_create(event=event, user=admin_user)
        EventMember.objects.get_or_create(event=event, user=team_user)

        self.stdout.write(self.style.SUCCESS("Demo Event 'Arjun & Priya Wedding' created."))

        # 4. Generate Sample Photography Images
        colors = [
            ("#1e293b", "Ceremony Entrance"),
            ("#0f172a", "Bridal Portrait"),
            ("#1e1b4b", "Exchange of Vows"),
            ("#064e3b", "Mandap Rituals"),
            ("#451a03", "Sunset Reception"),
            ("#312e81", "First Dance"),
            ("#111827", "Family Toast"),
            ("#14532d", "Ring Exchange"),
            ("#701a75", "Floral Decor"),
            ("#365314", "Couple Promenade"),
        ]

        if event.photos.count() == 0:
            for i, (bg_color, title) in enumerate(colors):
                img = Image.new("RGB", (1200, 800), color=bg_color)
                draw = ImageDraw.Draw(img)
                draw.rectangle([60, 60, 1140, 740], outline="#ffffff", width=4)
                draw.text((100, 100), f"Arjun & Priya Wedding - {title}", fill="#ffffff")

                img_io = io.BytesIO()
                img.save(img_io, format="JPEG", quality=90)
                img_file = ContentFile(img_io.getvalue(), name=f"wedding_photo_{i+1}.jpg")

                thumb_img = img.copy()
                thumb_img.thumbnail((300, 300))
                thumb_io = io.BytesIO()
                thumb_img.save(thumb_io, format="WEBP", quality=85)
                thumb_file = ContentFile(thumb_io.getvalue(), name=f"thumb_wedding_photo_{i+1}.webp")

                # First 6 photos selected for gallery
                is_selected = i < 6
                uploader = team_user if i % 2 == 0 else admin_user

                Photo.objects.create(
                    event=event,
                    uploaded_by=uploader,
                    image=img_file,
                    thumbnail=thumb_file,
                    filename=f"wedding_photo_{i+1}.jpg",
                    storage_location=f"events/{event.id}/photos/",
                    file_size=len(img_io.getvalue()),
                    mime_type="image/jpeg",
                    width=1200,
                    height=800,
                    is_selected=is_selected,
                )

            self.stdout.write(self.style.SUCCESS("Uploaded sample photos created."))

        # 5. Create Published Gallery
        gallery, _ = Gallery.objects.get_or_create(
            event=event,
            defaults={
                "slug": "arjun-priya-wedding",
                "pin_hash": make_password("482917"),
                "title": "Arjun & Priya Wedding",
                "description": "Official published wedding gallery for Arjun & Priya.",
                "is_published": True,
                "published_at": timezone.now(),
            }
        )
        gallery.slug = "arjun-priya-wedding"
        gallery.pin_hash = make_password("482917")
        gallery.is_published = True
        gallery.save()

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("DEMO SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("Admin Email: admin@trizen.com | Pass: AdminPass123!"))
        self.stdout.write(self.style.SUCCESS("Team Member Email: photographer@trizen.com | Pass: TeamPass123!"))
        self.stdout.write(self.style.SUCCESS("Public Gallery Link: /gallery/arjun-priya-wedding/"))
        self.stdout.write(self.style.SUCCESS("Gallery Access PIN: 482917"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
