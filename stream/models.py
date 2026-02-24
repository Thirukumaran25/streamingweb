from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import datetime

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Cast(models.Model):
    real_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='cast/')

    def __str__(self):
        return self.real_name


class Genre(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='genres/')
    icon_class = models.CharField(max_length=50, default='bx-film', help_text="Boxicon class name (e.g., bx-run)")

    def __str__(self):
        return self.name
    
class Movie(models.Model):
    CATEGORY_CHOICES = [
        ('movie', 'Movie'),
        ('tv', 'TV Show'),
    ]
    title = models.CharField(max_length=255)
    poster = models.ImageField(upload_to='posters/')
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    director = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to='genres/', null=True, blank=True)
    rating = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)
    cast_members = models.ManyToManyField(Cast, through='MovieCast')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='movie')
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class MovieCast(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cast = models.ForeignKey(Cast, on_delete=models.CASCADE)
    character_name = models.CharField(max_length=255, null=True, blank=True) 
    

class MyList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
    

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('pro', 'Pro'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES)
    order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} - {self.plan_name}"

    @property
    def is_expired(self):
        return timezone.now() > self.expiry_date