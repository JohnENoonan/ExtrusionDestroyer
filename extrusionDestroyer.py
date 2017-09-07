"""
Author: John Noonan
Copyright 2017

This is a program to create randomized face extrusion animations that "destroys"
the mesh.

Example: https://vimeo.com/217427452

Repository at: https://github.com/JohnENoonan/ExtrusionDestroyer
"""



############ IMPORTS ###########
from functools import partial
from maya import cmds
import random

############ CLASSES ###########
# geo stores the stings of the transform and shape nodes
class Geo:
	def __init__(self, name_):
		self.name = name_
		self.shape = cmds.listRelatives(self.name, shapes=True)[0]
	def __str__(self):
		return str([self.name, self.shape])

# face stores the face name and shape node as strings
class Face:
	def __init__(self, name_, shape_):
		self.name = name_
		self.shape = shape_

# GeoManager is container class that stores the faces, geo nodes, and shape nodes
class GeoManager:
	def __init__(self, _geo, _minDist, _maxDist, _minScale,\
	 		_maxScale, _maxDuration=24, _minDuration=1, _perIter=1):
		# mesh being operated on
		self.geo = Geo(_geo)
		# faceList stores a list of all faces in selection with their
		# corresponding shape nodes as a Face object
		self.faceList = []
		self.add_faces()
		self.faceLen = len(self.faceList)
		# global constants
		self.minDist = _minDist
		self.maxDist = _maxDist
		self.minScale =  _minScale
		self.maxScale = _maxScale
		self.maxDuration = _maxDuration
		self.minDuration = _minDuration
		self.perIter = _perIter

	# helper function to get all faces from geometry into faceList in form of
	# Face object
	def add_faces(self):
		allFaces = self.geo.name + ".f[*]"
		# cmds.filterExpand([allFaces], sm=34) returns a list of all faces in geo
		for face in cmds.filterExpand([allFaces], sm=34):
			self.faceList.append(Face(face, self.geo.shape))

	# after every extrusion the faces need to be recalculated as new faces have been created
	def recollect_faces(self):
		# new faces is list of faces from previously known onward
		newFaces = self.geo.name + ".f[" + str(self.faceLen) + ":]"
		geoFaces = cmds.filterExpand([newFaces], sm=34)
		# add new faces into faceList
		for face in geoFaces:
			self.faceList.append(Face(face, self.geo.shape))
		# update size of faceList
		self.faceLen = len(self.faceList)

	# random face returns a random Face object from faceList
	def get_random_face(self):
		return self.faceList[random.randint(0, self.faceLen-1)]

	# sets start and end keyframes for 1 extrusion
	def set_key_extrusion(self, start, end, numExt):
		# create individual constants for this extrusion
		distance = random.uniform(self.minDist, self.maxDist)
		scale = [random.uniform(self.minScale, self.maxScale), \
		 	     random.uniform(self.minScale, self.maxScale), \
				 random.uniform(self.minScale, self.maxScale) \
		]
		# get a random face
		randomFace = self.get_random_face()
		# create extrude node
		cmds.polyExtrudeFacet(randomFace.name, kft=False)
		# get extrusion node
		extrusion = "polyExtrudeFace" + str(numExt)
		# set initial keyframe
		cmds.setKeyframe( extrusion, attribute=['localTranslateZ', 'localScaleX', 'localScaleY', 'localScaleZ'], t=start )
		# set final keyframes
		cmds.setKeyframe( extrusion, attribute='localTranslateZ', v=distance, t=end )
		cmds.setKeyframe( extrusion, attribute='localScaleX', v=scale[0], t=end )
		cmds.setKeyframe( extrusion, attribute='localScaleY', v=scale[1], t=end )
		cmds.setKeyframe( extrusion, attribute='localScaleZ', v=scale[2], t=end )

	# function to create the animation according to constants and time variables
	def create_animation(self, start, end, step):
		# how many times there is an extrusion
		maxVal = ((end-start)/step)*self.perIter
		# init progress bar
		if (cmds.window("bar" , exists=True)):
			cmds.deleteUI("bar")
		bar = cmds.window("bar", t="Creating Animation", width=600)
		cmds.columnLayout()
		progressControl = cmds.progressBar(maxValue=maxVal, width=600)
		progress= 1
		cmds.showWindow( bar )

		# the number of times there has been an extrusion
		numExt = 1
		# iterate over all frames specified
		for i in xrange(start, end, step):
			# run procedure as specified by perIter
			for j in xrange(self.perIter):
				duration = random.randint(self.minDuration, self.maxDuration)
				self.set_key_extrusion(i, i+duration, numExt)
				# get the newly created faces after extruding
				self.recollect_faces()
				numExt += 1
				progress += 1
				cmds.progressBar(progressControl, edit=True, pr=progress)
		cmds.deleteUI("bar")

	def __str__(self):
		return str(self.faceList)



############ FUNCTIONS #########
def errorTest(geo, start, end, minDur, maxDur, minDist, maxDist, minScale, maxScale):
	if len(geo)!=1:
		cmds.error("Please select exactly 1 mesh." + \
		"If more than one is needed combine them with Combine tool")
	if start > end:
		cmds.error("The starting frame must be before the ending frame")
	if minDur > maxDur:
		cmds.error("The minimum duration must be smaller than the maximum duration")
	if minDist > maxDist:
		cmds.error("The minimum distance must be smaller than the maximum distance")
	if minScale > maxScale:
		cmds.error("The minimum scale must be smaller than the maximum scale")

