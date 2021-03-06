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


class Attribute:
    """Class-holder for attribute metadata"""

    def __init__(self, attributeId=None, maxAttributeId=None,
                 defaultValue=None, highIsGood=None, stackable=None):
        self.id = attributeId

        # When value of this attribute is calculated on any item, it cannot
        # be bigger than value of attribute referenced by maxAttributeId
        self.maxAttributeId = maxAttributeId

        # Default value of this attribute, used when base attribute value
        # is not available on item during calculation process
        self.defaultValue = defaultValue

        # Boolean describing if it's good when attribute is high or not,
        # used in calculation process
        self.highIsGood = bool(highIsGood) if highIsGood is not None else None

        # Boolean which defines if attribute can be stacking penalized (False)
        # or not (True)
        self.stackable = bool(stackable) if stackable is not None else None
