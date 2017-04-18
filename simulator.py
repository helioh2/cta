#!/usr/local/bin/python2.7
# encoding: utf-8

from collections import deque

COUNT_STREETS = 10

def genCarId():
    count = 0
    while True:
        yield count
        count += 1
        
def genStreetId():
    for i in range(COUNT_STREETS):
        yield i

DIRECTIONS = ["H", "V"]
SENSES = ["->", "<-"]

class FullLaneException(Exception):
    pass


class Car:
    
    def __init__(self, street):
        self.street = street
        self.id = genCarId()
        self.totalTimeInSim = 0
        self.block = None
        
    def setBlock(self, block):
        self.block = block
    
    def setLane(self, lane):
        self.lane = lane
    
    def move(self):
        if self.block.getLane(self.lane).index() == self.block.getLength()-1:
            

class Block:
    
    def __init__(self, street, length, lanesCount):
        
        self.id = (street.getId(), street.genBlockId())
        self.length = length
        self.lanesCount = lanesCount    
        self.lanes = [deque(maxlen = length) for _ in range(lanesCount)]
        
    def addCar(self, car, lane):
        if self.lanes[lane] == self.length:
            raise FullLaneException("Lane "+str(lane)+" is full.")
        self.lanes[lane].append(car)
        car.setBlock(self)
        car.setLane(lane)
         
            

class Street:
    
    def __init__(self, countBlocks, direction):
        
        self.countBlocks = countBlocks
        self.id = genStreetId()
        self.direction = direction
        self.sense = self.id % 2
        
        self.blocks = [Block(self) for i in range(countBlocks)]
        self.entryBlock = self.blocks[0]
        self.exitBlock = self.blocks[-1]
        
    def getId(self):
        return self.id    
    
    def genBlockId(self):
        for i in range(self.countBlocks):
            yield i
            
    def getEntryBlock(self):
        return self.entryBlock
    
    def newCar(self, lane):
        car = Car(self)
        try:
            self.entryBlock.addCar(car, lane)
        except FullLaneException as e:
            print(e)
            ## Put on log
            
            
    
            