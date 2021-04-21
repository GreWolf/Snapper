# -*- coding: utf-8 -*-

__author__ = 'gwolf'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by gwolf'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from PyQt5.QtGui import QIcon
from qgis.gui import QgisInterface
from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .snapper_provider import snapperProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class Snapper(object):

    def __init__(self, iface: QgisInterface) -> None:
        self.provider = None

        self.plugin_dir = os.path.dirname(__file__)
        self.main_icon = QIcon(os.path.join(self.plugin_dir, "icon.png"))

    def initProcessing(self) -> None:
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = snapperProvider(self.main_icon, self.plugin_dir)
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self) -> None:
        self.initProcessing()

    def unload(self) -> None:
        QgsApplication.processingRegistry().removeProvider(self.provider)
