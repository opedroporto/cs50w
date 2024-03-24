import numpy as np

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.db.models import Max, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from commerce import settings
from .models import Auction, Bid, Category, Comment, User, Watchlist

class AuctionForm(forms.ModelForm):
    minimum_bid = forms.DecimalField(max_value=1000000, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Auction
        fields = ["name", "description", "category", "minimum_bid", "image_url"]
        labels = {
            'name': 'Item name',
            'description': 'Item description',
            'category': 'Category',
            'minimum_bid': 'Minimum bid',
            'image_url': 'Image',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image_url': forms.FileInput(attrs={'class': 'form-control-file'}),
        }


class BidForm(forms.ModelForm):
    bid = forms.DecimalField(label='', decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bid'}))
    class Meta:
        model = Bid
        fields = ["bid"]


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = []


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment"]
        labels = {
            'comment': ''
        }
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': '2', 'placeholder': 'Add comment'}),
        }


def index(request):
    auctions = Auction.objects.order_by('-modified_at').all()
    for auction in auctions:
        auction.price = np.maximum(Bid.objects.filter(auction=auction).aggregate(max_bid=Max('bid'))['max_bid'] or auction.minimum_bid, auction.minimum_bid)
        
    return render(request, "auctions/index.html", {
        "auctions": auctions
    })


def categories(request):
    # categories = Category.objects.prefetch_related(Prefetch('auction_set', queryset=Auction.objects.all()))
    categories = Category.objects.order_by('-modified_at').all()
    for category in categories:
        newest_auction = category.auction_set.all().order_by('-created_at').first()
        if newest_auction and newest_auction.image_url:
            category.image_url = settings.BASE_URL + newest_auction.image_url.url
            
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category(request, id):
    category = Category.objects.get(id=id)
    auctions = Auction.objects.order_by('-modified_at').filter(category=category).all()
    for auction in auctions:
        auction.price = np.maximum(Bid.objects.filter(auction=auction).aggregate(max_bid=Max('bid'))['max_bid'] or auction.minimum_bid, auction.minimum_bid)
        auction.image_url = settings.BASE_URL + auction.image_url.url
            
    return render(request, "auctions/category.html", {
        "category": category,
        "auctions": auctions,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def auction(request, id):
    auction = Auction.objects.annotate(
        bids_amount=Count('bid__bid')
    ).get(id=id)
    current_bid = Bid.objects.filter(auction=auction).select_related('user').order_by('-bid').first()
    auction.price = np.maximum(current_bid.bid if current_bid else auction.minimum_bid, auction.minimum_bid)
    auction.image_url = settings.BASE_URL + auction.image_url.url
    if request.user.is_authenticated:
        auction.watchlist = Watchlist.objects.filter(user=request.user, auction=auction)

    if (request.user.is_authenticated and current_bid):
        user_has_current_bid = current_bid.user == request.user
    else:
        user_has_current_bid = False

    if request.user.is_authenticated:
        created_by_user = auction.user == request.user
    else:
        created_by_user = False

    try:
        comments = list(Comment.objects.filter(auction=auction))
    except Comment.DoesNotExist:
        comments = []

    

    return render(request, "auctions/auction.html", {
        "auction": auction,
        "user_has_current_bid": user_has_current_bid,
        "created_by_user": created_by_user,
        "comments": comments,
        "place_bid_form": BidForm(),
        "comment_form": CommentForm()
    })

@login_required
def create(request):
    if (request.method == "GET"):
        form = AuctionForm()
        return render(request, "auctions/create.html", {
            "form": form
        })
    elif (request.method == "POST"):
        form = AuctionForm(request.POST, request.FILES)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.user = request.user
            auction.save()
            return redirect('index')
        return render(request, "auctions/create.html", {
            "form": form
        })
    

@login_required
def auction_placebid(request, id):
    if request.method == "POST" and request.POST['bid']:
        place_bid_form = BidForm(request.POST)
        if place_bid_form.is_valid():
            # validate bid
            user_bid = float(request.POST['bid'])
            auction = Auction.objects.get(id=id)
            current_bid = Bid.objects.filter(auction=auction).aggregate(max_bid=Max('bid'))['max_bid'] or 0
            if (user_bid <= current_bid or user_bid < auction.minimum_bid):
                messages.error(request, f'The bid must be greater than the highest bid and at least as large as the starting bid!',  extra_tags='place_bid_error')
                return redirect(f"{reverse('auction', kwargs={'id': id})}#bid")

            bid = place_bid_form.save(commit=False)
            bid.auction = auction   
            bid.user = request.user
            bid.save()
    return redirect('auction', id=id)


@login_required
def auction_close(request, id):
    if request.method == "POST":
        try:
            Auction.objects.filter(id=id, user=request.user, closed=False).update(closed=True)
        except:
            pass
        return redirect("index")
    

@login_required
def auction_comment(request, id):
    if request.method == "POST" and request.POST['comment']:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            try:
                comment.auction = Auction.objects.get(id=id, closed=False)
                comment.save()
            except:
                pass
        return redirect("auction", id=id)


@login_required
def watchlist(request):
    watchlists = Watchlist.objects.order_by('-modified_at').filter(user=request.user).select_related('auction').all()
    auctions = []
    for watchlist in watchlists:
        auctions.append(watchlist.auction)
    for auction in auctions:
        auction.price = np.maximum(Bid.objects.filter(auction=auction).aggregate(max_bid=Max('bid'))['max_bid'] or auction.minimum_bid, auction.minimum_bid)
        
    return render(request, "auctions/watchlist.html", {
        "auctions": auctions
    })


@login_required
def watchlist_add(request):
    if request.method == "POST" and request.POST['id']:
        form = WatchlistForm(request.POST)
        if form.is_valid():
            watchlist = form.save(commit=False)
            watchlist.user = request.user
            try:
                watchlist.auction = Auction.objects.get(id=request.POST['id'])
                watchlist.save()
            except:
                pass
        return redirect("auction", id=request.POST['id'])


@login_required
def watchlist_remove(request):
    if request.method == "POST" and request.POST['id']:
        try:
            Watchlist.objects.filter(auction=Auction.objects.get(id=request.POST['id']), user=request.user).delete()
        except:
            pass
        return redirect("auction", id=request.POST['id'])