'''
Created on 20 de abr de 2017

@author: helio
'''
import unittest
from simulator_simplified import *


class Test(unittest.TestCase):
    def setUp(self):
        self.simulator = Simulator()

    def test_out_of_crossing(self):
        intersection = self.simulator.horizontal_streets[0].entry_block.next_intersection
        pos_out_left = (0, -1)
        pos_out_right = (0, intersection.v_street.count_lanes)
        pos_out_up = (-1, 0)
        pos_out_down = (intersection.h_street.count_lanes, 0)
        pos_outs = [pos_out_left, pos_out_right, pos_out_up, pos_out_down]
        for pos in pos_outs:
            self.assertTrue(intersection.out_of_crossing(pos))

        pos_in1 = (0, 0)
        pos_in2 = (intersection.h_street.count_lanes - 1, intersection.v_street.count_lanes - 1)
        pos_ins = [pos_in1, pos_in2]
        for pos in pos_ins:
            self.assertFalse(intersection.out_of_crossing(pos))

    # def test_corner(self):
    #     intersection = self.simulator.horizontal_streets[0].entry_block.next_intersection
    #
    #     street_ltor = self.simulator.horizontal_streets[0]
    #     street_utod = self.simulator.vertical_streets[0]
    #     street_rtol = self.simulator.horizontal_streets[1]
    #     street_dtou = self.simulator.vertical_streets[1]
    #     corner_ltor_utod = (street_ltor.count_lanes - 1, 0)
    #     corner_ltor_dtou = (0, 0)
    #     corner_rtol_utod = (street_rtol.count_lanes - 1, street_utod.count_lanes - 1)
    #     corner_rtol_dtou = (0, street_dtou.count_lanes - 1)
    #
    #     self.assertEqual(intersection.corner(street_ltor, street_utod), street_ltor.count_lanes - 1)
    #     self.assertEqual(intersection.corner(street_ltor, street_dtou), 0)
    #     self.assertEqual(intersection.corner(street_rtol, street_utod), 0)
    #     self.assertEqual(intersection.corner(street_rtol, street_dtou), street_rtol.count_lanes - 1)

    def test_is_possible_to_turn(self):

        street = self.simulator.horizontal_streets[0]
        intersection = street.entry_block.next_intersection
        car = street.new_car(street.count_lanes - 1)
        for _ in range(4): car.move()
        self.assertTrue(intersection.is_possible_to_turn(car))

        car2 = street.new_car(0)
        for _ in range(4): car2.move()
        self.assertFalse(intersection.is_possible_to_turn(car2))

        street = self.simulator.vertical_streets[0]
        intersection = street.entry_block.next_intersection
        car3 = street.new_car(0)
        for _ in range(4): car3.move()
        self.assertTrue(intersection.is_possible_to_turn(car3))

        car4 = street.new_car(street.count_lanes - 1)
        for _ in range(4): car4.move()
        self.assertFalse(intersection.is_possible_to_turn(car4))

    def test_move_forward(self):
        street = self.simulator.horizontal_streets[0]
        car = street.new_car(0)
        car.move_forward()
        self.assertTrue(car.lane.index(car) == 1)
        self.assertIsNone(car.lane[0])
        self.assertFalse(car.in_intersection)

    def test_move_forward_into_intersection(self):
        street = self.simulator.horizontal_streets[0]
        intersection = street.entry_block.next_intersection
        car = street.new_car(0)
        for _ in range(4):
            car.move_forward()
        car.move_forward_into_intersection()
        self.assertTrue(car.in_intersection)
        self.assertFalse(car.turning)

        def flatten(l):
            return [item for sublist in l for item in sublist]

        self.assertTrue(car in flatten(intersection.crossing))

    def test_turn_into_intersection(self):
        street = self.simulator.horizontal_streets[0]
        intersection = street.entry_block.next_intersection
        car = street.new_car(0)
        for _ in range(4):
            car.move_forward()
        car.turn_into_intersection()
        self.assertTrue(car.in_intersection)
        self.assertTrue(car.turning)

        def flatten(l):
            return [item for sublist in l for item in sublist]

        self.assertTrue(car in flatten(intersection.crossing))

    def test_move_forward_in_intersection(self):
        street = self.simulator.horizontal_streets[0]
        intersection = street.entry_block.next_intersection
        car = street.new_car(0)
        for _ in range(4):
            car.move_forward()
        car.move_forward_into_intersection()
        car.move_forward_in_intersection()
        self.assertIsNone(intersection.crossing)
        exit_block = intersection.exit_blocks[DIR_HOR]
        self.assertEqual(exit_block.lanes[0][0], car)

    def test_turn_in_intersection(self):
        street = self.simulator.horizontal_streets[0]
        intersection = street.entry_block.next_intersection
        car = street.new_car(0)
        for _ in range(4):
            car.move_forward()
        car.move_forward_into_intersection()
        car.turn_into_intersection()
        car.turn_in_intersection()

        self.assertFalse(car.in_intersection)
        self.assertFalse(car.turning)

        def flatten(l):
            return [item for sublist in l for item in sublist]

        self.assertFalse(car in flatten(intersection.crossing))
        exit_block = intersection.exit_blocks[DIR_VER]
        self.assertEqual(exit_block.lanes[0][0], car)

    # def test_first_lane_available(self):
    #     street = self.simulator.horizontal_streets[0]
    #     block = street.blocks[0]
    #     self.assertEqual(block.first_lane_available(),0)
    #     street.new_car(0)
    #     self.assertEqual(block.first_lane_available(), 1)

    def test_closed(self):
        street1 = self.simulator.horizontal_streets[0]
        street2 = self.simulator.vertical_streets[0]
        intersection = street1.entry_block.next_intersection
        car1 = street1.new_car(0)
        car2 = street2.new_car(0)
        self.assertTrue(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))
        semaphore = intersection.semaphore

        semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertFalse(intersection.closed(car2))

        for _ in range(38):
            semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertFalse(intersection.closed(car2))

        for _ in range(3):
            semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

        for _ in range(2):
            semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

        for _ in range(3):
            semaphore.tick()
        self.assertFalse(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

        for _ in range(40):
            semaphore.tick()
        self.assertFalse(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

        for _ in range(2):
            semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

        semaphore.tick()
        self.assertTrue(intersection.closed(car1))
        self.assertTrue(intersection.closed(car2))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_out_of_crossing']
    unittest.main()
