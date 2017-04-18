#!/usr/local/bin/python2.7
# encoding: utf-8

from collections import deque

def genStreetId():
    count = 0
    while True:
        yield count
        count += 1

DIRECTIONS = ["H", "V"]
SENSES = ["->", "<-"]

class FullLaneException(Exception):
    pass

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
         
            

class Street:
    
    def __init__(self, countBlocks, direction):
        
        self.countBlocks = countBlocks
        self.id = genStreetId()
        self.direction = direction
        self.sense = self.id % 2
        
        self.innerBlocks = [Block(self) for i in range(countBlocks-2)]
        self.entryBlock = Block(self)
        self.exitBlock = Block(self)
        
    def getId(self):
        return self.id    
    
    def genBlockId(self):
        for i in range(self.countBlocks):
            yield i
            