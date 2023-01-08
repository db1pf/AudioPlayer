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
import json

from PyQt5.QtCore import QObject
from PyQt5.Qt import QPixmap



class CAudioAlbum:
    """Represents one directory with audio files and an optional image"""

    def __init__( self, directoryPath, audioLibraryObj, parentDir ):
        self._path = directoryPath
        self._libObj = audioLibraryObj
        self._parentDir = parentDir         # parent CAudioDirectory object
        self._imageFiles = []
        self._audioFiles = []
        self._directoryDate = None

        if directoryPath is not None:
            self._searchDirectory( self._libObj.getAudioExtensions(), self._libObj.getImageExtensions() )


    def _searchDirectory( self, audioExtensions, imageExtensions ):
        """Search in own path for audio files and image
        """
        logging.debug( "Search in directory {} for album files".format( self._path ) )
        for entry in os.listdir( self._path ):
            entryPathName = os.path.join( self._path, entry )
            if not entry.startswith('.') and os.path.isfile( entryPathName ):
                logging.debug( "  Found file {}".format( entry ) )
                extension = os.path.splitext( entry )[1]
                if extension in audioExtensions:
                    self._audioFiles.append( entryPathName )
                elif extension in imageExtensions:
                    self._imageFiles.append( entryPathName )
        self._imageFiles.sort()
        self._audioFiles.sort()

        statData = os.stat( self._path )
        self._directoryDate = statData.st_mtime

        logging.debug( " Found {} file(s) and {} image(s)".format( len( self._audioFiles ), len( self._imageFiles ) ) )


    def toDict( self ):
        return { "type": "CAudioAlbum",
                 "path": self._path,
                 "imageFiles": self._imageFiles,
                 "audioFiles": self._audioFiles,
                 "directoryDate": self._directoryDate }

    def fromDict( self, data ):
        if data["type"] != "CAudioAlbum":
            raise Exception( "Wrong type {}".format( str( data ) ) )
        self._path = data["path"]
        self._imageFiles = data["imageFiles"]
        self._audioFiles = data["audioFiles"]
        self._directoryDate = data["directoryDate"]


    def getNumAudioFiles( self ):
        """Return number of audio files in this album
        """
        return len( self._audioFiles )

    def getAudioFiles( self ):
        """Return list with audio files of this album
        """
        return self._audioFiles

    def getImageFiles( self ):
        """Return list with all image files of this album
        """
        return self._imageFiles


    def getImage( self, idx=0, size=None ):
        """Return image object of this album. Return None in case image is not
        available or error during load.
        """
        res = None
        if idx < len( self._imageFiles ):
            imageFilePath = self._imageFiles[idx]
            logging.debug( "Load image {} of album {}".format( imageFilePath, self.getName() ) )
            try:
                p = QPixmap()
                if p.load( imageFilePath ):
                    res = p
            except Exception as e:
                logging.exception( "Could not load image {}".format( imageFilePath ) )
        return res



    def getNumImageFiles( self ):
        """Return number of image files in this album
        """
        return len( self._imageFiles )

    def getPath( self ):
        """Return path to this directory
        """
        return self._path

    def getName( self ):
        """Return name of this object derived from path
        """
        return self._path.replace( " ", "" ).replace( "/", "" )

    def getDate( self ):
        """Return create timestamp of directory
        """
        return self._directoryDate



class CAudioDirectory:
    """Represents one directory with at least one other audio directory or album directory
    """

    def __init__( self, audioLibraryObj, parentDir ):
        self._libObj = audioLibraryObj
        self._parentDir = parentDir         # parent CAudioDirectory or None in case of root
        self._childs = {}
        self._imageFiles = []
        if parentDir is not None:
            self._name = parentDir.getName() + "/"
        else:
            self._name = "root/"

    def toDict( self ):
        childsData = []
        for child in self._childs:
            childsData.append( self._childs[child].toDict() )
        return { "type": "CAudioDirectory",
                "name": self._name,
                "imageFiles": self._imageFiles,
                "childs": childsData }

    def fromDict( self, data ):
        if data["type"] != "CAudioDirectory":
            raise Exception( "Invalid type: {}".format( str( data ) ) )
        self._name = data["name"]
        self._imageFiles = data["imageFiles"]
        self._childs.clear()
        for childData in data["childs"]:
            if childData["type"] == "CAudioDirectory":
                child = CAudioDirectory( self._libObj, self )
            else:
                child = CAudioAlbum( None, self._libObj, self )
            child.fromDict( childData )
            logging.debug( "Restored {}: {}".format( str( child ), child.getName() ) )
            self._childs[child.getName()] = child


    def addPath( self, path, splash ):
        if self._name.endswith( "/" ):
            self._name += os.path.basename( path )
        self._searchDirectory( self._libObj.getImageExtensions(), path, splash )

    def getNumChilds( self ):
        """Return number of child directories
        """
        return len( self._childs )

    def getChildList( self ):
        """Return list with name of child elements
        """
        res = list( self._childs )
        res.sort()
        return res

    def getChild( self, childName ):
        """Return one child item
        """
        assert childName in self._childs
        return self._childs[childName]

    def _searchDirectory( self, imageExtensions, path, splash ):
        """Search in own path for albums or other directories
        """
        logging.debug( "Search in directory {} for directories or albums".format( path ) )
        for entry in os.listdir( path ):
            entryPathName = os.path.join( path, entry )
            if not entry.startswith( '.' ) and os.path.isdir( entryPathName ):
                logging.debug( "  Found directory {}".format( entry ) )
                if splash is not None:
                    splash.showMessage( self._libObj.tr( "Search in directory {} for audio files" ).format( entry ) )
                albumObj = CAudioAlbum( entryPathName, self._libObj, self )
                if albumObj.getNumAudioFiles() > 0:
                    # found album, append to my list
                    self._childs[albumObj.getName()] = albumObj
                else:
                    # no album, try directory
                    del albumObj
                    dirObj = CAudioDirectory( self._libObj, self )
                    dirObj.addPath( entryPathName, splash )
                    if dirObj.getNumChilds() > 0:
                        # found directory with at least one album, append to my list
                        self._childs[dirObj.getName()] = dirObj
                    else:
                        # nothing found
                        del dirObj
                        logging.debug( " No content in directory {}".format( entryPathName ) )
            elif not entry.startswith( "." ) and os.path.isfile( entryPathName ):
                # also look for image files
                extension = os.path.splitext( entry )[1]
                if extension in imageExtensions:
                    self._imageFiles.append( entryPathName )

        self._imageFiles.sort()


    def getName( self ):
        """Return name of this directory derived from tree and path
        """
        return self._name




