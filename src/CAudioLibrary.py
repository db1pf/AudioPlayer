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
import pathlib
import shutil
import threading
import time
import shutil

from PyQt5.QtCore import QObject
from PyQt5.QtCore import QTimer
from PyQt5.Qt import QPixmap
from PyQt5.QtCore import pyqtSignal



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


    def __eq__( self, other ):
        return self._path == other._path and \
               self._imageFiles == other._imageFiles and    \
               self._audioFiles == other._audioFiles and    \
               self._directoryDate == other._directoryDate

    def __ne__( self, other ):
        return not ( self == other )


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
            res = self._libObj.getImage( self._imageFiles[idx] )
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

    def getDisplayName( self ):
        """Return last directory part which might be shown in case no picture is available
        """
        return os.path.basename( self._path )

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


    def __eq__( self, other ):
        if self._imageFiles != other._imageFiles:
            return False

        myChildList = list( self._childs )
        myChildList.sort()
        otherChildList = list( other._childs )
        otherChildList.sort()
        if myChildList != otherChildList:
            return False

        for child in myChildList:
            if self._childs[child] != other._childs[child]:
                return False

        return True


    def __ne__( self, other ):
        return not ( self == other )


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


    def addPath( self, path, splash, delay=False ):
        if self._name.endswith( "/" ):
            self._name += os.path.basename( path )
        self._searchDirectory( self._libObj.getImageExtensions(), path, splash, delay )

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

    def _searchDirectory( self, imageExtensions, path, splash, delay ):
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
                    dirObj.addPath( entryPathName, splash, delay )
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
            if delay is not None:
                time.sleep( 0.010 )         # short sleep to allow other threads to continue and to reduce CPU load

        self._imageFiles.sort()


    def getName( self ):
        """Return name of this directory derived from tree and path
        """
        return self._name


    def getFirstAlbumName( self ):
        """Return first album found in my list. If first entry is a
        directory, forward call to this object
        """
        childNames = self.getChildList()
        child = self.getChild( childNames[0] )
        if isinstance( child, CAudioDirectory ):
            return child.getFirstAlbumName()
        return child.getName()



