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


from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.Qt import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QSize
import logging



class CGuiAlbumSelector( QLabel ):

    playAlbumSignal = pyqtSignal( str )

    def __init__( self, audioLibrary, settings, userData, parent=None ):
        super().__init__( parent )

        self._audioLibrary = audioLibrary
        self._settings = settings
        self._userData = userData

        self._curAlbumName = self._userData.value( "albumSelector/last", "" )
        self._curAlbum = None

        # setup UI
        self.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
        self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Minimum )
        self.setMinimumSize( QSize( 20, 20 ) )
        self.setWordWrap( True )
        font = self.font()
        font.setPointSize( int( self._settings.value( "albumSelector/fontSize", 20 ) ) )
        self.setFont( font )
        self.setFocusPolicy( Qt.StrongFocus )

        self.showAlbum()

        self._audioLibrary.contentChanged.connect( self.showAlbum )             # in case cache has changed also update my image

        self._curPlayName = None
        self._timer = QTimer()
        self._timer.setInterval( 10000 )
        self._timer.timeout.connect( self._handleTimer )

        self._mousePressPos = None


    def showAlbum( self ):
        logging.info( "Show album {}".format( self._curAlbumName ) )
        self._curAlbum = self._audioLibrary.getAlbum( self._curAlbumName )
        if self._curAlbum is None:
            self._curAlbumName = self._audioLibrary.getNextAlbum( "" )      # use first one
            self._curAlbum = self._audioLibrary.getAlbum( self._curAlbumName )
            logging.info( "Album not found, use first one {}".format( self._curAlbumName ) )

        self.clear()
        image = self._curAlbum.getImage( 0, self.size() )
        if image is not None:
            self.setPixmap( image.scaled( self.size(), Qt.KeepAspectRatio ) )
        else:
            self.setText( self._curAlbum.getDisplayName() )


    def nextAlbum( self ):
        self._curAlbumName = self._audioLibrary.getNextAlbum( self._curAlbumName )
        self.showAlbum()
        self._timer.start()


    def previousAlbum( self ):
        self._curAlbumName = self._audioLibrary.getPrevAlbum( self._curAlbumName )
        self.showAlbum()
        self._timer.start()


    def selectAlbum( self ):
        print( "Album selected: {}".format( self._curAlbumName ) )
        self.playAlbumSignal.emit( self._curAlbumName )
        self._userData.setValue( "albumSelector/last", self._curAlbumName )
        self._curPlayName = self._curAlbumName


    def resizeEvent( self, event ):
        super().resizeEvent( event )
        self.showAlbum()


    def mousePressEvent( self, event ):
        self._mousePressPos = [ event.x(), event.y() ]
        event.accept()
        super().mousePressEvent( event )


    def mouseReleaseEvent( self, event ):
        if self._mousePressPos is not None:
            event.accept()
            dx = event.x() - self._mousePressPos[0]
            dy = event.y() - self._mousePressPos[1]

            if abs( abs( dx ) - abs( dy ) ) > 20:       # min 20 px move
                if abs( dx ) > abs( dy ):
                    # horizontal move
                    if dx > 0:
                        self.previousAlbum()
                    else:
                        self.nextAlbum()
                else:
                    # vertical move
                    if dy > 0:
                        self.selectAlbum()
        self._mousePressPos = None
        super().mouseReleaseEvent( event )


    def _handleTimer( self ):
        if self._curPlayName is not None:
            # reset selector to album currently playing
            self._curAlbumName = self._curPlayName
            self.showAlbum()
        self._timer.stop()


    def jumpAlbum( self, albumName ):
        """Jump to given album and just show it
        """
        logging.debug( "Jump to album {}".format( albumName ) )
        self._curAlbumName = albumName
        self.showAlbum()
        self._timer.start()


    def keyPressEvent( self, event ):
        if event.key() == Qt.Key_Right:
            event.accept()
            self.nextAlbum()
        elif event.key() == Qt.Key_Left:
            event.accept()
            self.previousAlbum()
        elif event.key() == Qt.Key_Down or event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            event.accept()
            self.selectAlbum()
        else:
            super().keyPressEvent( event )