class CAudioLibrary( QObject ):

    def __init__( self, settings, userData, parent=None, splash=None ):
        super().__init__( parent )

        self._settings = settings
        self._userData = userData

        directoryList = self._settings.value( "library/dirs" )
        audioExtensions = self._settings.value( "library/audioExtension", [ ".mp3" ] )
        imageExtensions = self._settings.value( "library/imageExtension", [ ".png", ".jpg" ] )
        if isinstance( directoryList, str ):
            directoryList = [ directoryList ]
        if isinstance( audioExtensions, str ):
            audioExtensions = [ audioExtensions ]
        if isinstance( imageExtensions, str ):
            imageExtensions = [ imageExtensions ]

        logging.debug( "CAudioLibrary: {}, {}, {}".format( directoryList, audioExtensions, imageExtensions ) )

        self._audioExtensions = audioExtensions
        self._imageExtensions = imageExtensions

        self._audioTree = CAudioDirectory( self, None )

        # TODO: Save to cache directory!
        savedState = self._userData.value( "library/state", "" )
        if len( savedState ) > 0:
            try:
                logging.info( "Try to load previous state" )
                jsonData = json.loads( savedState )
                self._audioTree.fromDict( jsonData )
                logging.info( "Successfully loaded previous state" )
            except Exception as e:
                logging.exception( "Error load previous state" )
                raise

        if self._audioTree.getNumChilds() <= 0:
            # No data available so far, try to read directories
            for directory in directoryList:
                self._audioTree.addPath( directory, splash )
            # store state read
            self._userData.setValue( "library/state", json.dumps( self._audioTree.toDict() ) )

        # build up flat list, needed for search next / previous
        self._albumMap = {}                         # Dictionary with album name and album object
        self._buildAlbumMap( self._audioTree )
        logging.info( "Found {} albums".format( len( self._albumMap ) ) )


    def __del__( self ):
        pass


    def getAudioExtensions( self ):
        """Return valid audio file extensions
        """
        return self._audioExtensions


    def getImageExtensions( self ):
        """Return valid image extensions
        """
        return self._imageExtensions


    def _buildAlbumMap( self, audioDirectory ):
        """Walk through audioDirectory childs and write all albums found to self._albumMap
        """
        for childName in audioDirectory.getChildList():
            child = audioDirectory.getChild( childName )
            if isinstance( child, CAudioAlbum ):
                if child.getName() in self._albumMap:
                    raise Exception( "Child name {} already in album map".format( child.getName() ) )
                self._albumMap[ child.getName() ] = child
            elif isinstance( child, CAudioDirectory ):
                self._buildAlbumMap( child )
            else:
                raise Exception( "invalid object {}".format( str( child ) ) )


    def getAlbumList( self, type="full" ):
        """Return a list with the name of known albums. The list is already sorted.
        :param  type:   Type of list to return. Could be
                        "full":     Returns all albums in ascending order
                        "date":     Returns all albums in ascending date order
                        "dir":      Returns only first album of each directory
        """
        res = list( self._albumMap )
        if "full" == type:
            res.sort()
        elif "date" == type:
            res.sort( key=lambda albumName: self._albumMap[albumName].getDate() )
        else:
            raise Exception( "Order type/method {} not implemented yet".format( type ) )
        return res


    def getAlbum( self, albumName ):
        """Return album object for given name. Return None in case not found
        """
        if albumName in self._albumMap:
            return self._albumMap[albumName]
        return None


    def getNextAlbum( self, album, type="full" ):
        """Return name of next album in list (sort is done on type, see getAlbumList function)
        :param album:   Album object or album name
        """
        if isinstance( album, CAudioAlbum ):
            album = album.getName()

        allAlbums = self.getAlbumList( type )
        idx = allAlbums.index( album ) + 1          # if not found, use 0 as index -> first one
        if idx >= len( allAlbums ):
            idx = 0
        return allAlbums[idx]


    def getPrevAlbum( self, album, type="full" ):
        """Return name of previous album in list (sort is done on type, see getAlbumList function)
        :param album:   Album object or album name
        """
        if isinstance( album, CAudioAlbum ):
            album = album.getName()

        allAlbums = self.getAlbumList( type )
        idx = allAlbums.index( album ) - 1
        if idx < 0:
            idx = len( allAlbums ) - 1
        return allAlbums[idx]




if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG )
    if len( sys.argv ) > 1:
        a = CAudioLibrary( sys.argv[1:] )
        print( "-----" )
        print( "Full list:" )
        for albumName in a.getAlbumList():
            print( "  Album {}".format( albumName ) )

        print( "-----" )
        print( "date list:" )
        for albumName in a.getAlbumList( "date" ):
            print( "  Album {}".format( albumName ) )

    else:
        raise Exception( "At least one argument has to be given" )


