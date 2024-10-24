# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

# This grid class was taken from mapAgents.py file in practical 5 with some additions and changes to accomadate the values grid.

# A class that creates a grid that can be used as a map
#
# The map itself is implemented as a nested list, and the interface
# allows it to be accessed by specifying x, y locations.
#
class Grid:
         
    # Constructor
    #
    # Note that it creates variables:
    #
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row=[]
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)

        self.grid = subgrid

    # Print the grid out.
    def display(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print(self.grid[i][j],)
            # A new line after each line of the grid
            print 
        # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print(self.grid[self.height - (i + 1)][j],),
            # A new line after each line of the grid
            print 
        # A line after the grid
        print
        
    # Set the values of specific elements in the map grid.
    # Here x and y are indices.
    def setMapValue(self, x, y, value):
        self.grid[int(y)][int(x)] = value

    # Get the values of specific elements in the map grid.
    def getMapValue(self, x, y):
        # If we're off the map, return a wall
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return '%'
        return self.grid[y][x]
    
    # Get the values of specific elements in the values grid.
    def getValue(self, x, y, orginalValue=0):
        # If we're off the map, or the map value is a wall, return the original value
        if x < 0 or x >= self.width or y < 0 or y >= self.height or self.getMapValue(x, y) == '%':
            return orginalValue
        return self.grid[y][x]
    
    # Set the values of specific elements in the values grid.
    def setValue(self, x, y, value):
        # If we're off the map, do nothing
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        self.grid[y][x] = value

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width
    

class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print("Starting up MDPAgent!")
        self.discount = 1.0 # Set the gamma/discount factor for bellman equation
        self.iterations = 100 # Set the number of iterations for bellman equation
        self.map = None # This will hold the map for the current game
        self.values = None # This will hold the values for each state
        self.eatenCapsule = False # This will be used to check if pacman has eaten a capsule

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print("Running registerInitialState for MDPAgent!")
        print("I'm at:")
        print(api.whereAmI(state))

        self.makeMap(state) # Make a map of the right size

        self.updateEverythingInMap(state) # Update the map with walls, food, ghosts, pacman and capsules

        self.values = self.valueIteration(state) # Make a values grid using the valueIteration function

    # This is what gets run in between multiple games
    def final(self, state):
        print("Looks like the game just ended!")

    # This makeMap function is taken from mapAgents.py file in practical 5
    # Make a map by creating a grid of the right size
    def makeMap(self,state):
        corners = api.corners(state)
        print(corners)
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)
        self.map = Grid(width, height)
    
    # These layout functions are taken from mapAgents.py file in practical 5
    # # Functions to get the height and the width of the grid.
    # #
    # # We add one to the value returned by corners to switch from the
    # # index (returned by corners) to the size of the grid (that damn
    # # "start counting at zero" thing again).
    def getLayoutHeight(self, corners):
        height = -1
        for i in range(len(corners)):
            if corners[i][1] > height:
                height = corners[i][1]
        return height + 1

    def getLayoutWidth(self, corners):
        width = -1
        for i in range(len(corners)):
            if corners[i][0] > width:
                width = corners[i][0]
        return width + 1
    
    # This addWallsToMap function is taken from mapAgents.py file in practical 5  
    # Functions to manipulate the map.
    #
    # Put every element in the list of wall elements into the map
    def addWallsToMap(self, state):
        walls = api.walls(state)
        for i in range(len(walls)):
            self.map.setMapValue(walls[i][0], walls[i][1], '%')

    # This updateFoodInMap function is taken from mapAgents.py file in practical 5
    # Create a map with a current picture of the food that exists.
    def updateFoodInMap(self, state):
        # First, make all grid elements that aren't walls blank.
        for i in range(self.map.getWidth()):
            for j in range(self.map.getHeight()):
                if self.map.getMapValue(i, j) != '%':
                    self.map.setMapValue(i, j, ' ')
        food = api.food(state)
        for i in range(len(food)):
            self.map.setMapValue(food[i][0], food[i][1], '*')

    # Set map with a current picture of the ghosts that exist.
    def updateGhostInMap(self, state):
        ghosts = api.ghosts(state)
        for i in range(len(ghosts)):
            self.map.setMapValue(ghosts[i][0], ghosts[i][1], 'G')
    
    # Set map with a current picture of pacman.
    def updatePacmanInMap(self, state):
        pacman = api.whereAmI(state)
        self.map.setMapValue(pacman[0], pacman[1], 'P')
    
    # Set map with a current picture of the capsules that exist.
    def updateCapsuleInMap(self, state):
        capsules = api.capsules(state)
        for i in range(len(capsules)):
            self.map.setMapValue(capsules[i][0], capsules[i][1], 'C')

    # This is the function that checks if there is a ghost in the adjacent cells to pacman.
    def checkGhostAura(self, x, y):
        return self.map.getMapValue(x + 1, y) == 'G' or self.map.getMapValue(x - 1, y) == 'G' or self.map.getMapValue(x, y + 1) == 'G' or self.map.getMapValue(x, y - 1) == 'G'
    
    # This is the function that computes the values for each state. 
    # It uses the bellman equation to calculate the values for each state.
    # It bases the reward on the map value of x,y. Where the x,y is the current postiton of the state that is being calculated.
    # It bases the successor value on the values of the states around the current state.
    def getSuccessorValue(self, values, x, y, state):

        # This was the code for the scared ghost reward to allow pacman to chase ghosts. It was commented because it did not win as many games as without it.
        ############################################################################################################################################################################
        # ghostInfo = state.getGhostStates()
        # ghostScaredReward = any(ghost.scaredTimer > 0 for ghost in ghostInfo)

        # if ghostScaredReward:
        #     if self.map.getMapValue(x, y) == 'G':
        #         reward = 1000
        #     elif self.map.getMapValue(x, y) == '*':
        #         reward = 100
        #     elif self.map.getMapValue(x, y) == 'C':
        #         reward = 100
        #     else:
        #         if self.map.getMapValue(x + 1, y) == 'G' or self.map.getMapValue(x - 1, y) == 'G' or self.map.getMapValue(x, y + 1) == 'G' or self.map.getMapValue(x, y - 1) == 'G':
        #             reward = 1000
        #         else:
        #             reward = -1
        # else:
        ############################################################################################################################################################################


        # If statements to set the reward based on the map value of x,y. 
        # The positions of ghosts and adjacent cells to ghosts are set to a very low reward to encourage pacman to avoid them.
        # The positions of food and capsules are set to a high reward to encourage pacman to eat them.
        # The positions of empty are set to a very low reward to encourage pacman to explore.

        if self.map.getMapValue(x, y) == '*':
            if self.checkGhostAura(x, y):
                reward = -100000000
            else:
                reward = 100
        elif self.map.getMapValue(x, y) == 'C':
            if self.checkGhostAura(x, y):
                reward = -100000000
            else:
                reward = 100
        elif self.map.getMapValue(x, y) == 'G':
            if api.whereAmI(state) in api.capsules(state):
                reward = 100000000
            else:
                reward = -100000000
        else:
            if self.checkGhostAura(x, y): 
                reward = -100000000
            else:
                reward = -1

        orginal_value = values.getValue(x, y) # Set the original value of the state to use to return if the adjacent states are a wall or they are off the map
        discount_factor = self.discount # Set the discount factor to use in the bellman equation

        # Set the successor value to the max of the four possible actions using the probabilities of the actions and the values of the states around the current state.
        successor_value = max([
            (api.directionProb * values.getValue(x, y + 1, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x - 1, y, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x + 1, y, orginal_value)),  # North
            (api.directionProb * values.getValue(x, y - 1, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x - 1, y, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x + 1, y, orginal_value)),  # South
            (api.directionProb * values.getValue(x + 1, y, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x, y - 1, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x, y + 1, orginal_value)),  # East
            (api.directionProb * values.getValue(x - 1, y, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x, y - 1, orginal_value) + (1 - api.directionProb) * 0.5 * values.getValue(x, y + 1, orginal_value)),  # West
        ])

        return (reward + discount_factor * successor_value) # Return the value of the state using the bellman equation

    
    # This is the function that computes the values for each state using value iteration.
    def valueIteration(self, state):
        # Make a map of the right size
        corners = api.corners(state)
        height = self.getLayoutHeight(corners)
        width = self.getLayoutWidth(corners)
        values = Grid(width, height)
        # Initialize all values to zero to start off the bellman equation
        for i in range(values.getWidth()):
            for j in range(values.getHeight()):
                values.setValue(i, j, 0)

        
        # Iterate the bellman equation for the number of iterations specified
        for i in range(self.iterations):
            temp_values = Grid(width, height)
            for x in range(values.getWidth()):
                for y in range(values.getHeight()):
                    # If it's a wall, don't do anything
                    if self.map.getMapValue(x, y) == '%':
                        continue
                    # Otherwise, update the value using the successor values
                    temp_values.setValue(x, y, round(self.getSuccessorValue(values, x, y, state), 2))
            values = temp_values # Set the values to the new updated values

        return values
    
        
    # Function to get the best action for a state
    def getBestAction(self, values, x, y):
        # If it's a wall, return None
        if self.map.getValue(x, y) == '%':
            return Directions.STOP
        # Otherwise, get the values for the four actions
        orginal_value = values.getValue(x, y)

        north = self.values.getValue(x, y+1, orginal_value)
        south = self.values.getValue(x, y-1, orginal_value)
        east = self.values.getValue(x+1, y, orginal_value)
        west = self.values.getValue(x-1, y, orginal_value)
        # And pick the best one
        best = max([north, south, east, west])

        # Return the best actions direction, where if the best action is the original value, dont move
        if best == orginal_value:
            return Directions.STOP
        elif best == north:
            return Directions.NORTH
        elif best == south:
            return Directions.SOUTH
        elif best == east:
            return Directions.EAST
        else:
            return Directions.WEST
    
    # Function to update the map with walls, food, ghosts, pacman and capsules
    def updateEverythingInMap(self, state):
        self.addWallsToMap(state)
        self.updateFoodInMap(state)
        self.updateGhostInMap(state)
        self.updatePacmanInMap(state)
        self.updateCapsuleInMap(state)

    # Function to get pacman to make the best move given the current state, using the getBestAction function
    def getAction(self, state):
        # Update the map with walls, food, ghosts, pacman and capsules after every action taken. As well as the values grid.
        # This is done to make sure pacman is always up to date with the current state of the game.
        self.updateEverythingInMap(state)
        self.values = self.valueIteration(state)

        # Get the legal actions we can try
        legal = state.getLegalPacmanActions()

        # Make the best move, using the getBestAction function
        return api.makeMove(self.getBestAction(self.values, api.whereAmI(state)[0], api.whereAmI(state)[1]), legal)


    
