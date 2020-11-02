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


import CAudioPlayer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
import logging
import os


fileDirName = os.path.dirname( os.path.abspath(__file__) )



class CGuiAudioPlayer( QWidget ):

    def __init__( self, audioLibrary, settings, userData, parent=None ):
        super().__init__( parent )
        self._audioLibrary = audioLibrary
        self._settings = settings
        self._userData = userData
        self._player = CAudioPlayer.CAudioPlayer( self._audioLibrary )

        # restore volume
        volume = float( self._userData.value( "audioPlayer/volume", 0.5 ) )
        print( "restore volume to {}".format( volume ) )
        self._player.setVolume( min( 1.0, max( 0.0, volume ) ) )

        # create UI
        self.__buttons = [ #icon file name(s), icons, slot, buttonObj
                          [ [ "play.png", "pause.png" ], [], self._handlePlay, None ],
                          [ [ "previous.png" ], [], self._handlePrevious, None ],
                          [ [ "next.png" ], [], self._handleNext, None ],
                          [ [ "volumeup.png" ], [], self._handleVolumeUp, None ],
                          [ [ "volumedown.png" ], [], self._handleVolumeDown, None ],
                         ]
        buttonSize = self._settings.value( "audioPlayer/buttonSize", QSize( 40, 40 ) )
        buttonLayout = QHBoxLayout()

        for buttonData in self.__buttons:
            # load pictures for buttons
            for imgFile in buttonData[0]:
                img = QIcon()
                buttonFile = os.path.join( fileDirName, "../images", imgFile )
                img.addFile( buttonFile, buttonSize )
                buttonData[1].append( img )

            button = QPushButton()
            button.setFlat( True )
            button.setMinimumSize( buttonSize )
            button.setIcon( buttonData[1][0] )
            button.setIconSize( buttonSize )
            button.clicked.connect( buttonData[2] )
            buttonData[3] = button
            buttonLayout.addWidget( button )
        self._shownPlayButton = 0

        self.__progress = QProgressBar()
        self.__progress.setMaximum( 1000 )
        self.__progress.setMinimum( 0 )
        self.__progress.setOrientation( Qt.Horizontal )
        self.__progress.setTextVisible( True )
        self.__progress.setFormat( "" )

        mainLayout = QVBoxLayout()
        mainLayout.addLayout( buttonLayout )
        mainLayout.addWidget( self.__progress )
        self.setLayout( mainLayout )

        self._timer = QTimer()
        self._timer.setInterval( 1000 )
        self._timer.timeout.connect( self._handleTimer )
        self._timer.start()

        self._handleTimer()


    @pyqtSlot( str )
    def playAlbum( self, albumName ):
        self._player.playAlbum( albumName )
        self._handleTimer()


    @pyqtSlot()
    def _handlePlay( self ):
        if self._shownPlayButton == 0:
            # play is shown
            self._player.play()
        else:
            # pause is shown
            self._player.pause( True )
        self._handleTimer()

    @pyqtSlot()
    def _handlePrevious( self ):
        self._player.previous()
        self._handleTimer()

    @pyqtSlot()
    def _handleNext( self ):
        self._player.next()
        self._handleTimer()

    @pyqtSlot()
    def _handleVolumeUp( self ):
        curVolume = self._player.getVolume()
        self._player.setVolume( min( 1.0, curVolume+0.05 ) )
        volume = self._player.getVolume()
        print( "set volume to {}".format( volume ) )
        self._userData.setValue( "audioPlayer/volume", volume )

    @pyqtSlot()
    def _handleVolumeDown( self ):
        curVolume = self._player.getVolume()
        self._player.setVolume( max( 0.0, curVolume-0.05 ) )
        volume = self._player.getVolume()
        print( "set volume to {}".format( volume ) )
        self._userData.setValue( "audioPlayer/volume", volume )

    @pyqtSlot()
    def _handleTimer( self ):
        if self._player.isPlaying():
            curTrack = self._player.getTrack()
            numTracks = self._player.getTrackCount()
            trackTxt = self._player.getTrackDescription()
            self.__progress.setValue( int( self._player.getPosition() * 1000 ) )
            displayTxt = "{}/{} {}".format( curTrack, numTracks, trackTxt )
            fontMetrics = QFontMetrics( self.__progress.font() )
            displayTxt = fontMetrics.elidedText( displayTxt, Qt.ElideRight, self.__progress.width() )
            self.__progress.setFormat( displayTxt )
            expectedPlaybutton = 1
        else:
            expectedPlaybutton = 0
            if not self._player.isPause():
                self.__progress.setValue( 0 )
                self.__progress.setFormat( "" )
        if expectedPlaybutton != self._shownPlayButton:
            self.__buttons[0][3].setIcon( self.__buttons[0][1][expectedPlaybutton] )
            self._shownPlayButton = expectedPlaybutton

    def mousePressEvent( self, event ):
        if self.childAt( event.pos() ) == self.__progress:
            event.accept()
            pos = self.__progress.mapFrom( self, event.pos() )
            percent = pos.x() / self.__progress.width()
            if self._player.isPlaying():
                self._player.setPosition( percent )
        else:
            super().mousePressEvent( event )



