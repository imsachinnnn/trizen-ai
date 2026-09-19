from django.urls import path
from . import views, api_views

urlpatterns = [
    # Auth Views
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard & Event Views
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('events/create/', views.event_create_view, name='event_create'),
    path('events/<uuid:pk>/', views.event_detail_view, name='event_detail'),
    path('events/<uuid:pk>/members/add/', views.event_member_add_view, name='event_member_add'),
    path('events/<uuid:pk>/members/remove/', views.event_member_remove_view, name='event_member_remove'),
    path('events/<uuid:pk>/gallery/publish/', views.gallery_publish_view, name='gallery_publish'),

    # Public Customer Gallery
    path('gallery/<slug:slug>/', views.public_gallery_view, name='public_gallery'),

    # Direct Private Media Serving
    path('media/private/<uuid:photo_id>/<str:photo_type>/', views.private_media_serve_view, name='private_media_serve'),

    # DRF API Endpoints
    path('api/events/<uuid:event_id>/photos/upload/', api_views.PhotoUploadAPIView.as_view(), name='api_photo_upload'),
    path('api/events/<uuid:event_id>/photos/select/', api_views.PhotoSelectionToggleAPIView.as_view(), name='api_photo_select'),
    path('api/events/<uuid:event_id>/photos/delete/', api_views.PhotoDeleteAPIView.as_view(), name='api_photo_delete'),
    path('api/gallery/<slug:slug>/verify-pin/', api_views.GalleryVerifyPINAPIView.as_view(), name='api_gallery_verify_pin'),
]
