#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2013 Anton Vorobyov
#
# This file is part of Eos.
#
# Eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eos. If not, see <http://www.gnu.org/licenses/>.
#===============================================================================


from eos.const.eos import Slot, Restriction
from eos.const.eve import Attribute
from eos.tests.restrictionTracker.environment import Fit, ShipItem, IndependentItem
from eos.tests.restrictionTracker.restrictionTestCase import RestrictionTestCase


class TestTurretSlot(RestrictionTestCase):
    """Check functionality of turret slot amount restriction"""

    def testFail(self):
        # Check that error is raised when number of used
        # slots exceeds slot amount provided by ship
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder1 = ShipItem(item)
        fit.items.add(holder1)
        holder2 = ShipItem(item)
        fit.items.add(holder2)
        ship = IndependentItem(self.ch.type_(typeId=2))
        ship.attributes[Attribute.turretSlotsLeft] = 1
        fit.ship = ship
        restrictionError1 = fit.getRestrictionError(holder1, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError1)
        self.assertEqual(restrictionError1.slotsMax, 1)
        self.assertEqual(restrictionError1.slotsUsed, 2)
        restrictionError2 = fit.getRestrictionError(holder2, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError2)
        self.assertEqual(restrictionError2.slotsMax, 1)
        self.assertEqual(restrictionError2.slotsUsed, 2)
        fit.items.remove(holder1)
        fit.items.remove(holder2)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testFailShipNoAttr(self):
        # Make sure that absence of specifier of slot output
        # is considered as 0 output
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder = ShipItem(item)
        fit.items.add(holder)
        ship = IndependentItem(self.ch.type_(typeId=2))
        fit.ship = ship
        restrictionError = fit.getRestrictionError(holder, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError)
        self.assertEqual(restrictionError.slotsMax, 0)
        self.assertEqual(restrictionError.slotsUsed, 1)
        fit.items.remove(holder)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testFailNoShip(self):
        # Make sure that absence of ship
        # is considered as 0 output
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder = ShipItem(item)
        fit.items.add(holder)
        restrictionError = fit.getRestrictionError(holder, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError)
        self.assertEqual(restrictionError.slotsMax, 0)
        self.assertEqual(restrictionError.slotsUsed, 1)
        fit.items.remove(holder)
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testFailModified(self):
        # Make sure that modified number of slot output
        # is taken
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder1 = ShipItem(item)
        fit.items.add(holder1)
        holder2 = ShipItem(item)
        fit.items.add(holder2)
        ship = IndependentItem(self.ch.type_(typeId=2, attributes={Attribute.turretSlotsLeft: 5}))
        ship.attributes[Attribute.turretSlotsLeft] = 1
        fit.ship = ship
        restrictionError1 = fit.getRestrictionError(holder1, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError1)
        self.assertEqual(restrictionError1.slotsMax, 1)
        self.assertEqual(restrictionError1.slotsUsed, 2)
        restrictionError2 = fit.getRestrictionError(holder2, Restriction.turretSlot)
        self.assertIsNotNone(restrictionError2)
        self.assertEqual(restrictionError2.slotsMax, 1)
        self.assertEqual(restrictionError2.slotsUsed, 2)
        fit.items.remove(holder1)
        fit.items.remove(holder2)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testPass(self):
        # No error is raised when slot users do not
        # exceed slot output
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder1 = ShipItem(item)
        fit.items.add(holder1)
        holder2 = ShipItem(item)
        fit.items.add(holder2)
        ship = IndependentItem(self.ch.type_(typeId=2))
        ship.attributes[Attribute.turretSlotsLeft] = 3
        fit.ship = ship
        restrictionError1 = fit.getRestrictionError(holder1, Restriction.turretSlot)
        self.assertIsNone(restrictionError1)
        restrictionError2 = fit.getRestrictionError(holder2, Restriction.turretSlot)
        self.assertIsNone(restrictionError2)
        fit.items.remove(holder1)
        fit.items.remove(holder2)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testPassHolderNonShip(self):
        # Non-ship holders shouldn't be affected
        fit = Fit()
        item = self.ch.type_(typeId=1)
        item.slots = {Slot.turret}
        holder1 = IndependentItem(item)
        fit.items.add(holder1)
        holder2 = IndependentItem(item)
        fit.items.add(holder2)
        ship = IndependentItem(self.ch.type_(typeId=2))
        ship.attributes[Attribute.turretSlotsLeft] = 1
        fit.ship = ship
        restrictionError1 = fit.getRestrictionError(holder1, Restriction.turretSlot)
        self.assertIsNone(restrictionError1)
        restrictionError2 = fit.getRestrictionError(holder2, Restriction.turretSlot)
        self.assertIsNone(restrictionError2)
        fit.items.remove(holder1)
        fit.items.remove(holder2)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)

    def testPassNonSlot(self):
        # If holders don't use slot, no error should
        # be raised
        fit = Fit()
        item = self.ch.type_(typeId=1)
        holder1 = ShipItem(item)
        fit.items.add(holder1)
        holder2 = ShipItem(item)
        fit.items.add(holder2)
        ship = IndependentItem(self.ch.type_(typeId=2))
        ship.attributes[Attribute.turretSlotsLeft] = 1
        fit.ship = ship
        restrictionError1 = fit.getRestrictionError(holder1, Restriction.turretSlot)
        self.assertIsNone(restrictionError1)
        restrictionError2 = fit.getRestrictionError(holder2, Restriction.turretSlot)
        self.assertIsNone(restrictionError2)
        fit.items.remove(holder1)
        fit.items.remove(holder2)
        fit.ship = None
        self.assertEqual(len(self.log), 0)
        self.assertBuffersEmpty(fit)
