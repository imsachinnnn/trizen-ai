import os
import random
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import messages

from .models import User, Event, EventMember, Photo, Gallery
from .forms import LoginForm, RegisterForm, EventForm, GalleryForm
from .permissions import is_admin_user, is_assigned_to_event, admin_required
from .utils import get_signed_media_url


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.name or user.email}!")
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    if is_admin_user(user):
        events = Event.objects.all().order_by('-created_at')
    else:
        events = Event.objects.filter(assigned_members=user).order_by('-created_at')

    # Annotate events with photo metrics
    events_data = []
    for event in events:
        photos = event.photos.all()
        total_photos = photos.count()
        selected_photos = photos.filter(is_selected=True).count()
        gallery = getattr(event, 'gallery', None)
        events_data.append({
            'event': event,
            'total_photos': total_photos,
            'selected_photos': selected_photos,
            'gallery': gallery,
        })

    return render(request, 'dashboard.html', {
        'events_data': events_data,
        'is_admin': is_admin_user(user),
    })


@login_required
@admin_required
def event_create_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            # Assign creator as an event member as well
            EventMember.objects.create(event=event, user=request.user)
            messages.success(request, f"Event '{event.title}' created successfully.")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    return render(request, 'event_form.html', {'form': form})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not is_assigned_to_event(request.user, event):
        return HttpResponseForbidden("You are not assigned to this event.")

    is_admin = is_admin_user(request.user)
    photos = event.photos.all().select_related('uploaded_by').order_by('-created_at')
    gallery = getattr(event, 'gallery', None)
    
    # Process signed media URLs for each photo
    photos_data = []
    for photo in photos:
        photos_data.append({
            'photo': photo,
            'original_url': get_signed_media_url(photo, is_thumbnail=False, request=request),
            'thumb_url': get_signed_media_url(photo, is_thumbnail=True, request=request),
        })

    # Available team members to add (for Admin)
    available_users = []
    if is_admin:
        assigned_user_ids = event.assigned_members.values_list('id', flat=True)
        available_users = User.objects.exclude(id__in=assigned_user_ids)

    gallery_form = GalleryForm(instance=gallery) if is_admin else None
    random_pin = f"{random.randint(100000, 999999)}"

    return render(request, 'event_detail.html', {
        'event': event,
        'photos_data': photos_data,
        'total_photos': len(photos_data),
        'selected_photos': sum(1 for p in photos if p.is_selected),
        'gallery': gallery,
        'gallery_form': gallery_form,
        'random_pin': random_pin,
        'is_admin': is_admin,
        'assigned_members': event.assigned_members.all(),
        'available_users': available_users,
    })


@login_required
@admin_required
def event_member_add_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user_to_add = get_object_or_404(User, id=user_id)
            EventMember.objects.get_or_create(event=event, user=user_to_add)
            messages.success(request, f"Assigned {user_to_add.name or user_to_add.email} to event.")
        else:
            messages.error(request, "Please select a registered user to assign.")

    return redirect('event_detail', pk=pk)


@login_required
@admin_required
def event_member_remove_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user_to_remove = get_object_or_404(User, id=user_id)
            # Cannot remove creator/owner
            if user_to_remove == event.created_by:
                messages.error(request, "Cannot remove the event creator.")
            else:
                EventMember.objects.filter(event=event, user=user_to_remove).delete()
                messages.success(request, f"Removed {user_to_remove.name or user_to_remove.email} from event.")
    return redirect('event_detail', pk=pk)


