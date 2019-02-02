import os
class Rom:
    '''Class representing an n64 rom'''
    def __init__(self,rom:bytes):
        '''create a new Rom object containing the rom as bytes and information on all midi tracks contained therein'''
        self.rom=rom
        self.tracks=findTracks(self.rom)
    def ripTrack(self,trackNum:int,savePath:str)->None:
        '''Rip track number trackNum to a file at savePath'''
        ripTrackToFile(self.rom,savePath,self.tracks[trackNum]['start'],self.tracks[trackNum]['end'])
    def replaceTrack(self,trackNum:int,newTrackPath:str)->'Rom':
        '''Replace track number trackNum with the midi track stored at newTrackPath and return new Rom object reflecting changes'''
        newTrack=open(newTrackPath,'rb').read() #read in new track
        newTrack=padTrackNull(newTrack,self.tracks[trackNum]['length']) #pad new track to be the same length as the old one
        newRom=bytearray(self.rom) #get current rom in editable format
        newRom[self.tracks[trackNum]['start']:self.tracks[trackNum]['end']]=newTrack
        return Rom(bytes(newRom)) #return new Rom object with changed rom data
    def save(self,path:str):
        '''save rom image represented by this object to disk'''
        f=open(path,'wb')
        f.write(self.rom)
        f.close()
    def ripAllTracks(self,saveDir:str):
        i=0
        for track in self.tracks:
            f=open(os.path.join(saveDir,'Track '+str(i)+'.midi'),'wb')
            f.write(self.rom[track['start']:track['end']])
            f.close()
            i+=1
        

def loadRom(romPath:str)->Rom:
    '''Create a new Rom object from the rom stored at romPath'''
    f=open(romPath,'rb')
    rom=Rom(f.read())
    f.close()
    return rom

def findTracks(rom:bytes)->list:
    '''Search for MIDI tracks in the rom rom returns a list of dicts containing the start position of the track in the file and the total length of the track'''
    headerPos=[]
    start=0
    while True:
        #Find the position of all MIDI header chunks in the file and save them in the headerPos list
        try:
           newHeaderPos=rom.index(b'MThd',start) #search from the next header forward of position start
           headerPos.append(newHeaderPos)
           start=newHeaderPos+1
        except ValueError:
            break #no more headers, exit while loop
    else:
        raise Exception("This shouldn't ever happen")
    tracks=[] #list of midi songs to be returned, not midi track chunks
    for head in headerPos:
        #Figure out how many tracks each MIDI file contains and then find where the last track (and therefore file) ends
        headerLength=int.from_bytes(rom[head+4:head+8],'big')
        headerFormat=int.from_bytes(rom[head+8:head+10],'big')
        numTracks=int.from_bytes(rom[head+10:head+12],'big')
        division=int.from_bytes(rom[head+12:head+14],'big')
        #Search for start of last track chunk
        trackPos=head
        for i in range(numTracks):
            trackPos=head+1
            trackPos=rom.index(b'MTrk',trackPos)
        #trackPos should now be set to the beginning of the last track chunk
        trackLength=int.from_bytes(rom[trackPos+4:trackPos+8],'big')
        endPos=trackPos+8+trackLength
        tracks.append({'start':head,'end':endPos,'format':headerFormat,'division':division,'numTracks':numTracks,'length':endPos-head})
    return tracks

def ripTrackToFile(rom:bytes,savePath:str,start:int,end:int,**kwargs)->None:
    '''Rip track starting at byte position start and ending at end in the rom stored at romPath to a file at savePath'''
    track=rom[start:end]
    outFile=open(savePath,'wb')
    outFile.write(track)
    outFile.close()
def padTrackMeta(track:bytes,desiredLength:int)->bytes:
    '''Add text meta-event to the track to cause it to reach desiredLength. Returns padded track'''
    #Check that we have enough room in our length budget for the meta-event header (may not be possible)
    track=bytearray(track)
    curLen=len(track)
    padToAdd=desiredLength-curLen-2 #meta event has 2 byte overhead + len specifier + data
    if padToAdd<1:
        raise Exception('Track longer than desired length or too large to pad')
    #construct padding meta-event
    lenSpecifier=intToVariableLength(padToAdd)
    deadline=100
    while padToAdd-len(lenSpecifier)-parseVariableLength(lenSpecifier)!=0:
        #need to adjust lenSpecifier so len(lenSpecifier)+len(meta data)==padToAdd and len(meta data)==parseVariableLength(lenSpecifier)
        lenSpecifier=intToVariableLength(padToAdd-len(lenSpecifier))
        deadline-=1
        if not deadline:
            raise Exception('failed to find correct length specifier')
    padToAdd-=len(lenSpecifier) #The len specifier takes up some of our space
    meta=bytes(bytearray([0xFF,0x01])+bytearray(lenSpecifier)+bytearray([ord('a')]*padToAdd)) #meta event header for a text event followed by 'a's repeated to fill up space
    #Find first Track chunk
    firstTrackPos=track.index(b'MTrk')+4 #get position of right after 'MTrk' tag
    oldLength=int.from_bytes(track[firstTrackPos:firstTrackPos+4],'big') #length of track before padding
    newLength=oldLength+len(meta) #length of track after padding
    meta=newLength.to_bytes(length=4,byteorder='big')+meta
    #stuff padding meta-event in between chunk header and the rest of the file, overwriting old track length
    track[firstTrackPos:firstTrackPos+4]=meta
    #return new midi file as bytes
    return bytes(track)

def padTrackNull(track:bytes,desiredLength:int)->bytes:
    '''Add null bytes to the end of track to cause it to reach desiredLength. Returns padded track'''
    toAdd=desiredLength-len(track)
    track=track+bytes(toAdd)
    return track

def parseVariableLength(buf:bytes)->int:
    '''Convert the variable-length value starting at the first byte of buf to an int'''
    ans=''
    for b in buf:
        byteStr=bin(b)[2:] #strip '0b'
        #make sure byteStr has 8 bits
        while len(byteStr)<8:
            byteStr='0'+byteStr
        byteStr=byteStr[1:]#strip most significant bit
        ans=ans+byteStr #append new 7-bit section to our output number
        if b < 128: #The most significant bit is zero, so there is not another byte after this one
            break
    else:
        raise Exception('This should never happen')
    return int(ans,2)

def intToVariableLength(i:int)->bytes:
    iStr=bin(i)[2:] #strip '0b'
    #split into 7-bit sections
    sections=[]
    while iStr:
        thisSection=iStr[-7:]
        iStr=iStr[:-7]
        sections.append(thisSection)
    sections.reverse() #we want the left hand most section to be first in the list, it was constructed backwards
    #Ensure that the first section has 7 bits
    firstSection=sections[0]
    while len(firstSection)<7:
        firstSection='0'+firstSection
    sections[0]=firstSection
    #add 1s in front off all sections but the last section, to which we will add a 0
    for i in range(len(sections)-1):
        sections[i]='1'+sections[i]
    sections[-1]='0'+sections[-1]
    #concatenate and convert to bytes
    varLengthBytes=int(''.join(sections),2).to_bytes(length=len(sections),byteorder='big')
    return varLengthBytes
