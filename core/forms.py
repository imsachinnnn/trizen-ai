from django import forms
from django.contrib.auth import authenticate
from .models import User, Event, Gallery


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            'placeholder': 'user@example.com',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            'placeholder': '••••••••',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password. Please try again.")
            cleaned_data['user'] = user
        return cleaned_data


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'placeholder': "e.g. Vijay and Rashmika's Wedding",
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'rows': 3,
                'placeholder': 'Event details or notes...',
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white focus:outline-none focus:border-zinc-500 transition',
                'type': 'date',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'placeholder': 'Location / Venue',
            }),
        }


class GalleryForm(forms.ModelForm):
    pin = forms.CharField(
        max_length=6,
        min_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition font-mono tracking-wider',
            'placeholder': '123456',
        }),
        help_text="Set or update the 6-digit access PIN for customer access."
    )

    class Meta:
        model = Gallery
        fields = ['title', 'description', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'rows': 2,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-zinc-800 bg-zinc-900 text-white focus:ring-0',
            }),
        }
