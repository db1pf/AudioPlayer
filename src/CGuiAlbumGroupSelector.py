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
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import QAbstractListModel
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




class CDateModel( QAbstractListModel ):
    def __init__( self, audioLibrary, settings, userData, iconSize, parent=None):
        super().__init__( parent )
        self._audioLibrary = audioLibrary
        self._settings = settings
        self._userData = userData
        self._iconSize = iconSize

        self._albumList = self._audioLibrary.getAlbumList( "date" )
        self._maxItems = settings.value( "dateModel/numItems", 20 )
        self._albumList = self._albumList[-self._maxItems:]


    def rowCount( self, parent ):
        return len( self._albumList )


    def data( self, index, role ):
        if index.isValid() and index.row() < len( self._albumList):
            if role == Qt.UserRole:
                return self._albumList[index.row()]
            if role == Qt.DecorationRole:
                album = self._audioLibrary.getAlbum( self._albumList[index.row()] )
                img = album.getImage( 0, self._iconSize )
                if img is not None:
                    return QIcon( img )
                else:
                    return QVariant()
        return QVariant()







class CGuiAlbumGroupSelector( QWidget ):

    jumpAlbum = pyqtSignal( str )

    def __init__( self, audioLibrary, settings, userData, parent=None ):
        super().__init__( parent )

        self._audioLibrary = audioLibrary
        self._settings = settings
        self._userData = userData

        # setup UI
        self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Minimum )
        self.setMinimumSize( QSize( int( self._settings.value( "albumSelectorGroup/width", 200 ) ), 20 ) )

        iconSize = QSize( 150, 150 )

        self._view = QListView( self )
        self._view.setViewMode( QListView.IconMode )
        self._view.setIconSize( iconSize );

        self._dateModel = CDateModel( audioLibrary, settings, userData, iconSize )
        self._view.setModel( self._dateModel )

        mainLayout = QVBoxLayout()
        mainLayout.addWidget( self._view )
        self.setLayout( mainLayout )




    @pyqtSlot()
    def entrySelected( self, albumName ):
        """Jump to given album and just show it
        """
        logging.debug( "Jump to album {}".format( albumName ) )




