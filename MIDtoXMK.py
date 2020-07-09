from mido import MidiFile,tick2second,tempo2bpm
import mido
import mmap
import struct
import convertNote
import sys
import time

try:
	mid = MidiFile("notes.mid")
except FileNotFoundError:
	print("No file, must be named 'notes.mid'")
	input("Press Enter to Exit\n")
	sys.exit()
except ValueError:
	print("Bad file, try removing slider/solo")
	input("Press Enter to Exit\n")
	sys.exit()

intTicksPB = mid.ticks_per_beat
intMultiplier = 960/intTicksPB
for y,x in enumerate(mid.tracks):
	if x.name == "" or x.name == "BEAT":
		intTrackTempo = y
	if x.name == "PART GUITAR GHL":
		intTrackGHL = y
midTracks = mido.merge_tracks([mid.tracks[intTrackTempo],mid.tracks[intTrackGHL]])

class midEvent():
	def __init__(self,index,stat,chord,note,start,end,tick,diff,velocity,unknown,offset):
		self.index = index
		self.stat = stat
		self.chord = chord
		self.note = note
		self.start = start
		self.end = end
		self.tick = tick
		self.diff = diff
		self.velocity = velocity
		self.unknown = unknown
		self.offset = offset

class midTempo():
	def __init__(self,ticks,floatSec,tempo):
		self.ticks = ticks
		self.floatSec = floatSec
		self.tempo = tempo

class midTimeSig():
	def __init__(self,ticks,beat,numerator,denominator):
		self.ticks = ticks
		self.beat = beat
		self.numerator = numerator
		self.denominator = denominator

def getCrazy(listInput):
	oldTime = 0
	newTime = 0
	intShift = 0
	for x in listInput:
		oldTime = newTime
		newTime = x[1]
		if x[1] != oldTime:
			intShift += 1
			continue
	if intShift > 1:
		return True
	else:
		return False

def getDiff(intInput):
	if intInput >= 94 and intInput <= 100:
		return 4
	if intInput >= 82 and intInput <= 88:
		return 3
	if intInput >= 70 and intInput <= 76:
		return 2
	if intInput >= 58 and intInput <= 64:
		return 1
	else:
		return 0

def getTempo():
	print("- Parsing Tempo Map")
	intSeconds = 0
	intTicks = 0
	tempoAnchor = 0
	queuedTempo = 0
	queuedThresh = 999999
	listMidTempo = []
	for event in midTracks:
		if event.type == "set_tempo":
			tempoAnchor = event.tempo
	for event in midTracks:
		intTicks += event.time
		if intTicks > queuedThresh:
			tempoAnchor = queuedTempo
		if event.type == "set_tempo":
			queuedTempo = event.tempo
			queuedThresh = intTicks
		intSeconds += tick2second(event.time,intTicksPB,tempoAnchor)
		if event.type == "set_tempo":
			listMidTempo.append(midTempo(int(intTicks*intMultiplier),intSeconds,event.tempo))
	return listMidTempo

def getTimeSig():
	print("- Parsing Time Signatures")
	intNum = 4
	intDen = 4
	intTicks = 0
	intAbsTicks = 0
	tempoAnchor = 0
	listMidTimeSig = []
	for event in midTracks:
		intTicks += event.time
		intAbsTicks += event.time / intNum * intDen / (intTicksPB*4)
		if event.type == "time_signature":
			intNum = event.numerator
			intDen = event.denominator
			listMidTimeSig.append(midTimeSig(int(intTicks*intMultiplier),round(intAbsTicks)+1,intNum,intDen))
	return listMidTimeSig

def getEvents():
	print("- Parsing Events")
#	Set Primary Tempo
	tempoAnchor = 0
	for event in midTracks:
		if event.type == "set_tempo":
			tempoAnchor = event.tempo
			break
#	Variables
	intTicks = 0
	intSeconds = 0
	queuedTempo = 0
	queuedThresh = 999999
	listMidEvent = []
#	Grab MIDI Events
	for event in midTracks:
		intTicks += event.time
		if intTicks > queuedThresh:
			tempoAnchor = queuedTempo
		if event.type == "set_tempo":
			queuedTempo = event.tempo
			queuedThresh = intTicks
		intSeconds += tick2second(event.time,intTicksPB,tempoAnchor)
		if event.type == "note_on":
			if event.note >= 94 and event.note <= 116:
				if event.velocity == 100:
					listMidEvent.append(midEvent(0,32,0,convertNote.getNote(event.note),intSeconds,0,intTicks,getDiff(event.note),event.velocity,0,100))
				if event.velocity == 0:
					for newEvent in reversed(listMidEvent):
						if convertNote.getNote(event.note) == newEvent.note:
							newEvent.end = intSeconds
							break
#	Stat
	for index,entry in enumerate(list(listMidEvent)):
		if (entry.end - entry.start) > 0.08:
			entry.stat = entry.stat | 64 # Add Sustain
		for hopo in listMidEvent[index:]:
			if hopo.start == entry.start and hopo.note == 160:
				entry.stat = entry.stat | 128 # Add Hopo
				break
