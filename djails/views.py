# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext


def test_template(request, template, dictionary):
    return render_to_response(template, dictionary, RequestContext(request))