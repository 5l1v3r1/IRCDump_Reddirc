# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from datetime import datetime, timedelta
from django.utils import timezone

from django.db import models
from IrcDump.models import Link, Voter
from django.db.models import Q

from decimal import Decimal
import re

# index pagina, waar alles gebeurd
def index(request):
	return render(request, 'ircdump/index.html')
	
	
# http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:	ip = x_forwarded_for.split(',')[0]
	else:	ip = request.META.get('REMOTE_ADDR')
	return ip

# pak entries
def entries(request):
	context = {}

	# search
	if request.method == 'GET' and 's' in request.GET:
		entry_query = get_query(request.GET['s'], ['description', 'tags',])
		pop_links = Link.objects.filter(entry_query).order_by('-rating')
		title_results = 'Search Results'
	
	# archive
	elif request.method == 'GET' and 'a' in request.GET:
		pop_links = Link.objects.all().order_by('-date')
		title_results = 'Archive'
	
	# default pagina (populair)
	else:
		pop_links = Link.objects.all().order_by('-rating')
		title_results = 'Populair'
		
	# aantal results
	default_list_size = 16
	next_results = default_list_size
	if request.method == 'GET' and 'f' in request.GET:
		try:
			fromi = int(request.GET['f'])
			if fromi < len(pop_links)+1 and fromi > 0:
				next_results = fromi + default_list_size
		except:
			pass

	# context
	context ['pop_links'] = pop_links[next_results - default_list_size:next_results]
	context ['title_results'] = title_results
	if next_results < len(pop_links)+1:
		context ['next_results'] = next_results
	if next_results > default_list_size:
		context ['prev_results'] = next_results - (default_list_size * 2)
		
	return render(request, 'ircdump/entries.html', context)


# get content for id
def content(request, link_id):
	try:
		selected_choice = get_object_or_404(Link, pk=link_id)
	except (KeyError, Link.DoesNotExist):
		return HttpResponse("0")
		
	context = { 'selected' : selected_choice, }
		
	return render(request, 'ircdump/content.html', context)
	

# search
# http://julienphalip.com/post/2825034077/adding-search-to-a-django-site-in-a-snap
def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):
	return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 
def get_query(query_string, search_fields):
	query = None # Query to search for every search term        
	terms = normalize_query(query_string)
	for term in terms:
		or_query = None # Query to search for a given term in each field
		for field_name in search_fields:
			q = Q(**{"%s__icontains" % field_name: term})
			if or_query is None:	or_query = q
			else:	or_query = or_query | q
		if query is None:	query = or_query
		else:	query = query & or_query
	return query	

	
# rate een link
# als iemand stemt, wordt de vorige vote verwijderd
# dan dilute de vote over (1 / votes) naar de vorige link + de huidige
# na vier dagen horen de votes gereset te worden

# dit systeem faalt nog: user kan steeds blijven voten. vote wordt wel steeds minder waard.
# wat ook kan: steeds vorige votepoints / 2, maar dat is een saai systeem
def rate(request, link_id, updown):
	# get link
	try:
		selected_choice = get_object_or_404(Link, pk=link_id)
	except (KeyError, Comment.DoesNotExist):
		return HttpResponse("0")
	
	# http://stackoverflow.com/questions/10337670/update-existing-record-or-creating-new
	# get user profile, or create new
	addr = get_client_ip(request)
	try:
		userprofile = Voter.objects.get(ip=addr)
		# reset vote profile is first vote is older than 4 days
		if datetime.now().replace(tzinfo=timezone.utc) >= userprofile.votedate:
			userprofile.votes = 1
			userprofile.votedate = (datetime.now() + timedelta(days=4)).replace(tzinfo=timezone.utc)
		# no voting on the same link twice in a row, or more than 20 votes
		if int(userprofile.lastlink) == int(link_id) or userprofile.votes > 20:
			return HttpResponse("0")
		# remove old vote, add diluted vote
		else:
			past_choice = Link.objects.get(pk=userprofile.lastlink)
			if userprofile.lastdo == '+':
				past_choice.rating -= Decimal(1/userprofile.votes)
				past_choice.rating += Decimal(1/(userprofile.votes+1))
			if userprofile.lastdo == '-':
				past_choice.rating += Decimal(1/userprofile.votes)
				past_choice.rating -= Decimal(1/(userprofile.votes+1))
			past_choice.save()
	except:
		userprofile = Voter(ip=addr, votes=0, lastlink=link_id, votedate=(datetime.now() + timedelta(days=4)).replace(tzinfo=timezone.utc))
		
	# change rating new link
	userprofile.votes += 1
	votepoints = Decimal(1/userprofile.votes)

	if updown == '+':	selected_choice.rating += votepoints
	if updown == '-':	selected_choice.rating -= votepoints
	
	userprofile.lastdo=updown
	userprofile.lastlink =  link_id
	userprofile.save()
	selected_choice.save()
	return HttpResponse(str(selected_choice.rating))