# Takes no arguments, but uses information from the UI to create the animation
def runProgram(*argv):
	#init vars and retrieve data
	start = cmds.intSliderGrp("startFrame", q =True, value=True)
	end = cmds.intSliderGrp("endFrame", q =True, value=True)
	step = cmds.intSliderGrp("step", q =True, value=True)
	perIter = cmds.intField( "perIter", q =True, value=True)
	minDur = cmds.intField( "minDur", q= True, value=True)
	maxDur = cmds.intField( "maxDur", q= True, value=True)
	minDist = cmds.floatField( "minDist", q= True, value=True)
	maxDist = cmds.floatField( "maxDist", q= True, value=True)
	maxScale = cmds.floatField( "maxScale", q= True, value=True)
	minScale = cmds.floatField( "minScale", q= True, value=True)

	# get selected meshes
	geometry = cmds.ls(sl=True, type="transform")
	errorTest(geometry, start, end, minDur, maxDur, minDist, maxDist, minScale, maxScale)
	# create container object
	manager = GeoManager(geometry[0], minDist, maxDist, minScale, maxScale, maxDur,
						 minDur, perIter)
	# run program
	manager.create_animation(start, end, step)
	# destroy the GUI
	cmds.deleteUI("ExtrusionDestroyer")


def createUI():
	windowName = "ExtrusionDestroyer"
	windowSize = (500, 450)
	#check to see if this window already exists
	if (cmds.window(windowName , exists=True)):
		cmds.deleteUI(windowName)
	# init window
	window = cmds.window( windowName, title= windowName, widthHeight=(windowSize[0], windowSize[1]) )

	cmds.columnLayout( "mainColumn", adjustableColumn=True, rowSpacing=20, columnAttach= ("both", 20) )
	# get frame range
	timeStart = cmds.playbackOptions( animationStartTime=True, q=True )
	timeEnd = cmds.playbackOptions( animationEndTime=True, q=True )

	############## Frame info ##############
	cmds.intSliderGrp ( "startFrame", label = "Start frame", field = True, \
	 	minValue = timeStart, maxValue = timeEnd, \
		columnWidth3 = [60, 60, 50], columnAlign3 = ["left", "both", "left"],\
		value = timeStart, parent = "mainColumn"
	)
	cmds.intSliderGrp ( "endFrame", label = "End frame", field = True, \
	 	minValue = timeStart, maxValue = timeEnd, \
		columnWidth3 = [55, 60, 50], columnAlign3 = ["left", "both", "left"],\
		value = timeEnd, parent = "mainColumn"
	)
	cmds.intSliderGrp ( "step", label = "Run Every (in Frames)", field = True, \
	 	minValue = 1, maxValue = timeEnd, \
		columnWidth3 = [115, 60, 50], columnAlign3 = ["left", "both", "left"],\
		value = 1, parent = "mainColumn"
	)

	############## Extrusions per iteration ##############
	# max distance for extrusion
	cmds.rowLayout("perIterLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Faces Extruded per Single Execution", parent="perIterLayout")
	cmds.intField( "perIter", minValue=1, parent="perIterLayout",\
		width=700, value=1
	)

	############## Duration ##############
	# min distance for extrusion
	cmds.rowLayout("minDurLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Minimum Duration of a Single Extrusion (in Frames)", parent="minDurLayout")
	cmds.intField( "minDur", minValue=1, parent="minDurLayout",\
		width=700, value=10
	)
	# max distance for extrusion
	cmds.rowLayout("maxDurLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Maximum Duration of a Single Extrusion (in Frames)", parent="maxDurLayout")
	cmds.intField( "maxDur", minValue=1, parent="maxDurLayout",\
		width=700, value=24
	)

	############## Distance ##############
	# min distance for extrusion
	cmds.rowLayout("minDistLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Minimum Extrusion Distance", parent="minDistLayout")
	cmds.floatField( "minDist", minValue=0, precision=5, parent="minDistLayout",\
		width=700, value=1
	)
	# max distance for extrusion
	cmds.rowLayout("maxDistLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Maximum Extrusion Distance", parent="maxDistLayout")
	cmds.floatField( "maxDist", minValue=0, precision=5, parent="maxDistLayout",\
		width=700, value=1
	)

	############## Scale ##############
	# min scale for extrusion
	cmds.rowLayout("minScaleLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Minimum Extrusion Scale", parent="minScaleLayout")
	cmds.floatField( "minScale", minValue=0, precision=5, parent="minScaleLayout",\
		width=700, value =1
	)
	# max scale for extrusion
	cmds.rowLayout("maxScaleLayout", numberOfColumns = 2, parent = "mainColumn",\
		columnAttach2=("left", "left"), columnOffset2=(0,20)
	)
	cmds.text(label="Maximum Extrusion Scale", parent="maxScaleLayout")
	cmds.floatField( "maxScale", minValue=0, precision=5, parent="maxScaleLayout",\
		width=700, value=1
	)
	# execute button
	cmds.button( label='Run', parent = "mainColumn", command=partial(runProgram))

	cmds.showWindow( windowName )
	# This is a workaround to get MEL global variable value in Python
	gMainWindow = maya.mel.eval('$tmpVar=$gMainWindow')
	cmds.window( windowName, edit=True, widthHeight=(windowSize[0], windowSize[1]) )


############ MAIN ##############
if __name__ == "__main__":
	createUI()