class CAudioLibrary( QObject ):

    contentChanged = pyqtSignal()
    """Signal emitted after audio library changed. All clients saved at least parts of the
    audio library have to load the changed library data again
    """

    def __init__( self, settings, userData, parent=None, splash=None ):
        super().__init__( parent )

        self._settings = settings
        self._userData = userData

        self._directoryList = self._settings.value( "library/dirs" )
        self._audioExtensions = self._settings.value( "library/audioExtension", [ ".mp3" ] )
        self._imageExtensions = self._settings.value( "library/imageExtension", [ ".png", ".jpg" ] )
        self._cacheUpdateTime = int( self._settings.value( "library/updateCache", 600 ) )
        if isinstance( self._directoryList, str ):
            self._directoryList = [ self._directoryList ]
        if isinstance( self._audioExtensions, str ):
            self._audioExtensions = [ self._audioExtensions ]
        if isinstance( self._imageExtensions, str ):
            self._imageExtensions = [ self._imageExtensions ]

        logging.debug( "CAudioLibrary: {}, {}, {}".format( self._directoryList, self._audioExtensions, self._imageExtensions ) )

        if int( self._settings.value( "library/imageCache", True ) ):
            self._cacheDir = os.path.join( pathlib.Path.home(), ".cache", "AudioPlayer" )
            self._cacheImgDir = os.path.join( self._cacheDir, "img" )
            logging.debug( "Cache dir: {}".format( self._cacheDir ) )
            os.makedirs( self._cacheImgDir, exist_ok=True )
        else:
            self._cacheDir = None
            logging.debug( "Image cache disabled" )

        self._cacheWorker = {}                                  # Data exchange between cache update worker and this object

        self._audioTree = CAudioDirectory( self, None )         # Tree with all albums found
        self._albumMap = {}                                     # Dictionary with album name and album object

        if self._cacheDir is not None:
            try:
                logging.info( "Try to load previous state" )
                with open( os.path.join( self._cacheDir, "library.json" ), "r" ) as fp:
                    jsonData = json.load( fp )
                    self._audioTree.fromDict( jsonData )
                    logging.info( "Successfully loaded previous state" )
            except Exception as e:
                logging.exception( "Error load previous state" )

        if self._audioTree.getNumChilds() <= 0:
            # No data available so far, try to read directories and save directories read
            self._createAudioTree( self._audioTree, splash )
            self._saveAudioTree( self._audioTree )

        # build up flat list, needed for search next / previous
        self._buildAlbumMap( self._audioTree )
        logging.info( "Found {} ({}) albums".format( len( self._albumMap ), self._audioTree.getNumChilds() ) )
        if len( self._albumMap ) <= 0:
            raise Exception( "No album found. Could not start" )

        self._timer = QTimer()
        self._timer.setInterval( 10000 )
        self._timer.timeout.connect( self._processCache )
        self._timer.start()


    def __del__( self ):
        if "thread" in self._cacheWorker:
            self._cacheWorker["stop"] = True
            self._cacheWorker["thread"].join()


    def getAudioExtensions( self ):
        """Return valid audio file extensions
        """
        return self._audioExtensions


    def getImageExtensions( self ):
        """Return valid image extensions
        """
        return self._imageExtensions


    def getImage( self, imgPath ):
        """Return QPixmap of given imgPath. If possible try to fetch image from cache
        directory. If file does not exist in cache fetch from given location and save
        copy in cache.
        Returns none in case image could not be loaded
        """
        if self._cacheDir is not None:
            cachePath = os.path.join( self._cacheImgDir, imgPath[1:] if imgPath[0] == "/" else imgPath )
            if not os.path.isfile( cachePath ):
                try:
                    logging.debug( "Image {} not in cache, try to copy now".format( imgPath ) )
                    os.makedirs( os.path.dirname( cachePath ), exist_ok = True )
                    shutil.copyfile( imgPath, cachePath )
                except Exception as e:
                    logging.exception( "Copy file to cache" )
                    return None

            logging.debug( "Load image {} from cache {}".format( imgPath, cachePath ) )
        else:
            cachePath = imgPath

        try:
            p = QPixmap()
            if p.load( cachePath ):
                return p
        except:
            logging.exception( "Could not load image {} ({})".format( imgPath, cachePath ) )
        return None



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
        elif "dir" == type:
            res = []
            for childName in self._audioTree.getChildList():
                child = self._audioTree.getChild( childName )
                if isinstance( child, CAudioDirectory ):
                    firstAlbumName = child.getFirstAlbumName()
                    res.append( firstAlbumName )
                    logging.debug( "First album of directory {} is {}".format( child.getName(), firstAlbumName ) )
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
        try:
            idx = allAlbums.index( album ) + 1
        except:
            idx = 0

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
        try:
            idx = allAlbums.index( album ) - 1
        except:
            idx = -1

        if idx < 0:
            idx = len( allAlbums ) - 1
        return allAlbums[idx]



    def _processCache( self ):
        """Periodically executed by timer. Build up new audio tree in a separate thread. After thread
        is done check if new audio tree differs from current one. If yes, replace current with new one
        and inform other parts about update via signal contentChanged().
        """

        if "state" not in self._cacheWorker:
            self._cacheWorker["state"] = "idle"
        if "nextCheck" not in self._cacheWorker:
            self._cacheWorker["nextCheck"] = time.time() + 30           # do first scan 30 seconds after start

        if self._cacheWorker["state"] == "idle" and time.time() > self._cacheWorker["nextCheck"]:
            self._cacheWorker["stop"] = False
            self._cacheWorker["state"] = "update"
            self._cacheWorker["thread"] = threading.Thread( target=self._processCacheWorker )
            self._cacheWorker["thread"].start()

        elif self._cacheWorker["state"] == "done":
            if self._cacheWorker["cacheChanged"]:
                logging.info( "Audio tree changed, exchange now" )
                self._audioTree = self._cacheWorker["tree"]
                del self._cacheWorker["tree"]
                self._albumMap = {}
                self._buildAlbumMap( self._audioTree )
                self.contentChanged.emit()
            else:
                logging.info( "No changes in audio tree" )
            self._cacheWorker["state"] = "idle"
            self._cacheWorker["nextCheck"] = time.time() + self._cacheUpdateTime


    def _processCacheWorker( self ):
        """Executed in separate thread to do work load of cache update
        """
        logging.info( "Started thread to update cache" )
        self._cacheWorker["tree"] = self._audioTree
        self._cacheWorker["tree"] = CAudioDirectory( self, None )
        self._createAudioTree( self._cacheWorker["tree"], None, True )      # Build up new audio tree. Use short delay for each directory found

        cacheChanged = self._cacheWorker["tree"] != self._audioTree
        if cacheChanged:
            self._saveAudioTree( self._cacheWorker["tree"] )                # save new data read if changed

        if self._cacheDir:
            cacheChanged = self._checkCacheContent( self._cacheImgDir, "/" ) or cacheChanged

        self._cacheWorker["cacheChanged"] = cacheChanged

        self._cacheWorker["state"] = "done"
        logging.info( "Thread done" )


    def _checkCacheContent( self, cacheDir, origDir ):
        """Check if size of all elements in cacheDir is equal to origDir.
        Recursive call for all directories found
        """
        res = False
        for entry in os.listdir( cacheDir ):
            if "." == entry or ".." == entry:
                continue
            entryPath = os.path.join( cacheDir, entry )
            origPath = os.path.join( origDir, entry )

            try:
                if os.path.isdir( entryPath ):
                    if os.path.isdir( origPath ):
                        res = self._checkCacheContent( entryPath, origPath ) or res
                    else:
                        # directory does no longer exist, delete from cache now
                        logging.debug( "Directory {} in cache outdated".format( entryPath ) )
                        shutil.rmtree( entryPath )
                        res = True
                elif os.path.isfile( entryPath ):
                    keep = os.path.isfile( origPath )
                    if keep:
                        statCache = os.stat( entryPath )
                        statOrig = os.stat( origPath )
                        keep = statCache.st_size == statOrig.st_size
                    if not keep:
                        logging.debug( "File {} in cache outdated".format( entryPath ) )
                        os.remove( entryPath )
                        res = True
            except:
                logging.exception( "Error update cache content" )
        return res


    def _createAudioTree( self, audioTree, splash=None, delay=None ):
        """Append self._directoryList directories to audio tree. Audio tree is
        build up.
        """
        for directory in self._directoryList:
            audioTree.addPath( directory, splash, delay )


    def _saveAudioTree( self, audioTree ):
        if self._cacheDir is not None:
            with open( os.path.join( self._cacheDir, "library.json" ), "w" ) as fp:
                json.dump( audioTree.toDict(), fp )




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


