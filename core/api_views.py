import os
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Event, Photo, Gallery
from .permissions import is_admin_user, is_assigned_to_event
from .utils import process_and_validate_image, get_signed_media_url


class PhotoUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        if not is_assigned_to_event(request.user, event):
            return Response(
                {"error": "You are not assigned to this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        files = request.FILES.getlist('photos')
        if not files and 'file' in request.FILES:
            files = [request.FILES['file']]

        if not files:
            return Response(
                {"error": "No image files were provided in the upload request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_photos = []
        errors = []

        for file in files:
            try:
                validated_file, width, height, file_size, mime_type, thumbnail_file = process_and_validate_image(file)
                
                photo = Photo.objects.create(
                    event=event,
                    uploaded_by=request.user,
                    image=validated_file,
                    thumbnail=thumbnail_file,
                    filename=file.name,
                    storage_location=f"events/{event.id}/photos/",
                    file_size=file_size,
                    mime_type=mime_type,
                    width=width,
                    height=height,
                    is_selected=False,
                )
                
                uploaded_photos.append({
                    "id": str(photo.id),
                    "filename": photo.filename,
                    "file_size": photo.file_size,
                    "mime_type": photo.mime_type,
                    "width": photo.width,
                    "height": photo.height,
                    "original_url": get_signed_media_url(photo, is_thumbnail=False, request=request),
                    "thumb_url": get_signed_media_url(photo, is_thumbnail=True, request=request),
                })
            except Exception as e:
                errors.append({"filename": file.name, "error": str(e)})

        if not uploaded_photos and errors:
            return Response(
                {"error": "Photo upload failed.", "details": errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": f"Successfully uploaded {len(uploaded_photos)} photos.",
            "photos": uploaded_photos,
            "errors": errors,
        }, status=status.HTTP_201_CREATED)


class PhotoSelectionToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        if not is_admin_user(request.user):
            return Response(
                {"error": "Only Admin leads can select photos for publishing."},
                status=status.HTTP_403_FORBIDDEN
            )

        photo_ids = request.data.get('photo_ids', [])
        action = request.data.get('action', 'toggle')  # 'select', 'deselect', 'toggle'

        if not photo_ids:
            return Response(
                {"error": "No photo_ids provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        photos = Photo.objects.filter(id__in=photo_ids, event=event)
        updated_count = 0

        for photo in photos:
            if action == 'select':
                photo.is_selected = True
            elif action == 'deselect':
                photo.is_selected = False
            else:
                photo.is_selected = not photo.is_selected
            photo.save()
            updated_count += 1

        total_selected = event.photos.filter(is_selected=True).count()

        return Response({
            "message": f"Updated selection state for {updated_count} photos.",
            "updated_count": updated_count,
            "total_selected": total_selected,
        }, status=status.HTTP_200_OK)


class GalleryVerifyPINAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        gallery = get_object_or_404(Gallery, slug=slug)

        if not gallery.is_published:
            return Response(
                {"error": "Gallery not found or is currently unpublished."},
                status=status.HTTP_404_NOT_FOUND
            )

        submitted_pin = request.data.get('pin', '').strip()
        if not submitted_pin:
            return Response(
                {"error": "PIN is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify hashed PIN
        if check_password(submitted_pin, gallery.pin_hash):
            request.session[f'gallery_unlocked_{slug}'] = True
            return Response({
                "success": True,
                "message": "PIN verified successfully. Gallery unlocked.",
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"success": False, "error": "Incorrect PIN. Access denied."},
                status=status.HTTP_401_UNAUTHORIZED
            )
