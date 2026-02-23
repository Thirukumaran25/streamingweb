from django.contrib import admin
from .models import Movie, Genre, MovieCast,Cast


# Register your models here.

@admin.register(Cast)
class CastAdmin(admin.ModelAdmin):
    list_display = ('real_name',)
    
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class')
    search_fields = ('name',)


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 1

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_featured')
    list_filter = ('category', 'is_featured')
    inlines = [MovieCastInline]