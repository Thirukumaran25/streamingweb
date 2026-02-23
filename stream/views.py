from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib import messages
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import JsonResponse
from .models import Profile,Movie,Genre,Cast,MyList
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import razorpay
from django.core.cache import cache
from .forms import RegisterForm
from django.views.decorators.http import require_POST


# Create your views here.

def home(request):
    featured = Movie.objects.filter(is_featured=True).first()
    movies = Movie.objects.filter(category='movie')
    tv_shows = Movie.objects.filter(category='tv')
    continue_watching = Movie.objects.all()[:5] 
    my_list = []
    if request.user.is_authenticated:
        my_list = MyList.objects.filter(user=request.user).select_related('movie')
    
    genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Thriller', 'Romance', 'Animation']

    context = {
        'featured': Movie.objects.filter(is_featured=True).first(),
        'movies': Movie.objects.filter(category='movie'),
        'tv_shows': Movie.objects.filter(category='tv'),
        "my_list": my_list,
        'genres': Genre.objects.all(), 
    }
    return render(request, 'home.html', context)


def movies_page(request):
    genres = Genre.objects.prefetch_related('movie_set')

    context = {
        'genres': genres
    }
    return render(request, 'movies.html', context)

@login_required(login_url='login')
def play_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    return render(request, 'play_movie.html', {'movie': movie})

def Tv_shows(request):
    return render(request, 'tv_shows.html',)

def genre(request):
    genres= Genre.objects.all()
    context = {
        'genres': genres
    }
    return render(request, 'genre.html',context)


def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    cast_list = movie.moviecast_set.all() 
    return render(request, 'detail.html', {'movie': movie, 'cast_list': cast_list})


def category_list(request, category_name):
    db_category = 'movie' if category_name == 'movies' else 'tv'

    genre_name = request.GET.get('genre')

    items = Movie.objects.filter(category=db_category)

    if genre_name:
        items = items.filter(genre__name=genre_name)

    display_title = "Movies" if db_category == 'movie' else "TV Shows"

    return render(request, 'list.html', {
        'items': items,
        'display_title': display_title,
    })


@login_required
def my_list(request):
    my_list_items = MyList.objects.filter(user=request.user).select_related('movie')

    return render(request, "my_list.html", {
        "my_list_items": my_list_items
    })

@login_required
@require_POST
def toggle_my_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    obj = MyList.objects.filter(user=request.user, movie=movie)

    if obj.exists():
        obj.delete()
    else:
        MyList.objects.create(user=request.user, movie=movie)

    return redirect('my_list')


def search_api(request):
    query = request.GET.get('q', '')
    results = []
    
    if len(query) > 2:
        movies = Movie.objects.filter(
            Q(title__icontains=query) | 
            Q(director__icontains=query) |
            Q(genres__name__icontains=query) |
            Q(cast_members__real_name__icontains=query)
        ).distinct()[:12]
        
        for movie in movies:
            results.append({
                'Title': movie.title,
                'Poster': movie.poster.url if movie.poster else 'N/A',
                'imdbID': movie.id,
                'Year': movie.year if movie.year else ""
            })
            
    return JsonResponse({'results': results})


def get_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = set()

    if len(query) > 1:
        directors = Movie.objects.filter(director__icontains=query).values_list('director', flat=True)[:3]
        suggestions.update(directors)
        cast = Cast.objects.filter(real_name__icontains=query).values_list('real_name', flat=True)[:3]
        suggestions.update(cast)
        genres = Genre.objects.filter(name__icontains=query).values_list('name', flat=True)[:3]
        suggestions.update(genres)
    return JsonResponse({'suggestions': list(suggestions)[:6]})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            mobile = form.cleaned_data.get('mobile_no')
            
            user.profile.mobile = mobile
            user.profile.save()
            
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

def subscription(request):
    return render(request, 'subscription.html')


def payment_page(request, plan_name):
    plan_map = {
        'basic': {'name': 'Basic', 'price': 599},
        'standard': {'name': 'Standard', 'price': 1599},
        'premium': {'name': 'Premium', 'price': 1999},
    }

    selected_plan = plan_map.get(plan_name.lower(), plan_map['basic'])
    amount_in_paise = selected_plan['price'] * 100
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"receipt_{plan_name}",
        "payment_capture": 1 
    }
    order = client.order.create(data=data)

    context = {
        'plan': selected_plan,
        'amount': amount_in_paise,
        'display_amount': selected_plan['price'], 
        'order_id': order['id'],
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'payment_page.html', context)


@login_required
def profile_view(request):
    user_profile = request.user.profile
    context = {
        'user': request.user,
        'is_subscribed': user_profile.is_subscribed,
        'mobile': user_profile.mobile,
    }
    return render(request, 'profile.html', context)


def create_subscription_order(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    amount = 159900 
    data = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"receipt_{request.user.id}",
    }
    razorpay_order = client.order.create(data=data)
    
    context = {
        "order_id": razorpay_order['id'],
        "amount": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "user": request.user,
    }
    return render(request, 'payment_page.html', context)


def payment_verify(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    params_dict = {
        'razorpay_order_id': request.GET.get('order_id'),
        'razorpay_payment_id': request.GET.get('payment_id'),
        'razorpay_signature': request.GET.get('signature')
    }

    try:
        client.utility.verify_payment_signature(params_dict)
        messages.success(request, "Payment successful! Welcome to Streaming Star.")
        return render(request, 'payment_success.html', {'payment_id': params_dict['razorpay_payment_id']})

    except razorpay.errors.SignatureVerificationError:
        messages.error(request, "Payment verification failed. Please contact support.")
        return render(request, 'payment_failed.html')
    except Exception as e:
        messages.error(request, "An unexpected error occurred.")
        return redirect('pricing')
    