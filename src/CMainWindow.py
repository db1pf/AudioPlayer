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



from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QTimer
import logging
import os


import CAudioLibrary
import CGuiAudioPlayer
import CGuiAlbumSelector


fileDirName = os.path.dirname( os.path.abspath(__file__) )


class CMainWindow( QWidget ):

    def __init__( self, fullScreen=True, parent=None ):
        super().__init__( parent )

        self._settings = QSettings( os.path.join( fileDirName, "../settings/settings.ini" ), QSettings.IniFormat )
        self._userData = QSettings()

        self._audioLibrary = CAudioLibrary.CAudioLibrary( self._settings.value( "library/dirs" ),
                                                          self._settings.value( "library/audioExtension", [ ".mp3" ] ),
                                                          self._settings.value( "library/imageExtension", [ ".png", ".jpg" ] ) )

        self._player = CGuiAudioPlayer.CGuiAudioPlayer( self._audioLibrary, self._settings, self._userData )
        self._selector = CGuiAlbumSelector.CGuiAlbumSelector( self._audioLibrary, self._settings, self._userData )

        mainLayout = QVBoxLayout()
        mainLayout.addWidget( self._selector, 100 )
        mainLayout.addWidget( self._player, 1 )
        self.setLayout( mainLayout )

        self._selector.loadImages()
        self._selector.showAlbum()

        self._selector.playAlbumSignal.connect( self._player.playAlbum )

        self._selector.setFocus()

        if fullScreen:
            self.setWindowFlags( Qt.CustomizeWindowHint | Qt.FramelessWindowHint )
            self.setWindowState( Qt.WindowFullScreen )
            self.showFullScreen()
            self.setCursor( Qt.BlankCursor )
            screens = QGuiApplication.screens()
            self.move( screens[0].geometry().topLeft() )
            self.resize( screens[0].geometry().size() )
            self.setFixedSize( screens[0].geometry().size() )
        else:
            self.resize( 500, 400 )
            self.setFixedSize( QSize( 500, 400 ) )

        self._timer = QTimer()
        self._timer.setInterval( 60000 )
        self._timer.timeout.connect( self._handleTimer )
        self._timer.start()


    def keyPressEvent( self, event ):
        if event.key() == Qt.Key_Escape:
            self._userData.sync()
            self.close()
            event.accept()
        else:
            super().keyPressEvent( event )


    @pyqtSlot()
    def _handleTimer( self ):
        self._userData.sync()


