#!/bin/python3
# 
# Copyright Florian Pfanner 2023
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
from PyQt5.QtWidgets import QListView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import QAbstractListModel
from PyQt5.QtCore import QModelIndex
from PyQt5.Qt import QPixmap
from PyQt5.Qt import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QVariant
import logging
import os


class CDataModel( QAbstractListModel ):
    def __init__( self, audioLibrary, iconSize, dataType, maxNumItems=None, reverse=False, parent=None):
        super().__init__( parent )
        self._audioLibrary = audioLibrary
        self._iconSize = iconSize
        self._dataType = dataType
        self._maxNumItems = maxNumItems
        self._reverse = reverse
        self._albumList = []
        audioLibrary.contentChanged.connect( self._reloadContent )

        self._reloadContent()


    def rowCount( self, parent ):
        return len( self._albumList )


    def data( self, index, role ):
        if index.isValid() and index.row() < len( self._albumList):
            albumName = self._albumList[index.row()]
            if role == Qt.UserRole:
                return albumName
            if role == Qt.DecorationRole:
                if albumName not in self._iconData:
                    album = self._audioLibrary.getAlbum( albumName )
                    img = album.getImage( 0, self._iconSize )
                    if img is not None:
                        img = QIcon( img )
                    self._iconData[albumName] = img

                res = self._iconData[albumName]
                if res is not None:
                    return res
                else:
                    return QVariant()
        return QVariant()


    def _reloadContent( self ):
        logging.debug( "Reload content of {} CDataModel".format( self._dataType ) )
        self.layoutAboutToBeChanged.emit()

        self._albumList = self._audioLibrary.getAlbumList( self._dataType )
        if self._reverse:
            self._albumList.reverse()
        if self._maxNumItems is not None:
            self._albumList = self._albumList[0:self._maxNumItems]
        self._iconData = {}

        self.layoutChanged.emit()




class CGuiAlbumGroupSelector( QWidget ):

    jumpAlbum = pyqtSignal( str )

    def __init__( self, audioLibrary, settings, userData, parent=None ):
        super().__init__( parent )

        self._audioLibrary = audioLibrary
        self._settings = settings
        self._userData = userData

        # setup UI
        widgetWidth = int( self._settings.value( "albumSelectorGroup/width", 200 ) )
        buttonSize = self._settings.value( "albumSelectorGroup/buttonSize", QSize( 30, 30 ) )
        pictureWidth = int( self._settings.value( "albumSelectorGroup/pictureWidth", ( widgetWidth - 50 ) / 2 ) )
        iconSize = QSize( pictureWidth, pictureWidth )

        self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Minimum )
        self.setMinimumSize( QSize( widgetWidth, 20 ) )

        self._view = QListView( None )
        self._view.setViewMode( QListView.IconMode )
        self._view.setIconSize( iconSize );
        self._view.setSelectionMode( QAbstractItemView.NoSelection )
        self._view.setAttribute( Qt.WA_TransparentForMouseEvents )
        self._view.verticalScrollBar().hide()
        self._view.horizontalScrollBar().hide()
        palette = self._view.palette()
        palette.setColor( QPalette.Base, palette.color( QPalette.Window ) )
        self._view.setPalette( palette )
        self._view.setFrameShape( QFrame.NoFrame )

        # create model
        dateListMaxItems = int( self._settings.value( "albumSelectorGroup/dateListNumItems", 20 ) )
        self._model = {}
        self._model["date"] = CDataModel( audioLibrary, iconSize, "date", dateListMaxItems, True )
        self._model["dir"] = CDataModel( audioLibrary, iconSize, "dir" )

        buttonLayout = QHBoxLayout()
        self.__buttons = [ #icon filename, modelName, slot, buttonObj
                          [ "folder.png", "dir", self._dirButtonClicked, None ],
                          [ "calendar.png", "date", self._dateButtonClicked, None ],
                         ]

        for buttonData in self.__buttons:
            button = QPushButton()
            button.setFlat( True )
            button.setMinimumSize( buttonSize )
            ico = QIcon()
            ico.addFile( os.path.join( os.path.dirname( os.path.abspath(__file__) ), "../images", buttonData[0] ), buttonSize )
            button.setIcon( ico )
            button.setIconSize( buttonSize )
            button.clicked.connect( buttonData[2] )
            buttonData[3] = button
            buttonLayout.addWidget( button )
        self.__buttons[0][3].click()

        # create layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout( buttonLayout )
        mainLayout.addWidget( self._view )
        self.setLayout( mainLayout )

        self._clickStart = None
        self._clickPos = None


    def mouseReleaseEvent( self, event ):
        """Mouse press releases. Check if move was below threshold. If yes it
        was a click on an item thus select item under cursor.
        """
        if self._clickStart:
            dist = event.pos().y() - self._clickStart.y()
            if abs( dist ) < 10:
                posObj = self._view.mapFrom( self, event.pos() )
                idx = self._view.indexAt( posObj )
                albumName = self._view.model().data( idx, Qt.UserRole )
                if idx.isValid() and isinstance( albumName, str ):
                    logging.debug( "Album selected {}".format( albumName ) )
                    self.jumpAlbum.emit( albumName )
        self._clickStart = None


    def mousePressEvent( self, event ):
        """Click in window. Remember click position
        """
        self._clickPos = event.pos()
        self._clickStart = event.pos()


    def mouseMoveEvent( self, event ):
        """Mouse moved, move scrollbar in same manner
        """
        if self._clickPos is None:
            self._clickPos = event.pos()
        dist = event.pos().y() - self._clickPos.y()
        sb = self._view.verticalScrollBar()
        sb.setValue( max( sb.minimum(), min( sb.maximum(), sb.value() - dist ) ) )
        self._clickPos = event.pos()


    def _dirButtonClicked( self ):
        self._buttonClicked( "dir" )


    def _dateButtonClicked( self ):
        self._buttonClicked( "date" )


    def _buttonClicked( self, dataType ):
        """Selector button was clicked, switch model if necessary
        """
        self._view.setModel( self._model[dataType] )
        self._view.verticalScrollBar().setValue( 0 )


