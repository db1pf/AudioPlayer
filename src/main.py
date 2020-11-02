#!/bin/python3
# 
# Copyright Florian Pfanner 2020
#
# This file is part of AudioPlayer.
# 
# AudioPlayer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# AudioPlayer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with AudioPlayer. If not, see <https://www.gnu.org/licenses/>.
# 
# 



from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
import sys
import time

import CAudioLibrary
import CMainWindow



if __name__ == "__main__":

    QCoreApplication.setOrganizationName( "Pfanner" )
    QCoreApplication.setApplicationName( "AudioPlayer" )

    app = QApplication( sys.argv )

    while True:
        try:
            g = CMainWindow.CMainWindow( "-d" not in sys.argv )
            g.show()

            sys.exit( app.exec_() )
        except Exception as e:
            print( "Exception: " + str( e ) )
        time.sleep( 5 )

