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
        self._useCache = self._settings.value( "albumSelector/usecache", True )
        self._albumData = []
        self._curAlbum = 0

        lastAlbumName = self._userData.value( "albumSelector/last", "" )

        for albumName in self._audioLibrary.getAlbumList():
            if lastAlbumName == albumName:
                print( "select album" )
                self._curAlbum = len( self._albumData )
            self._albumData.append( { "name": albumName, "image": None, "image_error": False } )

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

        self._curPlay = None
        self._timer = QTimer()
        self._timer.setInterval( 10000 )
        self._timer.timeout.connect( self._handleTimer )

        self._mousePressPos = None



    def getImage( self, albumData ):
        """Return image of an ablbum. Either take image from cache, if image is
        not available in cache try to load from disc"""
        res = None
        if albumData["image"] is None and not albumData["image_error"]:
            imageSource = self._audioLibrary.getAlbumImageFilename( albumData["name"] )
            if imageSource is not None:
                logging.info( "Load image {} for album {}".format( imageSource, albumData["name"] ) )
                print( "Load image {} for album {}".format( imageSource, albumData["name"] ) )
                try:
                    p = QPixmap()
                    if p.load( imageSource ):
                        res = p
                        if self._useCache == True:
                            albumData["image"] = p
                except Exception as e:
                    print( "Could not load image from {}: {}".format( imageSource ).format(e) )
                    logging.error( "Could not load image from {}".format( imageSource ) )
            albumData["image_error"] = self._useCache == True and albumData["image"] is None
        else:
            res = albumData["image"]
        return res

    def loadImages( self ):        
        """Build up internal database with images from audio library"""
        return
        for albumData in self._albumData:
            self.getImage( albumData )


    def showAlbum( self ):
        albumData = self._albumData[self._curAlbum]
        print( "show album: " + str( albumData ) )
        self.clear()
        image = self.getImage( albumData )
        if image is not None:
            self.setPixmap( image.scaled( self.size(), Qt.KeepAspectRatio ) )
        else:
            self.setText( albumData["name"] )


    def nextAlbum( self ):
        self._curAlbum = self._curAlbum + 1
        if self._curAlbum >= len( self._albumData ):
            self._curAlbum = 0
        self.showAlbum()
        self._timer.start()


    def previousAlbum( self ):
        self._curAlbum = self._curAlbum - 1
        if self._curAlbum < 0:
            self._curAlbum = len( self._albumData ) - 1
        self.showAlbum()
        self._timer.start()


    def selectAlbum( self ):
        albumName = self._albumData[self._curAlbum]
        print( "Album selected: " + str( albumName ) )
        self.playAlbumSignal.emit( albumName["name"] )
        self._userData.setValue( "albumSelector/last", albumName["name"] )
        self._curPlay = self._curAlbum


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


    @pyqtSlot()
    def _handleTimer( self ):
        if self._curPlay is not None:
            self._curAlbum = self._curPlay
            self.showAlbum()
        self._timer.stop()


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


