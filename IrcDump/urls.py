from django.conf.urls import patterns, url
from django.views.generic.base import TemplateView

from IrcDump import views

class TextPlainView(TemplateView):
  def render_to_response(self, context, **kwargs):
    return super(TextPlainView, self).render_to_response(context, content_type='text/plain', **kwargs)

	
urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	

	url(r'^(?P<link_id>\d+)/rate/(?P<updown>[+-])', views.rate, name='rate'),
	
	url(r'^(?P<link_id>\d+)/content', views.content, name='content'),
	
	url(r'^entries/', views.entries, name='entries'),
	
	
	url(r'^robots\.txt$', TextPlainView.as_view(template_name='robots.txt')),
)