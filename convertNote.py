def getNote(intInput):
	dictNote = {
	#	Expert
		98: 59,		# B1
		95: 60,		# W1
		99: 61,		# B2
		96: 62,		# W2
		100: 63,	# B3
		97: 64,		# W3
		94: 69,		# Open
		101: 160,	# ForcedHOPO
		102: 32,	# ForcedStrum
	#	Hard
		86: 41,		# B1
		83: 42,		# W1
		87: 43,		# B2
		84: 44,		# W2
		88: 45,		# B3
		85: 46,		# W3
		82: 51,		# Open
		89: 152,	# ForcedHOPO
		90: 24,		# ForcedStrum
	#	Medium
		74: 23,		# B1
		71: 24,		# W1
		75: 25,		# B2
		72: 26,		# W2
		76: 27,		# B3
		73: 28,		# W3
		70: 33,		# Open
		77: 144,	# ForcedHOPO
		78: 16,		# ForcedStrum
	#	Easy
		62: 5,		# B1
		59: 6,		# W1
		63: 7,		# B2
		60: 8,		# W2
		64: 9,		# B3
		61: 10,		# W3
		58: 15,		# Open
		65: 136,	# ForcedHOPO
		66: 8,		# ForcedStrum
	#	Other
		116: 74		# StarPower

	}
	if intInput in dictNote:
		return dictNote[intInput]
	else:
		return intInput

def getChord(listInput):
	dictNote = {
	#	Expert
		59: 4,
		61: 8,
		63: 16,
		60: 32,
		62: 64,
		64: 128,
	#	Hard
		41: 4,
		43: 8,
		45: 16,
		42: 32,
		44: 64,
		46: 128,
	#	Medium
		23: 4,
		25: 8,
		27: 16,
		24: 32,
		26: 64,
		28: 128,
	#	Easy
		5: 4,
		7: 8,
		9: 16,
		6: 32,
		8: 64,
		10: 128
	}
	output = 0
	for x in listInput:
		output = output | dictNote[x[0]]
	return output