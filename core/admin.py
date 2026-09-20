from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Event, EventMember, Photo, Gallery


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Studio Role', {'fields': ('role', 'name')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Studio Role', {'fields': ('role', 'name')}),
    )
    ordering = ('email',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'event_date', 'location', 'created_at')
    search_fields = ('title', 'location')


@admin.register(EventMember)
class EventMemberAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'created_at')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('filename', 'event', 'uploaded_by', 'is_selected', 'file_size', 'created_at')
    list_filter = ('is_selected', 'event')


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'slug', 'is_published', 'published_at', 'expires_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'slug')

