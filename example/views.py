# Create your views here.
from djails import decorators


def anonymous(request, view, *args, **kwargs):
    """
    The anonymous callback function must be accepted as the parameter.
    """
    pass


def content(request, function, current_ban, *args, **kwargs):
    """
    This content function must accept kwargs or current_ban, or both.
    This content must have a second positional parameter (the intercepted view).
    """
    return {'content': '<html><head>You suck</head><body>You really suck!</body></html>', 'content_type': 'text/html'}


def redirected(request):
    """
    This content is independant.
    """
    pass


def chained(request, func, current_ban, *args, **kwargs):
    """
    This chained view must accept the request and a current_ban named parameter.
    This content must have a second positional parameter (the intercepted view).
    """
    return func(request, current_ban)


@decorators.ifban_forbid(content_func=content)
def test_forbid(request):
    pass


@decorators.ifban_forbid(content_func=content, on_anonymous=anonymous)
def test_forbid_anon(request):
    pass


@decorators.ifban_chain(target_view=chained)
def test_chain(request, c_ban=None):
    pass


@decorators.ifban_chain(target_view=chained, on_anonymous=anonymous)
def test_chain_anon(request, c_ban=None):
    pass


@decorators.ifban_redirect(target='redirect')
def test_chain_redirect(request):
    pass


@decorators.ifban_redirect(target='redirect', on_anonymous=anonymous)
def test_chain_redirect(request):
    pass