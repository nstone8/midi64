def findTracks(romPath):
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

def ripTrackToFile(romPath,savePath,start,end,**kwargs):
    '''Rip track starting at byte position start and ending at end in the rom stored at romPath to a file at savePath'''
    rom=open(romPath,'rb').read() #read rom
    track=rom[start:end]
    outFile=open(savePath,'wb')
    outFile.write(track)
    outFile.close()
