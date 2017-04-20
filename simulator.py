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
      

# DIRECTIONS = ["H", "V"]
# DIR_HOR = 0
# DIR_VER = 1
# SENSES = ["->", "<-"]
# L_TO_R = 0
# R_TO_L = 1

SENSES = [(0,1),(0,-1),(1,0),(-1,0)]
SENSES_NAMES = ["RIGHT", "LEFT", "DOWN", "UP"]

DIRECTIONS = [(0,1), (1,0)]
DIRECTIONS_NAMES = ["HORIZONTAL", "VERTICAL"]
DIR_HOR = 0
DIR_VER = 1



class Simulator:
    
    def __init__(self):
        self.horizontal_streets = []
        self.vertical_streets = []
        for _ in range(COUNT_STREETS//2):
            self.horizontal_streets.append(Street(COUNT_STREETS//2 + 1, DIR_HOR, LANES_COUNT))
        for _ in range(COUNT_STREETS//2):
            self.vertical_streets.append(Street(COUNT_STREETS//2 + 1, DIR_VER, LANES_COUNT))
        
        
        self.intersections = []

        for h in range(COUNT_STREETS//2):
            h_street = self.horizontal_streets[h]
            
            for hb in range(len(h_street.blocks) - 1):
                
                h_block = h_street.blocks[hb]
                h_block_next = h_street.blocks[hb+1]
                
                v_street = self.vertical_streets[hb]
                v_block = v_street.blocks[h]
                v_block_next = v_street.blocks[h+1]
                
                if h_street.sense == (0,1):
                    h_entry_block = h_block
                    h_exit_block = h_block_next
                else:
                    h_entry_block = h_block_next
                    h_exit_block = h_block

                if v_street.sense == (1,0):
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
        
        self.exit_blocks = [h_exit_block, v_exit_block]
        
        self.h_entry_block.next_intersection = self
        self.v_entry_block.next_intersection = self
        self.h_exit_block.previous_intersection = self
        self.v_exit_block.previous_intersection = self
        
        self.h_street = h_entry_block.street
        self.v_street = v_entry_block.street
        
        self.crossing = [[None]*self.h_street.count_lanes \
                          for _ in range(self.v_street.count_lanes)]
        
        self.__id = (h_entry_block.street.id, v_entry_block.street.id)
        
        self.h_semaphore = Semaphore()
        self.v_semaphore = Semaphore()
    
    
    @property
    def id(self):
        return self.__id
    
    def __str__(self):
        return "|I"+str(self.id)+"I|"
    
    def out_of_crossing(self, pos):
        return pos[1] >= self.h_street.count_lanes or pos[0] >= self.v_street.count_lanes \
            or pos[1] < 0 or pos[0] < 0
        
    
    def corner(self, street1, street2):
        sum_dirs = street1.direction + street2.direction
        return street1.lane_id-1 if sum(sum_dirs)==1 else 0 
    
    def is_possible_to_turn(self, car):
        current_street = car.street
        if current_street.direction == DIR_HOR:
            crossing_street = self.v_street
        else:
            crossing_street = self.h_street
        
        return car.lane_id == self.corner(current_street, crossing_street)
        
    def crossing_block_and_street(self, street):
        if self.exit_blocks[0].street == street:
            block = self.exit_blocks[1]
        else:
            block = self.exit_blocks[0]

        return block, block.street
    

  

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
        self.p_crossing = None,None

    
    def move_forward(self):
        i = self.lane.index(self)
        if self.lane[i+1] == None:
            self.lane[i], self.lane[i+1] = self.lane[i+1], self.lane[i]
        #else do nothing
    
    def move_forward_into_intersection(self):

        if self.street.sense == (0,1):
            self.p_crossing = self.lane_id, 0
            
        elif self.street.sense == (0,-1):
            self.p_crossing = self.lane_id, self.street.count_lanes - 1
            
        elif self.street.sense == (1,0):
            self.p_crossing = 0, self.lane_id
        
        elif self.street.sense == (-1,0):
            self.p_crossing = self.street.count_lanes - 1, self.lane_id
        
        intersection = self.block.next_intersection
        if intersection.crossroad[self.p_crossing[0]][self.p_crossing[1]] == None:                
            intersection.crossroad[self.p_crossing[0]][self.p_crossing[1]] = self 
            self.lane[-1] = None           
            self.in_intersection = True
            return True
        
        return False
            
      
    
    def turn_into_intersection(self):
        if self.move_forward_into_intersection():
            self.turning = True
        
    
    def move_forward_in_intersection(self):
        
        intersection = self.block.next_intersection     
        p_crossing_prev = self.p_crossing
        self.p_crossing += self.street.sense
        if (intersection.out_of_crossing(self.p_crossing)):
            next_block = intersection.exit_blocks[self.street.direction]
            self.block = next_block
            self.block.add_car(self,self.lane_id)
            self.in_intersection = False
        else:
            intersection.crossroad[self.p_crossing[0]][self.p_crossing[1]] = self      
        
        intersection.crossroad[p_crossing_prev[0]][p_crossing_prev[1]] = None
        #verificar possibilidade de colisao
        
          
        
    def turn_in_intersection(self):
        intersection = self.block.next_intersection
        
        self.block, self.street = intersection.crossing_block_and_street(self.street)
        
        self.in_intersection = False
        self.turning = False
        intersection.crossroad[self.p_crossing[0]][self.p_crossing[1]] = None
        self.block.add_car(self, 0 if self.lane_id != 0 else self.street.lanes_count - 1)
        #verificar possibilidade de colisão
       
        
    def move(self):
        if self.is_leaving_block():
            intersection = self.block.next_intersection
            if intersection != None:
                if not intersection.closed():
                    if random() <= TURN_RATE and intersection.is_possible_to_turn(self):
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
        self.lanes = [[None]*length for _ in range(lanes_count)]
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
        car.street = self.block
        car.lane = self.lanes[lane_id]
        car.lane_id = lane_id
        
    def __str__(self):
        string = ""
        for lane in self.lanes:
            string += "|L:"+str(lane)+"L|"
        return str(self.previous_intersection)+" ||B:"+ str(self.id) + " " + string + "B|| " + str(self.next_intersection)


class Street:
    
    def __init__(self, count_blocks, direction, count_lanes):
        
        self.count_blocks = count_blocks
        self.count_lanes = count_lanes
        self.gen_block_id = (i for i in range(self.count_blocks))
        self.__id = next(GEN_STREET_ID)
#         self.direction = direction
        self.direction = direction
        direc = DIRECTIONS[self.direction]
        
        def calcSense(x,idd):
            '''
            Examples: direc = (0,1) and id = 0 -> sense = (0,1)
                     direc = (0,1) and id = 1 -> sense = (0,-1)
                     direc = (1,0) and id = 2 -> sense = (1,0)
                     direc = (1,0) and id = 3 -> sense = (-1,0)
            '''
            if x == 0: return 0
            elif idd%2 == 0: return 1
            else: return -1
        
        self.sense = (calcSense(direc[0], self.__id), calcSense(direc[1], self.__id))
        
        self.blocks = [Block(self, BLOCK_LENGTH, count_lanes) for _ in range(count_blocks)]
        self.entry_block = self.blocks[0] \
                        if self.sense == (1,0) or self.sense == (0,1)  else self.blocks[-1]
        self.exit_block = self.blocks[-1] \
                        if self.sense == (-1,0) or self.sense == (0,-1) else self.blocks[0]

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
        return "|||ST:"+ str(self.id) + "Sense:"+ SENSES_NAMES[SENSES.index(self.sense)] + string + "ST|||\n" 
    
    
    
def __main__():
    
    simulator = Simulator()
    print(simulator)
    
__main__()
            