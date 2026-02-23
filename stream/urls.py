from django.contrib import admin
from django.urls import path
from .views import (home, register_view,movie_detail,movies_page,
                   login_view,logout_view,profile_view,subscription,
                   create_subscription_order, payment_verify,
                   payment_page,search_api,get_suggestions,
                   category_list,play_movie,my_list,
                   toggle_my_list,Tv_shows,genre,
                   )


urlpatterns = [
    path("", home, name="home"),
    path("movies/", movies_page, name="movies"),
    path("movies/<int:pk>/", movie_detail, name="movie_detail"),
    path("category/<str:category_name>/", category_list, name="category_list"),
    path("tv-shows/", Tv_shows, name="tv_shows"),
    path('api/search/', search_api, name='search_api'),
    path('api/suggestions/', get_suggestions, name='get_suggestions'),
    path('play/<int:movie_id>/', play_movie, name='play_movie'),

    path("genres/", genre, name="genres"),
    path("my-list/", my_list, name="my_list"),
    path('toggle_my_list/<int:movie_id>/', toggle_my_list, name='toggle_my_list'),
    
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    path("profile/", profile_view, name="profile"),
    path("subscription/", subscription, name="subscription"),
    path("payment_page/<str:plan_name>/", payment_page, name="payment_page"),
    path("create_subscription_order/", create_subscription_order, name="create_subscription_order"),
    path("payment_verify/", payment_verify, name="payment_verify"),
]