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


import vlc
import os





class CAudioPlayer():

    def __init__( self, audioLibrary ):

        self.__audioLibrary = audioLibrary

        self.__player = vlc.MediaPlayer()
        self.__listPlayer = vlc.MediaListPlayer()
        self.__listPlayer.set_media_player( self.__player )
        self.__curMediaList = vlc.MediaList()
        self.__curAlbum = None

        self.__eventManager = self.__listPlayer.event_manager()
        self.__eventManager.event_attach( vlc.EventType.MediaListPlayerNextItemSet, self.__eventHandler )
        self.__eventsCount = 0


    def __del__( self ):
        if not self.isStopped():
            self.stop()


    def __eventHandler( self, *args ):
        self.__eventsCount = min( self.getTrackCount(), self.__eventsCount + 1 )


    def playAlbum( self, albumName ):
        """Play all files of given album. The name has to exist, else
        an exception is thrown. If currently another album is playing,
        it stops and the new one starts"""

        album = self.__audioLibrary.getAlbum( albumName )
        albumFiles = album.getAudioFiles()
        if not self.isStopped():
            self.stop()
        self.__eventsCount = 0

        mediaList = vlc.MediaList()
        for file in albumFiles:
            mediaList.add_media( file )
        self.__curMediaList = mediaList
        self.__listPlayer.set_media_list( mediaList )
        self.__listPlayer.play()
        self.__curAlbum = albumName


    def getCurAlbum( self ):
        return self.__curAlbum


    def stop( self ):
        self.__listPlayer.stop()


    def pause( self, on ):
        self.__player.set_pause( on )


    def play( self ):
        self.__listPlayer.play()


    def next( self ):
        self.__listPlayer.next()


    def previous( self ):
        oldEvents = self.__eventsCount
        self.__listPlayer.previous()
        newEvents = self.__eventsCount
        if oldEvents < newEvents:
            self.__eventsCount = max( 1, self.__eventsCount - 2 )


    def isPlaying( self ):
        return self.__player.is_playing()


    def isStopped( self ):
        return self.__player.get_state() == vlc.State.Stopped


    def isPause( self ):
        return self.__player.get_state() == vlc.State.Paused


    def getTrackCount( self ):
        return self.__curMediaList.count()


    def getTrack( self ):
        return self.__eventsCount


    def getVolume( self ):
        """Return volume in the rage of 0 ... 1.0"""
        return self.__player.audio_get_volume() / 100.0


    def setVolume( self, volume ):
        """Set volume, input range is 0 ... 1.0"""
        self.__player.audio_set_volume( max( 0, min( 100, int( volume*100 )  ) ) )


    def getTime( self ):
        """Return time of current track in s"""
        return self.__player.get_time() / 1000.0


    def getLength( self ):
        """Return length of current track in s"""
        return self.__player.get_length() / 1000.0


    def getPosition( self ):
        """Return position of current track in percent 0 ... 1.0"""
        return self.__player.get_position()


    def setPosition( self, pos ):
        """Set playback position of current track in percent 0 ... 1.0"""
        self.__player.set_position( pos )


    def getTrackDescription( self ):
        """Return text description of current active track"""
        m = self.__player.get_media()
        if m is not None:
            title = m.get_meta( vlc.Meta.Title )
            artist = m.get_meta( vlc.Meta.Artist )
            if title is None:
                title = ""
            if artist is None:
                artist = ""
            return  "{} - {}".format( title, artist )
        return ""



