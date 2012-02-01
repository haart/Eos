#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2012 Anton Vorobyov
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


"""
This file holds IDs of multiple Eos-specific entities.
"""


class State:
    """
    Possible item states, used as part of public API and
    internally by Info class and classes interacting with it
    """
    # Values assigned to states are not deliberate, they must
    # be in ascending order. It means that e.g. online module
    # state, which should trigger modules' online and offline
    # effects/infos, must have higher value than offline, and
    # so on.
    offline = 1
    online = 2
    active = 3
    overload = 4


class Slot:
    # TODO: add more sensible docstring here
    """All slot types items can take"""
    moduleHigh = 1  #
    moduleMed = 2
    moduleLow = 3
    rig = 4
    subsystem = 5
    turret = 6
    launcher = 7

# Class used by Infos and Item definitions
class Location:
    """
    Location specification, often relative, thus item
    context must be taken into account. Used only
    internally by Info class, item classes and calculation
    engine in general.
    """
    self_ = 1  # Self, i.e. carrier of modification source
    character = 2  # Character
    ship = 3  # Ship
    target = 4  # Currently locked and selected target
    other = 5  # If used from charge, refers charge's container, if used from container, refers its charge
    area = 6  # No detailed data about this one, according to expressions, it affects everything on grid (the only expression using it is area-of-effect repair, but it's not assigned to any effects)
    space = 7  # Target stuff in space (e.g. your launched drones and missiles); this location is Eos-specific and not taken from EVE


class Context:
    """
    Describes when modification is applied, used only internally
    by Info class and classes interacting with it
    """
    local = 1  # Fit-local modification
    gang = 2  # Gang-wide modification
    projected = 3  # Modification which is applied only when its holder is projected onto something


class RunTime:
    """
    Modification runtime ID holder, used only internally
    by Info class and classes interacting with it
    """
    duration = 1  # Applies modification over duration
    pre = 2  # Instant modification, applied in the beginning of the cycle
    post = 3  # Instant modification, applied in the end of the cycle


class FilterType:
    """
    Filter type ID holder, used only internally
    by Info class and classes interacting with it
    """
    all_ = 1  # Affects all items in target location
    group = 2  # Affects items in target location with additional filter by group
    skill = 3  # Affects items in target location with additional filter by skill requirement


class Operator:
    """
    Operator ID holder, used only internally
    by Info class and classes interacting with it
    """
    # Following operators are used in modifications
    # applied over some duration. We can deliberately assign
    # these some ID, but we need to make sure they're sorted
    # in the order they're kept here by python for proper
    # attribute calculation process
    preAssignment = 1
    preMul = 2
    preDiv = 3
    modAdd = 4
    modSub = 5
    postMul = 6
    postDiv = 7
    postPercent = 8
    postAssignment = 9
    # Following operators are for immediate modification
    increment = 10
    decrement = 11
    assignment = 12


class SourceType:
    """
    Source value type ID holder, used only internally
    by Info class and classes interacting with it
    """
    attribute = 1  # Source value is reference to attribute via ID, whose value should be used for modification
    value = 2  # Source value is actual value for modification


class Type:
    """
    Eos-specific type declarations, used only internally
    by Info class and classes interacting with it
    """
    self_ = -1  # Refers carrier of info, special type ID, thus it must not overlap with any real type ID