#	Remove Hopo/Strum					
	for entry in list(listMidEvent):
		if entry.note == 69 and entry.stat > 96:
			entry.stat -= 128
		if entry.note == 32 or entry.note == 160 or entry.note == 103:
			listMidEvent.remove(entry)
#	Barre Chords
	for entry in list(listMidEvent):
		for chord in listMidEvent:
			if entry.start == chord.start:
				if entry.note == 59 and chord.note == 60:
					entry.chord = entry.chord | 2
					listMidEvent.remove(chord)
				if entry.note == 61 and chord.note == 62:
					entry.chord = entry.chord | 2
					listMidEvent.remove(chord)
				if entry.note == 63 and chord.note == 64:
					entry.chord = entry.chord | 2
					listMidEvent.remove(chord)
#	Crazies
	listChord = []
	for index,entry in enumerate(list(listMidEvent)):
		if entry.note != 74:
			listChunk = [[entry.note,entry.start]]
			for chord in listMidEvent[index:]:
				if chord.note != 74 and chord.start >= entry.start and chord.start < entry.end:
					listChunk.append([chord.note,chord.start])
			if listChunk not in listChord:
				if len(listChunk) > 1:
					if getCrazy(listChunk):
						listChord.append(listChunk)
	for entry in list(listMidEvent):
		for chord in listChord:
			for i in range(len(chord)):
				if entry.note == chord[i][0] and entry.start == chord[i][1]:
					entry.chord = entry.chord | convertNote.getChord(chord)
#	Index Groups
	noteIndex = 0
	heroIndex = 0
	for entry in list(listMidEvent):
		if entry.note >= 59 and entry.note <= 69:
			entry.index = noteIndex
			noteIndex += 1
		if entry.note == 74:
			entry.index = heroIndex
			heroIndex += 1
	return listMidEvent

print("Starting...")
tic = time.perf_counter()
listEvent = getEvents()
listTempo = getTempo()
listTimeSig = getTimeSig()

strBlob = "MadeByBanta546\x00andTheGuitarHeroNerd\x00"
intEventOffset = 28 + (len(listTimeSig)*12) + (len(listTempo)*16)
intVersion = 8
intHash = 0

listEvent.insert(0,midEvent(0,58,0,141,0.0,0.045,0,0,0,0,100))	# Highway Up
listEvent.insert(0,midEvent(0,3,0,128,0.0,0.0,0,0,0,0,100))		# Initial Section
listEvent.insert(0,midEvent(0,4,0,0,0.0,0.0,0,0,0,0,100))		# Start
listEvent[0].unknown = (len(listEvent)*24)+intEventOffset+585589924
listEvent[0].offset = (len(listEvent)*24)+intEventOffset
listEvent[1].unknown = (len(listEvent)*24)+intEventOffset+585589939
listEvent[1].offset = (len(listEvent)*24)+intEventOffset+15

print("- Writing XMK")
outputFile = open("guitar_3x2.xmk","wb")
outputFile.write(intVersion.to_bytes(4,byteorder="big"))
outputFile.write(intHash.to_bytes(4,byteorder="big"))
outputFile.write(len(listEvent).to_bytes(4,byteorder="big"))
outputFile.write(len(strBlob).to_bytes(4,byteorder="big"))
outputFile.write(intHash.to_bytes(4,byteorder="big"))
outputFile.write(len(listTempo).to_bytes(4,byteorder="big"))
outputFile.write(len(listTimeSig).to_bytes(4,byteorder="big"))
for x in listTempo:
	outputFile.write(x.ticks.to_bytes(4,byteorder="big"))
	outputFile.write(struct.pack(">f",x.floatSec))
	outputFile.write(x.tempo.to_bytes(4,byteorder="big"))
for x in listTimeSig:
	outputFile.write(x.ticks.to_bytes(4,byteorder="big"))
	outputFile.write(x.beat.to_bytes(4,byteorder="big"))
	outputFile.write(x.numerator.to_bytes(4,byteorder="big"))
	outputFile.write(x.denominator.to_bytes(4,byteorder="big"))
for x in listEvent:
	outputFile.write(x.index.to_bytes(4,byteorder="big"))
	outputFile.write(x.chord.to_bytes(2,byteorder="big"))
	outputFile.write(x.stat.to_bytes(1,byteorder="big"))
	outputFile.write(x.note.to_bytes(1,byteorder="big"))
	outputFile.write(struct.pack(">f",x.start))
	outputFile.write(struct.pack(">f",x.end))
	outputFile.write(x.unknown.to_bytes(4,byteorder="big"))
	outputFile.write(x.offset.to_bytes(4,byteorder="big"))
outputFile.write(strBlob.encode())
outputFile.close()

toc = time.perf_counter()
print(f"Completed in {toc - tic:0.2f} seconds")
input("Press Enter to Exit\n")
sys.exit()

#for x in listTempo:
#	print(x.ticks, x.floatSec, x.tempo)
#for x in listTimeSig:
#	print(x.ticks,x.beat,x.numerator,x.denominator)
#for x in listEvent:
#	print("{:<5}{:<5}{:<5}{:<10}{:<20}{:<20}{:<15}{:<5}".format(x.index,x.chord,x.stat,x.note,x.start,x.end,x.unknown,x.offset))
