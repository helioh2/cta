#!/usr/local/bin/python2.7
# encoding: utf-8

from collections import deque
from random import random

COUNT_STREETS = 20
TURN_RATE = 0.1
BLOCK_LENGTH = 5
LANES_COUNT = 1

def gen_car_id():
    count = 0
    while True:
        yield count
        count += 1
GEN_CAR_ID = gen_car_id()       
GEN_STREET_ID = (i for i in range(COUNT_STREETS))
      

DIRECTIONS = ["H", "V"]
DIR_HOR = 0
DIR_VER = 1
SENSES = ["->", "<-"]
L_TO_R = 0
R_TO_L = 1


class Simulator:
    
    def __init__(self):
        self.horizontal_streets = []
        self.vertical_streets = []
        for _ in range(COUNT_STREETS//2):
            self.horizontal_streets.append(Street(COUNT_STREETS//2 + 1, DIR_HOR))
        for _ in range(COUNT_STREETS//2):
            self.vertical_streets.append(Street(COUNT_STREETS//2 + 1, DIR_VER))
        
        self.crossroad = [[None for _ in range(LANES_COUNT)] for _ in range(LANES_COUNT)]

        self.intersections = []

        for h in range(COUNT_STREETS//2):
            h_street = self.horizontal_streets[h]
            
            for hb in range(len(h_street.blocks) - 1):
                
                h_block = h_street.blocks[hb]
                h_block_next = h_street.blocks[hb+1]
                
                v_street = self.vertical_streets[hb]
                v_block = v_street.blocks[h]
                v_block_next = v_street.blocks[h+1]
                
                if h_street.sense == L_TO_R:
                    h_entry_block = h_block
                    h_exit_block = h_block_next
                else:
                    h_entry_block = h_block_next
                    h_exit_block = h_block

                if v_street.sense == L_TO_R:
                    v_entry_block = v_block
                    v_exit_block = v_block_next
                else:
                    v_entry_block = v_block_next
                    v_exit_block = v_block
                    
                intersection = Intersection(h_entry_block, h_exit_block, v_entry_block, v_exit_block)
                self.intersections.append(intersection)

                       
    def __str__(self):
        string = "HORIZONTAL STREETS:\n"
        for h_street in self.horizontal_streets:
            string += str(h_street)
        string += "VERTICAL STREETS:\n"
        for v_street in self.vertical_streets:
            string += str(v_street)
            
        return string


class FullLaneException(Exception):
    pass

class Semaphore:
    pass


class Intersection:
    
    def __init__(self, h_entry_block, h_exit_block, v_entry_block, v_exit_block):
        self.h_entry_block = h_entry_block
        self.h_exit_block = h_exit_block
        self.v_entry_block = v_entry_block       
        self.v_exit_block = v_exit_block
        
        self.h_entry_block.next_intersection = self
        self.v_entry_block.next_intersection = self
        self.h_exit_block.previous_intersection = self
        self.v_exit_block.previous_intersection = self
        
        self.__id = (h_entry_block.street.id, v_entry_block.street.id)
        
        self.h_semaphore = Semaphore()
        self.v_semaphore = Semaphore()
    
    
    @property
    def id(self):
        return self.__id
    
    def __str__(self):
        return "|I"+str(self.id)+"I|"
    
    

  

class Car:
    
    def __init__(self, street):
        self.street = street
        self.__id = next(GEN_CAR_ID)
        self.total_time_in_sim = 0
        self.block = None
        self.lane = None
        self.lane_id = None
        self.in_intersection = False
        self.turning = False
        self.pos_intersection = None,None

    
    def move_forward(self):
        i = self.lane.index(self)
        if self.lane[i+1] == None:
            self.lane[i], self.lane[i+1] = self.lane[i+1], self.lane[i]
        #else do nothing
    
    def move_forward_into_intersection(self):
        intersection = self.block.next_intersection
        if self.street.direction == DIR_HOR and self.street.sense == L_TO_R:
            if intersection.crossroad[self.lane_id][0] == None:                
                intersection.crossroad[self.lane_id][0] = self 
                self.pos_intersection = self.lane_id, 0
                self.lane[-1] = None           
                self.in_intersection = True
                return True
        elif self.street.direction == DIR_HOR and self.street.sense == R_TO_L:
            if intersection.crossroad[self.lane_id][LANES_COUNT-1] == None:                
                intersection.crossroad[self.lane_id][LANES_COUNT-1] = self 
                self.pos_intersection = self.lane_id, LANES_COUNT-1
                self.lane[-1] = None           
                self.in_intersection = True
                return True
            
        elif self.street.direction == DIR_VER and self.street.sense == L_TO_R:    
            if intersection.crossroad[0][self.lane_id] == None:  
                intersection.crossroad[0][self.lane_id] = self 
                self.pos_intersection = 0, self.lane_id
                self.lane[-1] = None           
                self.in_intersection = True
                return True
            
        elif self.street.direction == DIR_VER and self.street.sense == R_TO_L:
            if intersection.crossroad[LANES_COUNT-1][self.lane_id] == None:  
                intersection.crossroad[LANES_COUNT-1][self.lane_id] = self 
                self.pos_intersection = LANES_COUNT-1, self.lane_id
                self.lane[-1] = None           
                self.in_intersection = True
                return True  
        return False
                
    
    def turn_into_intersection(self):
        if self.move_forward_into_intersection():
            self.turning = True
        
    
    def move_forward_in_intersection(self):
        #checar se andou até o final, senão andar
        intersection = self.block.next_intersection
        if self.street.direction == DIR_HOR and self.street.sense == L_TO_R:
            
            if self.pos_intersection == (self.lane_id, LANES_COUNT-1):                  
                next_block = intersection.h_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[self.lane_id][LANES_COUNT-1] = None
            else:
                intersection.crossroad[self.lane_id][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id, self.pos_intersection[1] + 1
                intersection.crossroad[self.lane_id][self.pos_intersection[1]] = self
                
                
        elif self.street.direction == DIR_HOR and self.street.sense == R_TO_L:
            
            if self.pos_intersection == (self.lane_id, 0):                  
                next_block = intersection.h_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[self.lane_id][0] = None
            else:
                intersection.crossroad[self.lane_id][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id, self.pos_intersection[1] - 1
                intersection.crossroad[self.lane_id][self.pos_intersection[1]] = self
                
        elif self.street.direction == DIR_VER and self.street.sense == L_TO_R:   
            
            if self.pos_intersection == (LANES_COUNT-1, self.lane_id):
                  
                next_block = intersection.v_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[LANES_COUNT-1][self.lane_id] = None
            else:
                intersection.crossroad[self.pos_intersection[1]][self.lane_id] = None
                self.pos_intersection = self.pos_intersection[1] + 1, self.lane_id
                intersection.crossroad[self.pos_intersection[1]][self.lane_id] = self
                
        elif self.street.direction == DIR_VER and self.street.sense == R_TO_L: 
            if self.pos_intersection == (0, self.lane_id):
                  
                next_block = intersection.v_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[0][self.lane_id] = None
            else:
                intersection.crossroad[self.pos_intersection[1]][self.lane_id] = None
                self.pos_intersection = self.pos_intersection[1] - 1, self.lane_id
                intersection.crossroad[self.pos_intersection[1]][self.lane_id] = self   
        
    def turn_in_intersection(self):
        #checar se andou até o final, senão andar
        intersection = self.block.next_intersection
        if self.street.direction == DIR_HOR and self.street.sense == L_TO_R:
            if self.pos_intersection[1] < self.lane_id:
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id, self.lane_id+1
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = self
                
            elif self.pos_intersection != (LANES_COUNT-1, self.lane_id):
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id+1, self.lane_id
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = self
            else:
                next_block = intersection.v_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None
                
        if self.street.direction == DIR_HOR and self.street.sense == R_TO_L:
            if self.pos_intersection[1] > self.lane_id:
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id, self.lane_id-1
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = self
                
            elif self.pos_intersection != (LANES_COUNT-1, self.lane_id):
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None
                self.pos_intersection = self.lane_id+1, self.lane_id
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = self
            else:
                next_block = intersection.v_exit_block
                self.block = next_block
                self.block.add_car(self,self.lane_id)
                intersection.crossroad[self.pos_intersection[0]][self.pos_intersection[1]] = None        
                
                 
        
                intersection = self.block.next_intersection
                if self.block == intersection.h_entry_block:
                    next_block = intersection.v_exit_block
                else:
                    next_block = intersection.h_exit_block
                self.next_block.add_car(self)
        
        
        
    def move(self):
        if self.is_leaving_block():
            intersection = self.block.next_intersection
            if intersection != None:
                if not intersection.closed():
                    if random() <= TURN_RATE:
                        self.turn_into_intersection()
                    else:
                        self.move_forward_into_intersection()
                # else do nothing
            else:
                self.block.remove_car(self)
        elif self.turning and self.in_intersection:
            self.turn_in_intersection()
        elif self.in_intersection:
            self.move_forward_in_intersection()
        else:
            self.move_forward()
                
            
    def is_leaving_block(self):
        return self.lane[-1] == self
    
    
    def __str__(self):
        return "|C:"+str(id)+"|"

class Block:
    
    def __init__(self, street, length, lanes_count):
        
        self.__id = (street.id, next(street.gen_block_id))
        self.street = street
        self.length = length
        self.lanes_count = lanes_count    
        self.lanes = [[None]*length for _ in lanes_count]
        self.next_intersection = None
        self.previous_intersection = None

    
    @property
    def id(self):
        return self.__id
        
    def add_car(self, car, lane_id):
        if self.lanes[lane_id][0] != None:
            raise FullLaneException("_lane "+str(lane_id)+" is full.")
        self.lanes[lane_id][0] = car
        car.block = self
        car.lane = self.lanes[lane_id]
        car.lane_id = lane_id
        
    def __str__(self):
        string = ""
        for lane in self.lanes:
            string += "|L:"+str(lane)+"L|"
        return str(self.previous_intersection)+" ||B:"+ str(self.id) + " " + string + "B|| " + str(self.next_intersection)


class Street:
    
    def __init__(self, count_blocks, direction):
        
        self.count_blocks = count_blocks
        self.gen_block_id = (i for i in range(self.count_blocks))
        self.__id = next(GEN_STREET_ID)
        self.direction = direction
        self.sense = self.__id % 2
        
        self.blocks = [Block(self, BLOCK_LENGTH, LANES_COUNT) for _ in range(count_blocks)]
        self.entry_block = self.blocks[0] if self.sense == L_TO_R else self.blocks[-1]
        self.exit_block = self.blocks[-1] if self.sense == L_TO_R else self.blocks[0]

    @property
    def id(self):
        return self.__id
    
  
    
    def new_car(self, lane):
        car = Car(self)
        try:
            self.entry_block.add_car(car, lane)
        except FullLaneException as e:
            print(e)
            ## _put on log
            
            
    def __str__(self):
        string = ""
        for block in self.blocks:
            string += str(block)
        return "|||ST:"+ str(self.id) + "Sense:"+ SENSES[self.sense] + string + "ST|||\n" 
    
    
    
def __main__():
    
    simulator = Simulator()
    print(simulator)
    
__main__()
            