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


from logging import getLogger, ERROR, INFO, WARNING

from eos.data.cache.handler.exception import TypeFetchError, AttributeFetchError, EffectFetchError
from eos.data.cache.object import Attribute, Effect, Type


class Logger:

    def __init__(self):
        self.__knownSignatures = set()
        self.__rootLogger = getLogger('eos_test')
        self.__rootLogger.setLevel(INFO)

    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR

    def error(self, msg, childName=None, signature=None):
        logger = self.__getChildLogger(childName)
        if signature is None:
            logger.error(msg)
        elif not signature in self.__knownSignatures:
            logger.error(msg)
            self.__knownSignatures.add(signature)

    def warning(self, msg, childName=None, signature=None):
        logger = self.__getChildLogger(childName)
        if signature is None:
            logger.warning(msg)
        elif not signature in self.__knownSignatures:
            logger.warning(msg)
            self.__knownSignatures.add(signature)

    def info(self, msg, childName=None, signature=None):
        logger = self.__getChildLogger(childName)
        if signature is None:
            logger.info(msg)
        elif not signature in self.__knownSignatures:
            logger.info(msg)
            self.__knownSignatures.add(signature)

    def __getChildLogger(self, childName):
        if childName is None:
            logger = self.__rootLogger
        else:
            logger = self.__rootLogger.getChild(childName)
        return logger


class CacheHandler:

    def __init__(self):
        self.__typeData = {}
        self.__attributeData = {}
        self.__effectData = {}
        self.__expressionData = {}

    def type_(self, **kwargs):
        type_ = Type(**kwargs)
        if type_.id in self.__typeData:
            raise KeyError(type_.id)
        self.__typeData[type_.id] = type_
        return type_

    def attribute(self, **kwargs):
        attr = Attribute(**kwargs)
        if attr.id in self.__attributeData:
            raise KeyError(attr.id)
        self.__attributeData[attr.id] = attr
        return attr

    def effect(self, **kwargs):
        eff = Effect(**kwargs)
        if eff.id in self.__effectData:
            raise KeyError(eff.id)
        self.__effectData[eff.id] = eff
        return eff

    def getType(self, typeId):
        try:
            return self.__typeData[typeId]
        except KeyError:
            raise TypeFetchError(typeId)

    def getAttribute(self, attrId):
        try:
            return self.__attributeData[attrId]
        except KeyError:
            raise AttributeFetchError(attrId)

    def getEffect(self, effId):
        try:
            return self.__effectData[effId]
        except KeyError:
            raise EffectFetchError(effId)
