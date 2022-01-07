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


import os
import sys
import logging

from PyQt5.QtCore import QObject


# self._album:
#    {name} = { "path": "abs/path/to/album",
#               "image": "image rel to path",
#               "files": [ "media files rel to path" ] }
#



class CAudioLibrary( QObject ):

    def __init__( self, directoryList, audioExtensions=[".mp3"], imageExtensions=[".png", ".jpg"], parent=None, splash=None ):
        super().__init__( parent )

        if isinstance( directoryList, str ):
            directoryList = [ directoryList ]
        if isinstance( audioExtensions, str ):
            audioExtensions = [ audioExtensions ]
        if isinstance( imageExtensions, str ):
            imageExtensions = [ imageExtensions ]

        print( "CAudioLibrary: {}, {}, {}".format( directoryList, audioExtensions, imageExtensions ) )

        self._audioExtensions = audioExtensions
        self._imageExtensions = imageExtensions
        self._album = {}

        for directory in directoryList:
            self.__searchPath( directory, "", splash )


    def __delete__( self ):
        pass


    def getAlbumList( self ):
        """Return a list with the name of all known albums. The list is already sorted"""
        ret = list( self._album.keys() )
        ret.sort()
        return ret


    def getAlbumImageFilename( self, albumName, absolutePath=True ):
        """Return path to image file of given album. If album is unknown, an exception
        is thrown. If no image is available, None is returned."""
        if albumName not in self._album:
            raise Exception( "Unknown album name: {}".format( albumName ) )
        albumEntry = self._album[albumName]
        if absolutePath and albumEntry["image"] is not None:
            return os.path.join( albumEntry["path"], albumEntry["image"] )
        else:
            return albumEntry["image"]


    def getAlbumFiles( self, albumName, absolutePath=True ):
        """Return list of files of one album. The list is already sorted.
        If album is unknown, an exception is thrown."""
        if albumName not in self._album:
            raise Exception( "Unknown album name: {}".format( albumName ) )
        albumEntry = self._album[albumName]
        ret = []
        for fileName in albumEntry["files"]:
            if absolutePath:
                ret.append( os.path.join( albumEntry["path"], fileName ) )
            else:
                ret.append( fileName )
        return ret


    def __searchPath( self, directory, relPathName, splash ):
        """Searches in given directory for media files. If the directory contains a file
        covered by self._fileFilter, the directory is appended to my album list. For
        each sub directory this function is called recursive"""

        logging.info( "Search in directory {} for files".format( directory ) )
        if splash is not None:
            splash.showMessage( self.tr( "Search in directory {} for audio files" ).format( relPathName ) )

        dirAlbum = { "path": directory,
                     "image": [],
                     "files": [] }

        for entry in os.listdir( directory ):
            entryPathName = os.path.join( directory, entry )
            if not entry.startswith('.') and os.path.isfile( entryPathName ):
                logging.info( "Found file {}".format( entry ) )
                extension = os.path.splitext( entry )[1]
                if extension in self._audioExtensions:
                    dirAlbum["files"].append( entry )
                elif extension in self._imageExtensions:
                    dirAlbum["image"].append( entry )

            elif os.path.isdir( entryPathName ):
                self.__searchPath( os.path.join( directory, entry ), os.path.join( relPathName, entry ), splash )

        if len( dirAlbum["files"] ) > 0:
            dirAlbum["files"].sort()
            if len( dirAlbum["image"] ) > 0:
                dirAlbum["image"].sort()
                dirAlbum["image"] = dirAlbum["image"][0]
            else:
                dirAlbum["image"] = None
            self._album[relPathName] = dirAlbum






if __name__ == "__main__":
    if len( sys.argv ) > 1:
        a = CAudioLibrary( sys.argv[1:] )
        for album in a.getAlbumList():
            print( "Album {}".format( album ) )
            image = a.getAlbumImageFilename( album, False )
            print( "  Image: {}".format( image ) )
            for fileName in a.getAlbumFiles( album, False ):
                print( "  {}".format( fileName ) )
    else:
        raise Exception( "At least one argument has to be given" )


