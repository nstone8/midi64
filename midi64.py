def findTracks(romPath:str)->list:
    '''Search for MIDI tracks in the rom stored at romPath returns a list of dicts containing the start position of the track in the file and the total length of the track'''
    rom=open(romPath,'rb').read() #read rom
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
        tracks.append({'start':head,'end':endPos,'format':headerFormat,'division':division,'numTracks':numTracks})
    return tracks

def ripTrackToFile(romPath:str,savePath:str,start:int,end:int,**kwargs)->None:
    '''Rip track starting at byte position start and ending at end in the rom stored at romPath to a file at savePath'''
    rom=open(romPath,'rb').read() #read rom
    track=rom[start:end]
    outFile=open(savePath,'wb')
    outFile.write(track)
    outFile.close()
def padTrack(track:bytes,desiredLength:int)->bytes:
    '''Add text meta-event to the track to cause it to reach desiredLength. Returns padded track'''
    #Check that we have enough room in our length budget for the meta-event header (may not be possible)
    #Find first Track chunk
    #stuff padding meta-event in between chunk header and the rest of the file
    #return new midi file as bytes
    pass

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
    print(sections)
    varLengthBytes=int(''.join(sections),2).to_bytes(length=len(sections),byteorder='big')
    return varLengthBytes
