from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib import messages
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import JsonResponse
from .models import Profile,Movie,Genre,Cast,MyList,Subscription
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import razorpay
from django.core.cache import cache
from .forms import RegisterForm
from django.views.decorators.http import require_POST
import datetime
from django.utils import timezone


# Create your views here.

def home(request):
    featured = Movie.objects.filter(is_featured=True).first()
    is_in_list = False
    if request.user.is_authenticated and featured:
        is_in_list = MyList.objects.filter(user=request.user, movie=featured).exists()

    movies = Movie.objects.filter(category='movie')
    tv_shows = Movie.objects.filter(category='tv')

    my_list = []
    if request.user.is_authenticated:
        my_list = MyList.objects.filter(user=request.user).select_related('movie')

    context = {
        'featured': featured,
        'movies': movies,
        'tv_shows': tv_shows,
        "my_list": my_list,
        'is_in_list': is_in_list, # This now refers to the featured movie
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
    subscription = Subscription.objects.filter(user=request.user, active=True).first()
    if not subscription or subscription.expiry_date < timezone.now():
        user_profile = request.user.profile
        if user_profile.is_subscribed:
            user_profile.is_subscribed = False
            user_profile.save()
            
        messages.warning(request, "Please subscribe to a plan to watch this movie.")
        return redirect('subscription')

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
    
    similar_movies = Movie.objects.filter(
        genre=movie.genre
    ).exclude(id=movie.id)[:6]  

    is_in_list = False
    if request.user.is_authenticated:
        is_in_list = MyList.objects.filter(user=request.user, movie=movie).exists()

    context = {
        'movie': movie, 
        'cast_list': cast_list,
        'is_in_list': is_in_list,
        'similar_movies': similar_movies,
    } 
    return render(request, 'detail.html', context)


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
        messages.info(request, f"Removed {movie.title} from your list.")
    else:
        MyList.objects.create(user=request.user, movie=movie)
        messages.success(request, f"Added {movie.title} to your list.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))


def search_api(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if len(query) >= 2:
        # Fixed: Changed 'genres' to 'genre' based on your model choices
        movies = Movie.objects.filter(
            Q(title__icontains=query) | 
            Q(director__icontains=query) |
            Q(genre__name__icontains=query) | # Changed from genres__name
            Q(cast_members__real_name__icontains=query)
        ).distinct()[:15]
        
        for movie in movies:
            results.append({
                'Title': movie.title,
                'Poster': movie.poster.url if movie.poster else 'https://via.placeholder.com/300x450',
                'imdbID': movie.id,
                'Year': str(movie.year) if movie.year else ""
            })
            
    return JsonResponse({'results': results})

def get_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = set()

    if len(query) >= 2:
        # Get matching metadata for quick selection
        suggestions.update(Movie.objects.filter(director__icontains=query).values_list('director', flat=True)[:2])
        suggestions.update(Cast.objects.filter(real_name__icontains=query).values_list('real_name', flat=True)[:2])
        suggestions.update(Genre.objects.filter(name__icontains=query).values_list('name', flat=True)[:2])
        
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

@login_required
def profile_view(request):
    user_profile = request.user.profile
    subscription = Subscription.objects.filter(user=request.user, active=True).first()
    
    context = {
        'user': request.user,
        'is_subscribed': user_profile.is_subscribed,
        'subscription': subscription,
        'mobile': user_profile.mobile,
    }
    return render(request, 'profile.html', context)


def subscription(request):
    return render(request, 'subscription.html')


def payment_page(request, plan_name):
    plan_map = {
        'basic': {'name': 'Basic', 'price': 599},
        'standard': {'name': 'Standard', 'price': 1599},
        'premium': {'name': 'Premium', 'price': 1999},
        'pro': {'name': 'Pro', 'price': 19999},
    }

    selected_plan = plan_map.get(plan_name.lower(), plan_map['basic'])
    amount_in_paise = selected_plan['price'] * 100
    
    request.session['selected_plan_name'] = selected_plan['name']
    request.session['selected_plan_price'] = f"{selected_plan['price']}.00"

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"receipt_{plan_name}_{request.user.id}",
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
        
        plan_name = request.session.get('selected_plan_name', 'Standard').lower()
        amount = request.session.get('selected_plan_price', '1599.00')
        
        if plan_name == 'pro':
            expiry = timezone.now() + datetime.timedelta(days=365)
            billing_type = 'Yearly'
        else:
            expiry = timezone.now() + datetime.timedelta(days=30)
            billing_type = 'Monthly'

        sub, created = Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan_name': plan_name,
                'order_id': params_dict['razorpay_order_id'],
                'payment_id': params_dict['razorpay_payment_id'],
                'active': True,
                'expiry_date': expiry
            }
        )

        user_profile = request.user.profile
        user_profile.is_subscribed = True
        user_profile.save()

        context = {
            'payment_id': params_dict['razorpay_payment_id'],
            'plan_name': plan_name.capitalize() + " plan",
            'amount': amount,
            'billing_type': billing_type,
            'next_payment': expiry.strftime('%b %d, %Y')
        }
        
        return render(request, 'payment_success.html', context)

    except razorpay.errors.SignatureVerificationError:
        return render(request, 'payment_failed.html')

