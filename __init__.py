# -*- coding: utf-8 -*-

__author__ = 'gwolf'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by gwolf'


def classFactory(iface):
    from .snapper import Snapper
    return Snapper(iface)
