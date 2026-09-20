import random
from django import forms
from django.contrib.auth import authenticate
from .models import User, Event, Gallery


SAMPLE_EVENT_TITLES = [
    "e.g. Rahul & Sneha Wedding",
    "e.g. Annual Tech Summit 2026",
    "e.g. Autumn Fashion Gala",
    "e.g. Kapoor Family Portrait",
    "e.g. Royal Palace Reception",
    "e.g. Horizon Product Showcase",
]

SAMPLE_LOCATIONS = [
    "e.g. Grand Ballroom, Taj Palace",
    "e.g. Sunset Resort & Spa",
    "e.g. Metropolitan Convention Center",
    "e.g. Botanical Gardens Pavilion",
]


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


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            'placeholder': '••••••••',
        })
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'role']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'placeholder': 'Full Name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'placeholder': 'name@example.com',
            }),
            'role': forms.Select(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white focus:outline-none focus:border-zinc-500 transition',
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'title' in self.fields:
            self.fields['title'].widget.attrs['placeholder'] = random.choice(SAMPLE_EVENT_TITLES)
        if 'location' in self.fields:
            self.fields['location'].widget.attrs['placeholder'] = random.choice(SAMPLE_LOCATIONS)

    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
                'rows': 3,
                'placeholder': 'e.g. Full ceremony coverage, reception highlights, and portraits...',
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white focus:outline-none focus:border-zinc-500 transition',
                'type': 'date',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition',
            }),
        }


class GalleryForm(forms.ModelForm):
    pin = forms.CharField(
        max_length=6,
        min_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-md text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 transition font-mono tracking-wider',
        }),
        help_text="Set or update the 6-digit access PIN for customer access."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'pin' in self.fields:
            self.fields['pin'].widget.attrs['placeholder'] = f"{random.randint(100000, 999999)}"

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
