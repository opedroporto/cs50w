from auctions.models import Watchlist

def watchlist_context(request):
    watchlist_count = 0
    if request.user.is_authenticated:
        watchlist_count = Watchlist.objects.filter(user=request.user).count()
    return {'watchlist_count': watchlist_count}