"""
This file changes how py.test runs collected tests. The class docstring is prepended to the
tests's docstring and printed nicely with the standard pytest strings.

e.g.

Base route '/' should have the application name in the body. <- tests/test_index_page.py PASSED
Base route '/' should have JSON encoded body. <- tests/test_index_page.py PASSED
"""


def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    suf = suf[0].lower() + suf[1:]
    if pref or suf:
        item._nodeid = ' '.join((pref, suf))
