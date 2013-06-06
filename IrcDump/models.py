from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# een url naar iets
class Link(models.Model):
	#title = models.CharField(max_length=200)
	url = models.CharField(max_length=200)
	user = models.CharField(max_length=200)
	description = models.CharField(max_length=200)
	rating = models.DecimalField(max_digits=5, decimal_places=2)
	tags = models.CharField(max_length=200)
	thumburl = models.CharField(max_length=200)
	date = models.DateTimeField('date published')
	def __str__(self):
		return self.url

# iemand die stemt
class Voter(models.Model):
	ip = models.CharField(max_length=200, unique=True)
	votes = models.IntegerField(default=0)
	lastlink = models.IntegerField(default=0)
	lastdo = models.CharField(max_length=5)
	votedate = models.DateTimeField('first vote')
	def __str__(self):
		return self.ip