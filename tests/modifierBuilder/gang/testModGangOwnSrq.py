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


from eos.const.eos import State, Location, EffectBuildStatus, Context, FilterType, Operator
from eos.tests.modifierBuilder.modBuilderTestCase import ModBuilderTestCase


class TestModGangOwnSrq(ModBuilderTestCase):
    """Test parsing of trees describing gang-mates' in-space items modification filtered by skill requirement"""

    def setUp(self):
        ModBuilderTestCase.setUp(self)
        # Manually composed example, as CCP doesn't use this modification type in any effect
        eTgtSrq = self.ef.make(1, operandID=29, expressionTypeID=3326)
        eTgtAttr = self.ef.make(2, operandID=22, expressionAttributeID=654)
        eOptr = self.ef.make(3, operandID=21, expressionValue='PostMul')
        eSrcAttr = self.ef.make(4, operandID=22, expressionAttributeID=848)
        eTgtSpec = self.ef.make(5, operandID=64, arg1=eTgtSrq['expressionID'], arg2=eTgtAttr['expressionID'])
        eOptrTgt = self.ef.make(6, operandID=31, arg1=eOptr['expressionID'], arg2=eTgtSpec['expressionID'])
        self.eAddMod = self.ef.make(7, operandID=4, arg1=eOptrTgt['expressionID'], arg2=eSrcAttr['expressionID'])
        self.eRmMod = self.ef.make(8, operandID=56, arg1=eOptrTgt['expressionID'], arg2=eSrcAttr['expressionID'])

    def testGenericBuildSuccess(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 0)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(modifier.sourceAttributeId, 848)
        self.assertEqual(modifier.operator, Operator.postMul)
        self.assertEqual(modifier.targetAttributeId, 654)
        self.assertEqual(modifier.location, Location.space)
        self.assertEqual(modifier.filterType, FilterType.skill)
        self.assertEqual(modifier.filterValue, 3326)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryPassive(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 0)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.offline)
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryActive(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 1)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.active)
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryTarget(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 2)
        self.assertEqual(status, EffectBuildStatus.error)
        self.assertEqual(len(modifiers), 0)
        self.assertEqual(len(self.log), 1)

    def testEffCategoryArea(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 3)
        self.assertEqual(status, EffectBuildStatus.error)
        self.assertEqual(len(modifiers), 0)
        self.assertEqual(len(self.log), 1)

    def testEffCategoryOnline(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 4)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.online)
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryOverload(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 5)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.overload)
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryDungeon(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 6)
        self.assertEqual(status, EffectBuildStatus.error)
        self.assertEqual(len(modifiers), 0)
        self.assertEqual(len(self.log), 1)

    def testEffCategorySystem(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionID'], self.eRmMod['expressionID'], 7)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.offline)
        self.assertEqual(modifier.context, Context.gang)
        self.assertEqual(len(self.log), 0)