@login_required
@admin_required
def gallery_publish_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    gallery = getattr(event, 'gallery', None)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip() or event.title
        description = request.POST.get('description', '')
        pin = request.POST.get('pin', '').strip()
        is_published = request.POST.get('is_published') == 'on'

        # Validate 6-digit numeric PIN
        if pin:
            if len(pin) != 6 or not pin.isdigit():
                messages.error(request, "Access PIN must be exactly 6 numeric digits (e.g. 482917).")
                return redirect('event_detail', pk=pk)

        # Sync event title as well so Dashboard, Studio, and Gallery reflect the updated title
        event.title = title
        event.save()

        slug = slugify(title) or str(event.id)[:8]
        
        # Check slug collision
        if Gallery.objects.filter(slug=slug).exclude(event=event).exists():
            slug = f"{slug}-{str(event.id)[:4]}"

        expires_at_str = request.POST.get('expires_at', '').strip()
        expires_at = None
        if expires_at_str:
            try:
                expires_at = timezone.datetime.fromisoformat(expires_at_str)
            except Exception:
                pass

        if not gallery:
            if not pin:
                pin = f"{random.randint(100000, 999999)}"  # Generate random 6-digit PIN if empty
            gallery = Gallery(
                event=event,
                title=title,
                description=description,
                slug=slug,
                pin_hash=make_password(pin),
                is_published=is_published,
                published_at=timezone.now() if is_published else None,
                expires_at=expires_at,
            )
        else:
            gallery.title = title
            gallery.description = description
            gallery.slug = slug
            gallery.expires_at = expires_at
            if pin:
                gallery.pin_hash = make_password(pin)
            if is_published and not gallery.is_published:
                gallery.published_at = timezone.now()
            gallery.is_published = is_published

        gallery.save()
        messages.success(request, f"Gallery configuration updated. PIN set to '{pin or 'existing'}'." if is_published else "Gallery saved as draft.")

    return redirect('event_detail', pk=pk)


def public_gallery_view(request, slug):
    gallery = get_object_or_404(Gallery, slug=slug)

    # If gallery is not published, return 404 for unauthenticated customers
    if not gallery.is_published and not is_admin_user(request.user):
        raise Http404("Gallery not found or is currently unpublished.")

    # Expiration check
    if gallery.is_expired() and not is_admin_user(request.user):
        return render(request, 'gallery.html', {
            'gallery': gallery,
            'is_expired': True,
        })

    session_key = f'gallery_unlocked_{slug}'
    is_unlocked = request.session.get(session_key, False) or is_admin_user(request.user)

    if not is_unlocked:
        return render(request, 'gallery.html', {
            'gallery': gallery,
            'is_locked': True,
        })

    # Render unlocked published gallery (Selected photos only)
    photos = gallery.event.photos.filter(is_selected=True).select_related('uploaded_by').order_by('-created_at')
    photos_data = []
    for photo in photos:
        photos_data.append({
            'photo': photo,
            'original_url': get_signed_media_url(photo, is_thumbnail=False, request=request),
            'thumb_url': get_signed_media_url(photo, is_thumbnail=True, request=request),
        })

    return render(request, 'gallery.html', {
        'gallery': gallery,
        'is_locked': False,
        'photos_data': photos_data,
        'total_photos': len(photos_data),
    })


def private_media_serve_view(request, photo_id, photo_type):
    """
    Direct Private Object Security Layer.
    Enforces that unauthenticated / unauthorized requests CANNOT access raw image files directly.
    """
    photo = get_object_or_404(Photo, id=photo_id)
    gallery = getattr(photo.event, 'gallery', None)
    
    # Permission Check
    authorized = False
    
    # 1. Admin or Assigned Team Member
    if request.user.is_authenticated and is_assigned_to_event(request.user, photo.event):
        authorized = True
    
    # 2. PIN-authenticated Customer accessing selected photo in a published gallery
    elif gallery and gallery.is_published and photo.is_selected:
        session_key = f'gallery_unlocked_{gallery.slug}'
        if request.session.get(session_key):
            authorized = True

    if not authorized:
        return HttpResponseForbidden("Unauthorized: Direct object access denied.")

    target_file = photo.thumbnail if photo_type == 'thumb' and photo.thumbnail else photo.image
    if not target_file or not os.path.exists(target_file.path):
        raise Http404("Photo binary file not found.")

    content_type, _ = mimetypes.guess_type(target_file.path)
    with open(target_file.path, 'rb') as f:
        return HttpResponse(f.read(), content_type=content_type or 'image/jpeg')
