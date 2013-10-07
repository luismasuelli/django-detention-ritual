from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
import views

urlpatterns = patterns('',
    # url(r'^$', 'DjailsSampleProject.views.home', name='home'),
    # url(r'^djails/', include('example.urls')),
    #FIXME put all test urls here.
    url('^banned/$', views.banned_view, name='banned-target'),
    url('^noauth/$', views.noauth_view, name='noauth-target'),

    url('^view1/$', views.view1, name='view-1'),
    url('^view2/$', views.view2, name='view-2'),
    url('^view3/$', views.view3, name='view-3'),

    url('^$', lambda req: redirect(reverse('profile')),
              name="main"),
    url('^login/$', 'django.contrib.auth.views.login',
                    {'template_name': 'example/login.html'},
                    name="login"),
    url('^logout/$', 'django.contrib.auth.views.logout',
                     {'template_name': 'example/logout.html'},
                     name="logout"),
    url('^profile/$', views.profile,
                      name='profile')
)