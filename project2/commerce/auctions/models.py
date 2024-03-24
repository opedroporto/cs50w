from django.contrib.auth.models import AbstractUser
from django.db import models


class BaseModel(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(BaseModel, AbstractUser):
    pass

class Category(BaseModel):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class Auction(BaseModel):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    minimum_bid = models.FloatField()
    image_url = models.ImageField(upload_to='uploads/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    closed = models.BooleanField(default=False)

class Bid(BaseModel):
    bid = models.FloatField()
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Comment(BaseModel):
    comment = models.CharField(max_length=255)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Watchlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user','auction'),)