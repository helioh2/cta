#!/usr/local/bin/python2.7
# encoding: utf-8
import copy
from collections import deque
from random import random

COUNT_STREETS = 20
TURN_RATE = 0.1
BLOCK_LENGTH = 5
LANES_COUNT = 1

SENSES = [(0, 1), (0, -1), (1, 0), (-1, 0)]
SENSES_NAMES = ["RIGHT", "LEFT", "DOWN", "UP"]

DIRECTIONS = [(0, 1), (1, 0)]
DIRECTIONS_NAMES = ["HORIZONTAL", "VERTICAL"]
DIR_HOR = 0
DIR_VER = 1

RED = 0
GREEN = 1
YELLOW = 2

SEP = "|"
LOGNAME = "simulator.txt"


class Logger:
    def __init__(self, filename):
        self.file = open(filename, "w")

    def writeline(self, s):
        self.file.write(s + "\n")

    def log_init(self):
        s = "INIT" + SEP
        s += str(COUNT_STREETS // 2) + SEP
        s += str(COUNT_STREETS // 2) + SEP
        s += str(BLOCK_LENGTH) + SEP
        s += str(LANES_COUNT) + SEP
        s += str(0) + SEP
        s += str(0) + SEP
        s += str(1)
        self.writeline(s)

    def log_new_car(self, car):
        s = "CAR-NEW" + SEP
        s += str(car.id) + SEP
        s += str(car.street.direction) + SEP
        if car.street.direction == DIR_HOR:
            s += str(car.street.id)
        else:
            s += str(car.street.id - COUNT_STREETS // 2)
        self.writeline(s)

    def log_move_car(self, car, turn=False):
        s = "CAR-MOVE" + SEP
        s += str(car.id) + SEP
        if turn:
            s += str(1)
        else:
            s += str(0)
        self.writeline(s)

    def log_car_exit(self, car):
        s = "CAR-EXIT" + SEP
        s += str(car.id)
        self.writeline(s)

    def log_clock(self):
        s = "CLOCK" + SEP
        s += str(1)
        self.writeline(s)

    def log_semaphore(self, intersection):
        s = "SEMAPHORE" + SEP
        hor = intersection.h_street.id
        ver = intersection.v_street.id - 10
        s += str(hor) + SEP
        s += str(ver) + SEP
        tfs = intersection.semaphore.traffic_lights
        timer = intersection.semaphore.timer
        if tfs[0] == RED and tfs[1] == RED and 1 + 38 + 5 <= timer < 47:
            pos = 0
        elif tfs[0] == GREEN and tfs[1] == RED:
            pos = 1
        elif tfs[0] == YELLOW and tfs[1] == RED:
            pos = 2
        elif tfs[0] == RED and tfs[1] == RED and timer == 0:
            pos = 3
        elif tfs[0] == RED and tfs[1] == GREEN:
            pos = 4
        elif tfs[0] == RED and tfs[1] == YELLOW:
            pos = 5

        s += str(pos)
        self.writeline(s)

    def close(self):
        self.file.close()


class Clock:
    def __init__(self, simulator):
        for _ in range(100):
            simulator.tick()


class Simulator:
    def __init__(self):

        def gen_car_id():
            count = 0
            while True:
                yield count
                count += 1

        self.gen_car_id = gen_car_id()
        self.gen_street_id = (i for i in range(COUNT_STREETS))

        self.timer = 0
        self.logger = Logger(LOGNAME)

        self.horizontal_streets = []
        self.vertical_streets = []
        for _ in range(COUNT_STREETS // 2):
            self.horizontal_streets.append(Street(self, COUNT_STREETS // 2 + 1, DIR_HOR, LANES_COUNT))
        for _ in range(COUNT_STREETS // 2):
            self.vertical_streets.append(Street(self, COUNT_STREETS // 2 + 1, DIR_VER, LANES_COUNT))

        self.intersections = []

        for h in range(COUNT_STREETS // 2):
            h_street = self.horizontal_streets[h]

            for hb in range(len(h_street.blocks) - 1):

                h_block = h_street.blocks[hb]
                h_block_next = h_street.blocks[hb + 1]

                v_street = self.vertical_streets[hb]
                v_block = v_street.blocks[h]
                v_block_next = v_street.blocks[h + 1]

                if h_street.sense == (0, 1):
                    h_entry_block = h_block
                    h_exit_block = h_block_next
                else:
                    h_entry_block = h_block_next
                    h_exit_block = h_block

                if v_street.sense == (1, 0):
                    v_entry_block = v_block
                    v_exit_block = v_block_next
                else:
                    v_entry_block = v_block_next
                    v_exit_block = v_block

                intersection = Intersection(h_entry_block, h_exit_block, v_entry_block, v_exit_block)
                self.intersections.append(intersection)
        self.logger.log_init()

    def __str__(self):
        string = "HORIZONTAL STREETS:\n"
        for h_street in self.horizontal_streets:
            string += str(h_street)
        string += "VERTICAL STREETS:\n"
        for v_street in self.vertical_streets:
            string += str(v_street)

        return string

    def tick(self):

        self.logger.log_clock()

        def flatten(l):
            return [item for sublist in l for item in sublist]

        moved = []
        for intersection in self.intersections:
            intersection.tick()
            crossing = [intersection.crossing[i][j] for i in range(1) for j in range(1)]

            for i in range(0,len(crossing)):
                print(i)
                car = crossing[i]
                if car is not None:
                    car.move()
                    moved.append(car)

        for street in self.horizontal_streets + self.vertical_streets:
            for block in street.blocks:
                for lane in block.lanes:
                    for car in reversed(lane):
                        if car is not None and car not in moved:
                            car.move()
            if self.timer % 10 == 0:
                street.new_car(street.entry_block.first_lane_available())

        self.timer += 1
        print(self)


class FullLaneException(Exception):
    pass


class Semaphore:
    def __init__(self, intersection):
        self.traffic_lights = [RED, RED]
        self.yellow_time = [47 + 38, 1 + 38]
        self.intersection = intersection
        self.timer = 0

    def tick(self):

        self.timer += 1
        if self.timer == 1:
            self.traffic_lights[1] = GREEN
            self.intersection.simulator.logger.log_semaphore(self.intersection)
        elif self.timer == 1 + 38:
            self.traffic_lights[1] = YELLOW
            self.intersection.simulator.logger.log_semaphore(self.intersection)
        elif self.timer == 1 + 38 + 5:
            self.traffic_lights[1] = RED
            self.intersection.simulator.logger.log_semaphore(self.intersection)
        elif self.timer == 47:
            self.traffic_lights[0] = GREEN
            self.intersection.simulator.logger.log_semaphore(self.intersection)
        elif self.timer == 47 + 38:
            self.traffic_lights[0] = YELLOW
            self.intersection.simulator.logger.log_semaphore(self.intersection)
        elif self.timer == 47 + 38 + 5:
            self.traffic_lights[0] = RED
            self.timer = 0
            self.intersection.simulator.logger.log_semaphore(self.intersection)


class Intersection:
    def __init__(self, h_entry_block, h_exit_block, v_entry_block, v_exit_block):
        self.h_entry_block = h_entry_block
        self.h_exit_block = h_exit_block
        self.v_entry_block = v_entry_block
        self.v_exit_block = v_exit_block

        self.exit_blocks = [h_exit_block, v_exit_block]
        self.entry_blocks = [h_entry_block, v_entry_block]

        self.h_entry_block.next_intersection = self
        self.v_entry_block.next_intersection = self
        self.h_exit_block.previous_intersection = self
        self.v_exit_block.previous_intersection = self

        self.h_street = h_entry_block.street
        self.v_street = v_entry_block.street

        self.simulator = self.h_street.simulator

        self.crossing = [[None] * self.v_street.count_lanes \
                         for _ in range(self.h_street.count_lanes)]

        self.__id = (h_entry_block.street.id, v_entry_block.street.id)

        self.semaphore = Semaphore(self)

    @property
    def id(self):
        return self.__id

    def __str__(self):
        return "|I" + str(self.id) + "I|"

    def out_of_crossing(self, pos):
        return pos[1] >= self.h_street.count_lanes or pos[0] >= self.v_street.count_lanes \
               or pos[1] < 0 or pos[0] < 0

    def corner(self, street1, street2):
        senses_sum = [sum(x) for x in zip(street1.sense, street2.sense)]
        if street1.direction == DIR_HOR:
            if sum(senses_sum) == 0:
                return 0
            else:
                return street1.count_lanes - 1
        else:
            if sum(senses_sum) == 0:
                street1.count_lanes - 1
            else:
                return 0

    def is_possible_to_turn(self, car):
        current_street = car.street
        if current_street.direction == DIR_HOR:
            crossing_street = self.v_street
        else:
            crossing_street = self.h_street

        return car.lane_id == self.corner(current_street, crossing_street)

    def crossing_block_and_street(self, street):
        if self.entry_blocks[0].street == street:
            block = self.entry_blocks[1]
        else:
            block = self.entry_blocks[0]

        return block, block.street

    def closed(self, car):

        dir_semaphore = car.street.direction
        traffic_light = self.semaphore.traffic_lights[dir_semaphore]

        return traffic_light == RED or \
               (traffic_light == YELLOW and \
                self.semaphore.timer > self.semaphore.yellow_time[dir_semaphore] + 2)

    def tick(self):
        self.semaphore.tick()


class Car:
    def __init__(self, street):
        self.street = street
        self.simulator = self.street.simulator
        self.__id = next(self.simulator.gen_car_id)
        self.total_time_in_sim = 0
        self.block = None
        self.lane = None
        self.lane_id = None
        self.in_intersection = False
        self.turning = False
        self.p_crossing = None, None

    @property
    def id(self):
        return self.__id

    def move_forward(self):
        i = self.lane.index(self)
        if self.lane[i + 1] is None:
            self.lane[i], self.lane[i + 1] = self.lane[i + 1], self.lane[i]
            self.simulator.logger.log_move_car(self)
            # else do nothing
        return True

    def move_forward_into_intersection(self, turn=False):

        if self.street.sense == (0, 1):
            self.p_crossing = self.lane_id, 0

        elif self.street.sense == (0, -1):
            self.p_crossing = self.lane_id, self.street.count_lanes - 1

        elif self.street.sense == (1, 0):
            self.p_crossing = 0, self.lane_id

        elif self.street.sense == (-1, 0):
            self.p_crossing = self.street.count_lanes - 1, self.lane_id

        intersection = self.block.next_intersection
        # if intersection.crossing[self.p_crossing[0]][self.p_crossing[1]] is None:
        intersection.crossing[self.p_crossing[0]][self.p_crossing[1]] = self
        self.lane[-1] = None
        self.in_intersection = True

        if turn:
            self.block, self.street = intersection.crossing_block_and_street(self.street)
            self.simulator.logger.log_move_car(self, False)
            self.simulator.logger.log_move_car(self, True)

        else:
            self.simulator.logger.log_move_car(self, False)

        return True

        # return False

    def move_forward_in_intersection(self, turn=False):

        intersection = self.block.next_intersection
        p_crossing_prev = self.p_crossing
        self.p_crossing = [sum(x) for x in zip(self.p_crossing, self.street.sense)]
        if intersection.out_of_crossing(self.p_crossing):
            next_block = intersection.exit_blocks[self.street.direction]
            self.block = next_block
            try:
                self.block.add_car(self, self.lane_id)
            except FullLaneException as e:
                print(e)
            self.in_intersection = False
        else:
            intersection.crossing[self.p_crossing[0]][self.p_crossing[1]] = self

        intersection.crossing[p_crossing_prev[0]][p_crossing_prev[1]] = None
        self.simulator.logger.log_move_car(self)


        # verificar possibilidade de colisao

    # def turn_in_intersection(self):
    #
    #
    #
    #
    #     # self.in_intersection = False
    #     # self.turning = False
    #
    #     # self.move_forward_in_intersection()
    #     # verificar possibilidade de colisão

    def move(self):
        if self.is_leaving_block():
            intersection = self.block.next_intersection
            if intersection is not None:
                if not intersection.closed(self):
                    if random() <= TURN_RATE:  # and intersection.is_possible_to_turn(self):
                        self.move_forward_into_intersection(True)
                    else:
                        self.move_forward_into_intersection()
                        # else do nothing
            else:
                self.block.remove_car(self)
                return True
        # elif self.turning and self.in_intersection:
        #     self.turn_in_intersection()
        elif self.in_intersection:
            return self.move_forward_in_intersection()
        else:
            return self.move_forward()

    def is_leaving_block(self):
        return self.lane[-1] == self

    def __str__(self):
        return "|C:" + str(id) + "|"


class Block:
    def __init__(self, street, length, lanes_count):

        self.__id = (street.id, next(street.gen_block_id))
        self.street = street
        self.length = length
        self.lanes_count = lanes_count
        self.lanes = [[None] * length for _ in range(lanes_count)]
        self.next_intersection = None
        self.previous_intersection = None

    @property
    def id(self):
        return self.__id

    def add_car(self, car, lane_id):
        if lane_id is None or self.lanes[lane_id][0] != None:
            raise FullLaneException("_lane " + str(lane_id) + " is full.")
        self.lanes[lane_id][0] = car
        car.block = self
        car.street = self.street
        car.lane = self.lanes[lane_id]
        car.lane_id = lane_id

    def first_lane_available(self):
        for i in range(len(self.lanes)):
            if self.lanes[i][0] is None:
                return i
        return None

    def __str__(self):
        string = ""
        for lane in self.lanes:
            string += "|L:" + str(lane) + "L|"
        return str(self.previous_intersection) + " ||B:" + str(self.id) + " " + string + "B|| " + str(
            self.next_intersection)

    def remove_car(self, car):
        lane = car.lane
        lane[lane.index(car)] = None
        self.street.simulator.logger.log_car_exit(car)


class Street:
    def __init__(self, simulator, count_blocks, direction, count_lanes):

        self.simulator = simulator
        self.count_blocks = count_blocks
        self.count_lanes = count_lanes
        self.gen_block_id = (i for i in range(self.count_blocks))
        self.__id = next(self.simulator.gen_street_id)
        #         self.direction = direction
        self.direction = direction
        direc = DIRECTIONS[self.direction]

        def calcSense(x, idd):
            '''
            Examples: direc = (0,1) and id = 0 -> sense = (0,1)
                     direc = (0,1) and id = 1 -> sense = (0,-1)
                     direc = (1,0) and id = 2 -> sense = (1,0)
                     direc = (1,0) and id = 3 -> sense = (-1,0)
            '''
            if x == 0:
                return 0
            elif idd % 2 == 0:
                return 1
            else:
                return -1

        self.sense = (calcSense(direc[0], self.__id), calcSense(direc[1], self.__id))

        self.blocks = [Block(self, BLOCK_LENGTH, count_lanes) for _ in range(count_blocks)]
        self.entry_block = self.blocks[0] \
            if self.sense == (1, 0) or self.sense == (0, 1)  else self.blocks[-1]
        self.exit_block = self.blocks[-1] \
            if self.sense == (-1, 0) or self.sense == (0, -1) else self.blocks[0]

    @property
    def id(self):
        return self.__id

    def new_car(self, lane):
        car = Car(self)
        try:
            self.entry_block.add_car(car, lane)
            self.simulator.logger.log_new_car(car)
            return car
        except FullLaneException as e:
            print(e)
            ## _put on log

    def __str__(self):
        string = ""
        for block in self.blocks:
            string += str(block)
        return "|||ST:" + str(self.id) + "Sense:" + SENSES_NAMES[SENSES.index(self.sense)] + string + "ST|||\n"


def __main__():
    simulator = Simulator()
    print(simulator)
    clock = Clock(simulator)


__main__()
