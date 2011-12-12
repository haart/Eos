#===============================================================================
# Copyright (C) 2010-2011 Anton Vorobyov
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

import collections
import re

import const

# Several local constants, describing type of the table
table_BASE = 1  # Defines some entity
table_AUX = 2  # Auxiliary table, complements some entity with data or serves as link between several other base tables

# Auxiliary named tuples for use with custom database structure specification
TableSpec = collections.namedtuple("TableSpec", ("columns", "strong"))
ColumnSpec = collections.namedtuple("ColumnSpec", ("fk", "index", "strongvals"))

class EosAdapter(object):
    """
    Adapt data to use in Eos before dumping
    """
    def __init__(self, tables):
        self.tables = tables

    def run(self):
        """Control database refactoring workflow"""
        print("Refactoring database for Eos")
        # Before cleaning database according to specification, run attribute
        # normalization - it will move all attributes to typeattribs table;
        # if it's done after, we may lack some data required for process
        self.__normalize_attrs()
        # Transform literal references to IDs in expressions table too,
        # before required data is removed
        self.__expression_idzing()
        # Run helper method which will be needed for proper autocleanup
        attrcat_attrid_map = self.__define_attrvalue_relationships_hamster()
        # Assign database format specification to object for ease of use and
        # modification on the fly
        self.dbspec = self.__get_dbspec()
        # Delete malformed entries in both structures; also, fill actual data
        # with additional flags taken from custom data specification
        self.__synch_dbinfo()
        # Container to store signs of so-called strong data, such rows are immune to removal
        # Format: {table name: {column index: {exception values}}
        strong_data = {}
        # Fill it with manually specified data
        self.__process_manual_strongs(strong_data)
        # Mark types we want to keep and metadata as strong
        self.__invtypes_pumping(strong_data)
        self.__metadata_pumping(strong_data)
        # Create data structure for removed data, we need it for proper resulting
        # statistics and in case if we want to put something back
        # Format: {table name: {data rows}}
        trashed_data = {}
        # Automatically clean up broken data
        self.__autocleanup(strong_data, trashed_data, attrcat_attrid_map)
        # Print some statistics to know what has been cleaned
        self.__print_stats(trashed_data)

    def __get_dbspec(self):
        """Return specification of data Eos needs"""
        dataspec = {}

        dataspec["dgmattribs"] = TableSpec({}, False)
        dgmattribs = dataspec["dgmattribs"].columns
        dgmattribs["attributeID"] = ColumnSpec(None, False, set())
        dgmattribs["attributeName"] = ColumnSpec(None, False, set())
        #dgmattribs["attributeCategory"] = ColumnSpec(None, False, set())
        dgmattribs["maxAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        #dgmattribs["chargeRechargeTimeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmattribs["defaultValue"] = ColumnSpec(None, False, set())
        dgmattribs["published"] = ColumnSpec(None, False, set())
        dgmattribs["unitID"] = ColumnSpec("eveunits.unitID", False, set())
        dgmattribs["stackable"] = ColumnSpec(None, False, set())
        dgmattribs["highIsGood"] = ColumnSpec(None, False, set())
        dgmattribs["iconID"] = ColumnSpec("icons.iconID", False, set())
        dgmattribs["displayNameID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["dgmeffects"] = TableSpec({}, False)
        dgmeffects = dataspec["dgmeffects"].columns
        dgmeffects["effectID"] = ColumnSpec(None, False, set())
        dgmeffects["effectName"] = ColumnSpec(None, False, set())
        dgmeffects["preExpression"] = ColumnSpec("dgmexpressions.expressionID", False, set())
        dgmeffects["postExpression"] = ColumnSpec("dgmexpressions.expressionID", False, set())
        dgmeffects["effectCategory"] = ColumnSpec(None, False, set())
        dgmeffects["isOffensive"] = ColumnSpec(None, False, set())
        dgmeffects["isAssistance"] = ColumnSpec(None, False, set())
        dgmeffects["durationAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["trackingSpeedAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["dischargeAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["rangeAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["falloffAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["fittingUsageChanceAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmeffects["iconID"] = ColumnSpec("icons.iconID", False, set())

        dataspec["dgmexpressions"] = TableSpec({}, False)
        dgmexpressions = dataspec["dgmexpressions"].columns
        dgmexpressions["expressionID"] = ColumnSpec(None, False, set())
        dgmexpressions["operandID"] = ColumnSpec(None, False, set())
        dgmexpressions["arg1"] = ColumnSpec("dgmexpressions.expressionID", False, set())
        dgmexpressions["arg2"] = ColumnSpec("dgmexpressions.expressionID", False, set())
        dgmexpressions["expressionValue"] = ColumnSpec(None, False, set())
        dgmexpressions["expressionTypeID"] = ColumnSpec("invtypes.typeID", False, set())
        dgmexpressions["expressionGroupID"] = ColumnSpec("invgroups.groupID", False, set())
        dgmexpressions["expressionAttributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())

        dataspec["dgmtypeattribs"] = TableSpec({}, False)
        dgmtypeattribs = dataspec["dgmtypeattribs"].columns
        dgmtypeattribs["typeID"] = ColumnSpec("invtypes.typeID", False, set())
        dgmtypeattribs["attributeID"] = ColumnSpec("dgmattribs.attributeID", False, set())
        dgmtypeattribs["value"] = ColumnSpec(None, False, set())

        dataspec["dgmtypeeffects"] = TableSpec({}, False)
        dgmtypeeffects = dataspec["dgmtypeeffects"].columns
        dgmtypeeffects["typeID"] = ColumnSpec("invtypes.typeID", False, set())
        dgmtypeeffects["effectID"] = ColumnSpec("dgmeffects.effectID", False, set())
        dgmtypeeffects["isDefault"] = ColumnSpec(None, False, set())

        dataspec["eveunits"] = TableSpec({}, False)
        eveunits = dataspec["eveunits"].columns
        eveunits["unitID"] = ColumnSpec(None, False, set())
        eveunits["displayNameID"] = ColumnSpec("trntexts.textID", False, set())
        eveunits["descriptionID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["icons"] = TableSpec({}, False)
        icons = dataspec["icons"].columns
        icons["iconID"] = ColumnSpec(None, False, set())
        icons["iconFile"] = ColumnSpec(None, False, set())

        dataspec["invcategories"] = TableSpec({}, False)
        invcategories = dataspec["invcategories"].columns
        invcategories["categoryID"] = ColumnSpec(None, False, set())
        invcategories["categoryNameID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["invgroups"] = TableSpec({}, False)
        invgroups = dataspec["invgroups"].columns
        invgroups["groupID"] = ColumnSpec(None, False, set())
        invgroups["categoryID"] = ColumnSpec("invcategories.categoryID", False, set())
        invgroups["fittableNonSingleton"] = ColumnSpec(None, False, set())
        invgroups["published"] = ColumnSpec(None, False, set())
        invgroups["iconID"] = ColumnSpec("icons.iconID", False, set())
        invgroups["groupNameID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["invmarketgroups"] = TableSpec({}, False)
        invmarketgroups = dataspec["invmarketgroups"].columns
        invmarketgroups["parentGroupID"] = ColumnSpec("invmarketgroups.marketGroupID", False, set())
        invmarketgroups["marketGroupID"] = ColumnSpec(None, False, set())
        invmarketgroups["marketGroupName"] = ColumnSpec(None, False, set())
        #invmarketgroups["description"] = ColumnSpec(None, False, set())
        invmarketgroups["hasTypes"] = ColumnSpec(None, False, set())
        invmarketgroups["iconID"] = ColumnSpec("icons.iconID", False, set())

        dataspec["invmetagroups"] = TableSpec({}, False)
        invmetagroups = dataspec["invmetagroups"].columns
        invmetagroups["metaGroupID"] = ColumnSpec(None, False, set())
        invmetagroups["metaGroupNameID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["invmetatypes"] = TableSpec({}, False)
        invmetatypes = dataspec["invmetatypes"].columns
        invmetatypes["typeID"] = ColumnSpec("invtypes.typeID", False, set())
        invmetatypes["parentTypeID"] = ColumnSpec("invtypes.typeID", False, set())
        invmetatypes["metaGroupID"] = ColumnSpec("invmetagroups.metaGroupID", False, set())

        dataspec["invtypes"] = TableSpec({}, True)
        invtypes = dataspec["invtypes"].columns
        invtypes["typeID"] = ColumnSpec(None, False, set())
        invtypes["groupID"] = ColumnSpec("invgroups.groupID", False, set())
        invtypes["raceID"] = ColumnSpec(None, False, set())
        invtypes["published"] = ColumnSpec(None, False, set())
        invtypes["marketGroupID"] = ColumnSpec("invmarketgroups.marketGroupID", False, set())
        invtypes["iconID"] = ColumnSpec("icons.iconID", False, set())
        invtypes["typeNameID"] = ColumnSpec("trntexts.textID", False, set())
        invtypes["descriptionID"] = ColumnSpec("trntexts.textID", False, set())

        dataspec["metadata"] = TableSpec({}, False)
        metadata = dataspec["metadata"].columns
        metadata["fieldName"] = ColumnSpec(None, False, set())
        metadata["fieldValue"] = ColumnSpec(None, False, set())

        dataspec["trntexts"] = TableSpec({}, False)
        trntexts = dataspec["trntexts"].columns
        trntexts["textID"] = ColumnSpec(None, False, set())
        trntexts["de"] = ColumnSpec(None, False, set())
        trntexts["en-us"] = ColumnSpec(None, False, set())
        trntexts["ja"] = ColumnSpec(None, False, set())
        trntexts["ru"] = ColumnSpec(None, False, set())

        return dataspec

    def __normalize_attrs(self):
        """Moves attributes defined in type table to type-attribs mapping table"""
        # Map which defines links between types table column names and attrIDs
        attr_map = {"radius": const.attribute_RADIUS,
                    "mass": const.attribute_MASS,
                    "volume": const.attribute_VOLUME,
                    "capacity": const.attribute_CAPACITY}
        # First, compose set of PK tuples which are already in target table
        typeattrs_table = self.tables["dgmtypeattribs"]
        idx_typeattrs_typeid = typeattrs_table.getcolumnidx("typeID")
        idx_typeattrs_attrid = typeattrs_table.getcolumnidx("attributeID")
        idx_typeattrs_value = typeattrs_table.getcolumnidx("value")
        typeattrs_collen = len(typeattrs_table.columns)
        existing_data = set()
        for datarow in typeattrs_table.datarows:
            existing_data.add((datarow[idx_typeattrs_typeid], datarow[idx_typeattrs_attrid]))
        # Now, start working with invtypes table
        types_table = self.tables["invtypes"]
        idx_types_typeid = types_table.getcolumnidx("typeID")
        # Define replacement map, as we're going to update values in types table too
        type_replacements = {}
        # Flag which keeps track of any collision errors
        collisions = False
        # Go through each types table data row
        for datarow in types_table.datarows:
            mutablerow = list(datarow)
            for attrcolname in attr_map:
                # If such typeID-attributeID combination is already in typeattribs table,
                # don't do anything
                if (datarow[idx_types_typeid], attr_map[attrcolname]) in existing_data:
                    collisions = True
                    continue
                idx_types_attr = types_table.getcolumnidx(attrcolname)
                # If source attribute value is 0 or None, also skip such row
                attrval = datarow[idx_types_attr]
                if attrval in {0, None}:
                    continue
                # Initialize data row we're going to append to typeattrs table to 0 values
                typeattr_datarow = list(0 for i in range(typeattrs_collen))
                # Fill it
                typeattr_datarow[idx_typeattrs_typeid] = datarow[idx_types_typeid]
                typeattr_datarow[idx_typeattrs_attrid] = attr_map[attrcolname]
                typeattr_datarow[idx_typeattrs_value] = attrval
                # And add it to target table
                typeattrs_table.datarows.add(tuple(typeattr_datarow))
                # Nullify data source in mutable row
                mutablerow[idx_types_attr] = 0.0
            # When operations on all attributes for given row are done, check if we
            # have made any changes to our mutable row
            replacementrow = tuple(mutablerow)
            if datarow != replacementrow:
                # If we did, fill in replacement map
                type_replacements[datarow] = replacementrow
        # Replace data in types table according to replacement map
        for datarow in type_replacements:
            types_table.datarows.remove(datarow)
            types_table.datarows.add(type_replacements[datarow])
        if collisions is True:
            print("  Key collisions detected during attribute normalization")
        return

    def __expression_idzing(self):
        """Convert all references in expression table to attributes, groups and types to IDs"""
        # Create replacement map which will store old and new data rows
        # Format: {current data row: replacement data row}
        replacement_map = {}
        # Set of entity field names which we're going to use
        idz_datas = (("dgmattribs", "attributeID", "attributeName", "expressionAttributeID", const.operand_DEFATTR),
                     ("invgroups", "groupID", "groupName", "expressionGroupID", const.operand_DEFGRP),
                     ("invtypes", "typeID", "typeName", "expressionTypeID", const.operand_DEFTYPE))
        for idz_data in idz_datas:
            # First, we've got to compose name maps, as expressions can
            # reference using names
            entity_name_id = {}
            entity_name_collisions = set()
            entity_table = self.tables[idz_data[0]]
            idx_entityid = entity_table.getcolumnidx(idz_data[1])
            idx_entityname = entity_table.getcolumnidx(idz_data[2])
            for datarow in entity_table.datarows:
                name = datarow[idx_entityname]
                if not name in entity_name_id:
                    entity_name_id[name] = datarow[idx_entityid]
                else:
                    entity_name_collisions.add(name)
                # Sometimes names with stripped white space symbols are used
                name_stripped = re.sub("\s", "", name)
                if not name_stripped in entity_name_id:
                    entity_name_id[name_stripped] = datarow[idx_entityid]
                else:
                    entity_name_collisions.add(name_stripped)
            # Get column indices for required columns in expression table
            exp_table = self.tables["dgmexpressions"]
            idx_operand = exp_table.getcolumnidx("operandID")
            idx_expvalue = exp_table.getcolumnidx("expressionValue")
            idx_expentity = exp_table.getcolumnidx(idz_data[3])
            # Values which are considered to be empty
            nulls = {None, 0}
            for datarow in exp_table.datarows:
                operand = datarow[idx_operand]
                # Check if we're dealing with the operand referring entity
                # we're working with
                if operand == idz_data[4]:
                    entity = datarow[idx_expentity]
                    val = datarow[idx_expvalue]
                    if entity in nulls and val in entity_name_id:
                        if val in entity_name_collisions:
                            print("  Warning: use of colliding {0} {1} detected, expect errors".format(idz_data[2], val))
                        mutablerow = list(datarow)
                        mutablerow[idx_expentity] = entity_name_id[val]
                        mutablerow[idx_expvalue] = None
                        replacementrow = tuple(mutablerow)
                        replacement_map[datarow] = replacementrow
        # Do actual replacements
        for datarow in replacement_map:
            exp_table.datarows.remove(datarow)
            exp_table.datarows.add(replacement_map[datarow])
        return

    def __synch_dbinfo(self):
        """Synchronize data between data specification and actual database structure"""
        # Just error flag, used for user's convenience
        specerrors = False
        # Detect non-existing tables
        tab404 = set(self.dbspec.iterkeys()).difference(self.tables.iterkeys())
        # If we found any
        if len(tab404) > 0:
            # Remove them from specification container
            for tabname in tab404:
                del self.dbspec[tabname]
            # And inform about it
            plu = "" if len(tab404) == 1 else "s"
            tab404names = ", ".join(sorted(tab404))
            print("  Unable to find specified table{0}: {1}".format(plu, tab404names))
            # Set error flag to True
            specerrors = True
        # Get set of tables to be removed from actual data and get rid of them
        toremove = set(self.tables.iterkeys()).difference(set(self.dbspec.iterkeys()))
        for tabname in toremove:
            del self.tables[tabname]
        # Cycle through remaining tables
        # Sort them for alphabetic table name sorting, this is done for pretty-print
        # in case of any errors (doesn't matter otherwise)
        for tabname in sorted(self.dbspec.iterkeys()):
            table = self.tables[tabname]
            actcolnames = set(col.name for col in table.columns)
            specolnames = set(self.dbspec[tabname].columns.iterkeys())
            # Detect non-existing columns
            col404 = specolnames.difference(actcolnames)
            # If we've got such columns
            if len(col404) > 0:
                # Remove them from specification
                for col in col404:
                    del self.dbspec[tabname].columns[col]
                # Tell user about it
                plu = "" if len(col404) == 1 else "s"
                col404names = ", ".join(sorted(col404))
                print("  Unable to find specified column{0} for table {1}: {2}".format(plu, tabname, col404names))
                # Set error flag to True
                specerrors = True
            # Finally, get rid of unneeded columns in actual data structure
            toremove = actcolnames.difference(self.dbspec[tabname].columns.iterkeys())
            problems = table.removecolumns(toremove)
            # If we had any errors during column  removal, set error flag
            if problems is True:
                specerrors = True

        # Fill foreign key references for all columns according to specification
        # As our data/specification structures are now 'synchronized', we can go
        # through any of them - here we picked data as it's faster and more convenient
        for tabname in self.tables:
            table = self.tables[tabname]
            for column in table.columns:
                # Get FK specification string
                fkspec = self.dbspec[table.name].columns[column.name].fk
                # If it's None, ignore current column
                if fkspec is None:
                    continue
                # Source data column must be integer
                if column.datatype != const.type_INT:
                    print("  Non-integer column {0}.{1} has foreign key reference".format(table.name, column.name))
                    specerrors = True
                    continue
                fkspec = fkspec.split(".")
                # FK specification string must be in table.column format
                if len(fkspec) != 2:
                    print("  Foreign key reference of {0}.{1} is malformed".format(table.name, column.name))
                    specerrors = True
                    continue
                fktabname = fkspec[0]
                fkcolname = fkspec[1]
                # FK target must exist
                if not fktabname in self.tables or self.tables[fktabname].getcolumn(fkcolname) is None:
                    print("  Unable to find foreign key target for {0}.{1} ({2}.{3})".format(table.name, column.name, fktabname, fkcolname))
                    specerrors = True
                    continue
                fktable = self.tables[fktabname]
                fkcolumn = fktable.getcolumn(fkcolname)
                # FK target must be PK
                if fkcolumn.pk is not True:
                    print("  Foreign key target for {0}.{1} ({2}.{3}) is not primary key".format(table.name, column.name, fktabname, fkcolname))
                    specerrors = True
                    continue
                # FK target table must have no other PKs besides targeted
                if len(fktable.getpks()) != 1:
                    print("  Foreign key target for {0}.{1} ({2}.{3}) is not the only primary key in table".format(table.name, column.name, fktabname, fkcolname))
                    specerrors = True
                    continue
                # Store FK value in column field
                column.fk = "{0}.{1}".format(fktable.name, fkcolumn.name)

        # Set index flags for all appropriate columns
        for tabname in sorted(self.dbspec.iterkeys()):
            for colname in self.dbspec[tabname].columns:
                idxize = self.dbspec[tabname].columns[colname].index
                if idxize in (True, False):
                    self.tables[tabname].getcolumn(colname).index = idxize
                # Print error on unexpected values
                else:
                    print("  Corrupted index data for {0}.{1}".format(tabname, colname))

        # Print reminder in case of any errors
        if specerrors is True:
            print("  Please revise data specification")

    def __process_manual_strongs(self, strong_data):
        """Add manually specified strong data to internal temporary storage"""
        # Go through all tables in specifications
        for tabname in self.dbspec:
            table = self.tables[tabname]
            # Container for rows of given table which we're going to
            # mark as strong
            rows2pump = set()
            # All their columns
            for colname in self.dbspec[tabname].columns:
                # Check strong values section
                strong_vals = self.dbspec[tabname].columns[colname].strongvals
                # If it's empty, go on
                if len(strong_vals) == 0:
                    continue
                # Get index of column in question
                colidx = table.getcolumnidx(colname)
                # Go through data rows and see which match to our criterion
                for datarow in table.datarows:
                    # If row matches, add it to strong data set
                    if datarow[colidx] in strong_vals:
                        rows2pump.add(datarow)
            self.__pump_data(table, rows2pump, strong_data)
        return

    def __invtypes_pumping(self, strong_data):
        """Mark some hardcoded invtypes as strong"""
        # Set with categoryIDs we want to keep
        strong_categories = {const.category_SHIP, const.category_MODULE, const.category_CHARGE,
                             const.category_SKILL, const.category_DRONE, const.category_IMPLANT,
                             const.category_SUBSYSTEM}
        # Set with groupIDs we want to keep
        strong_groups = {const.group_EFFECTBEACON}
        # Get indices of group and category columns in group table
        group_table = self.tables["invgroups"]
        idx_groupid = group_table.getcolumnidx("groupID")
        idx_categoryid = group_table.getcolumnidx("categoryID")
        # Go through table data, filling valid groups set according to valid categories
        for datarow in group_table.datarows:
            if datarow[idx_categoryid] in strong_categories:
                strong_groups.add(datarow[idx_groupid])
        # Get typeIDs of items we're going to pump
        type_table = self.tables["invtypes"]
        idx_groupid = type_table.getcolumnidx("groupID")
        # Set-container for strong types
        rows2pump = set()
        for datarow in type_table.datarows:
            if datarow[idx_groupid] in strong_groups:
                rows2pump.add(datarow)
        self.__pump_data(type_table, rows2pump, strong_data)
        return

    def __metadata_pumping(self, strong_data):
        """Protect metadata table from removal"""
        # Set with categoryIDs we want to keep
        metadata_table = self.tables["metadata"]
        self.__pump_data(metadata_table, metadata_table.datarows, strong_data)
        return

    def __autocleanup(self, strong_data, trashed_data, attrcat_attrid_map):
        """Define auto cleanup workflow"""
        # Our first step would be to clean non-strong data
        self.__kill_weak(strong_data, trashed_data)
        # Detect table types, as we'll need them for proper data restore
        # process
        tabletypes = self.__detect_tabletypes()
        # Put all FK links into single dictionary
        src_fk_tgt, tgt_fk_src = self.__make_fk_links()
        # Now, start reanimating all related data in cycle
        # Set flag to True for first cycle
        changed = True
        while(changed):
            # Instantly reset to False, any changes to data should set it back
            changed = False
            changed = self.__reanimate_aux_friends(tabletypes, src_fk_tgt, trashed_data, changed)
            changed = self.__reestablish_broken_relationships(src_fk_tgt, tgt_fk_src, trashed_data, attrcat_attrid_map, changed)
        return

    def __kill_weak(self, strong_data, trashed_data):
        """Trash all data which isn't marked as strong"""
        # Go through all tables
        for tabname in self.tables:
            table = self.tables[tabname]
            rows2trash = set()
            strongrows = strong_data.get(tabname)
            # If it doesn't contain strong rows, kill all data
            if strongrows is None:
                rows2trash.update(table.datarows)
            # Else, filter out our strong rows
            else:
                rows2trash.update(table.datarows.difference(strongrows))
            # Finally, trash all data rows
            self.__trash_data(table, rows2trash, trashed_data)
        return

    def __detect_tabletypes(self):
        """Based on PK and FK data, detects table type"""
        # Create container holding our table type specifications
        type_map = {}
        for tabname in self.tables:
            table = self.tables[tabname]
            # We will judge basing on PK number as one of the factos
            pks = len(table.getpks())
            # If there's no PKs at all or 2+ PKs, then table is auxiliary
            if pks > 1 or pks == 0:
                type_map[tabname] = table_AUX
                continue
            # Even if there's single PK, but it references something else -
            # it means that table contents contain complementary data, thus table is
            # auxiliary too
            for column in table.columns:
                if column.pk is True and column.fk is not None:
                    type_map[tabname] = table_AUX
                    break
            # Additional check to avoid going further, if we already detected
            # type of current table
            if tabname in type_map:
                continue
            # Else, type is base
            type_map[tabname] = table_BASE
        return type_map

    def __make_fk_links(self):
        """Form dictionary to store links between tables in convenient form"""
        # 1:1 source-target relation
        # {source table: {source column: (target table, target column)}}
        src_fk_tgt = {}
        # 1:many target-source relation
        # {target table: {target column: {(source table, source column)}}}
        tgt_fk_src = {}
        # Go through all tables to fill map
        for src_tabname in self.tables:
            src_table = self.tables[src_tabname]
            for src_column in src_table.columns:
                # Columns with no FK are no interest for us
                if src_column.fk is None:
                    continue
                tgt_tabname, tgt_colname = src_column.fk.split(".")
                tgt_table = self.tables[tgt_tabname]
                tgt_column = tgt_table.getcolumn(tgt_colname)
                # Fill source-target map
                if not src_table.name in src_fk_tgt:
                    src_fk_tgt[src_table.name] = {}
                src_fk_tgt[src_table.name][src_column.name] = (tgt_table.name, tgt_column.name)
                # And target-source
                if not tgt_table.name in tgt_fk_src:
                    tgt_fk_src[tgt_table.name] = {}
                if not tgt_column.name in tgt_fk_src[tgt_table.name]:
                    tgt_fk_src[tgt_table.name][tgt_column.name] = set()
                tgt_fk_src[tgt_table.name][tgt_column.name].add((src_table.name, src_column.name))
        return src_fk_tgt, tgt_fk_src


    def __reanimate_aux_friends(self, tabletypes, src_fk_tgt, trashed_data, changed):
        """Restore auxiliary data which is related to data left in the database"""
        # Container for column data, for data re-use
        # Format: {"table.column": set(data)}
        coldata = {}
        # Fill it with data, for columns which are referenced by FKs
        for src_tabname in src_fk_tgt:
            # We won't need data for any source tables besides
            # auxiliary ones, so skip all other types
            if tabletypes[src_tabname] != table_AUX:
                continue
            # Go through all column-FKs in auxiliary table
            for src_colname in src_fk_tgt[src_tabname]:
                # Pick FK target and form full textual specification
                tgt_tabname, tgt_colname = src_fk_tgt[src_tabname][src_colname]
                # We're planning to restore auxiliary data only for
                # strong tables, so skip all others
                tgt_strength = self.dbspec[tgt_tabname].strong
                if tgt_strength is not True:
                    continue
                tgt_spec = "{0}.{1}".format(tgt_tabname, tgt_colname)
                # Get data for target column into single set, but only if it's
                # not yet there
                if not tgt_spec in coldata:
                    tgt_dataset = self.tables[tgt_tabname].getcolumndataset(tgt_colname)
                    coldata[tgt_spec] = tgt_dataset
        # Now, to the actual restore process
        for src_tabname in src_fk_tgt:
            # Skip all non-auxiliary tables
            if tabletypes[src_tabname] != table_AUX:
                continue
            src_table = self.tables[src_tabname]
            # Container for data we're going to restore
            rows2restore = set()
            # Go through all FK columns of out table
            for src_colname in src_fk_tgt[src_tabname]:
                tgt_tabname, tgt_colname = src_fk_tgt[src_tabname][src_colname]
                # Skip non-strong target tables
                tgt_strength = self.dbspec[tgt_tabname].strong
                if tgt_strength is not True:
                    continue
                tgt_spec = "{0}.{1}".format(tgt_tabname, tgt_colname)
                src_colidx = src_table.getcolumnidx(src_colname)
                # For each, check all thrashed data
                for datarow in trashed_data[src_tabname]:
                    src_val = datarow[src_colidx]
                    # If there's no value or it keeps zero, skip this row
                    if src_val in {0, None}:
                        continue
                    # If any of such rows refers existing target row,
                    # mark it as to-be-restored
                    if src_val in coldata[tgt_spec]:
                        rows2restore.add(datarow)
            # Restore rows
            self.__restore_data(src_table, rows2restore, trashed_data)
            # If we actually had something to restore, let others know about it
            if len(rows2restore) > 0:
                changed = True
        return changed

    def __reestablish_broken_relationships(self, src_fk_tgt, tgt_fk_src, trashed_data, attrcat_attrid_map, changed):
        """Restore rows targeted by FKs of actual data"""
        # Container for column data, for data re-use
        # Format: {"table.column": set(data)}
        coldata = {}
        # Fill it with data, for columns which are FKs
        for src_tabname in src_fk_tgt:
            # Go through all column-FKs in auxiliary table
            for src_colname in src_fk_tgt[src_tabname]:
                # Pick FK target and form full textual specification
                src_spec = "{0}.{1}".format(src_tabname, src_colname)
                # Get data for source column into single set
                src_dataset = self.tables[src_tabname].getcolumndataset(src_colname)
                # None and zero values are not actual references according to
                # CCP scheme, so get rid of them
                src_dataset.difference_update({0, None})
                coldata[src_spec] = src_dataset
        # Restore broken plain references; go through all target tables and columns
        for tgt_tabname in tgt_fk_src:
            tgt_table = self.tables[tgt_tabname]
            # Set-container for rows to be restored
            rows2restore = set()
            for tgt_colname in tgt_fk_src[tgt_tabname]:
                # Values which reference given target column are collected here
                src_vals = set()
                # Use our pre-gathered column data set as data source
                for src_tabname, src_colname in tgt_fk_src[tgt_tabname][tgt_colname]:
                    src_spec = "{0}.{1}".format(src_tabname, src_colname)
                    src_vals.update(coldata[src_spec])
                # Finally, go through rows of removed data and mark it as to-be-restored
                # if match happens
                tgt_colidx = tgt_table.getcolumnidx(tgt_colname)
                for datarow in trashed_data[tgt_tabname]:
                    tgt_val = datarow[tgt_colidx]
                    if tgt_val in src_vals:
                        rows2restore.add(datarow)
            # Actual data restore for given table
            self.__restore_data(tgt_table, rows2restore, trashed_data)
            if len(rows2restore) > 0:
                changed = True
        # Restore broken conditional references; first, grab their source values
        special_attrval_links = self.__define_attrvalue_relationships(attrcat_attrid_map)
        # Then follow almost the same approach
        for tgt_tabname in special_attrval_links:
            tgt_table = self.tables[tgt_tabname]
            rows2restore = set()
            for tgt_colname in special_attrval_links[tgt_tabname]:
                # Except for the fact that we already have our data at hand and can use it
                # without additional gathering
                src_vals = special_attrval_links[tgt_tabname][tgt_colname]
                tgt_colidx = tgt_table.getcolumnidx(tgt_colname)
                for datarow in trashed_data[tgt_tabname]:
                    tgt_val = datarow[tgt_colidx]
                    if tgt_val in src_vals:
                        rows2restore.add(datarow)
            # Actually restore rows
            self.__restore_data(tgt_table, rows2restore, trashed_data)
            if len(rows2restore) > 0:
                changed = True
        return changed

    def __define_attrvalue_relationships_hamster(self):
        """Hamster some data before it gets removed, it's needed for primary method"""
        # Format: {attrCategory: {attrID}}
        attrcat_attrid_map = {}
        attr_table = self.tables["dgmattribs"]
        idx_attrid = attr_table.getcolumnidx("attributeID")
        idx_attrcat = attr_table.getcolumnidx("attributeCategory")
        for datarow in attr_table.datarows:
            attrcat = datarow[idx_attrcat]
            if not attrcat in attrcat_attrid_map:
                attrcat_attrid_map[attrcat] = set()
            attrcat_attrid_map[attrcat].add(datarow[idx_attrid])
        return attrcat_attrid_map

    def __define_attrvalue_relationships(self, attrcat_attrid_map):
        """
        Provide additional data of what we need to keep in the database, namely -
        under certain conditions attribute values refer other entities, which we're
        better to keep.
        """
        # Storage for values which actually refer something
        # Format: {table name: {column name: values to restore}}
        special_attrval_links = {}
        # Get indices to work with data in dgmtypeattribs table
        typeattrs_table = self.tables["dgmtypeattribs"]
        idx_attrid = typeattrs_table.getcolumnidx("attributeID")
        idx_value = typeattrs_table.getcolumnidx("value")
        # Some high-level access instructions, what to restore
        conditional_links = {(const.attributeCategory_DEFATTR, "dgmattribs", "attributeID"),
                             (const.attributeCategory_DEFGROUP, "invgroups", "groupID"),
                             (const.attributeCategory_DEFTYPE, "invtypes", "typeID")}
        # Go through each of them
        for entity_attrcat, entity_tabname, entity_colname in conditional_links:
            # Container for attribute IDs which reference corresponding entity
            attrs_entity = attrcat_attrid_map[entity_attrcat]
            # Container for IDs of entities we're going to restore
            referenced_entities = set()
            # Cycle through data rows and see if we get attribute ID match
            for datarow in typeattrs_table.datarows:
                # If we do, write down ID of entity to corresponding set
                if datarow[idx_attrid] in attrs_entity:
                    value = datarow[idx_value]
                    referenced_entities.add(int(value))
            referenced_entities.difference_update({0, None})
            # Store data to dictionary
            if not entity_tabname in special_attrval_links:
                special_attrval_links[entity_tabname] = {}
            special_attrval_links[entity_tabname][entity_colname] = referenced_entities
        return special_attrval_links

    def __print_stats(self, trashed_data):
        """Print statistics about removed data"""
        # Print some statistics
        for tabname in sorted(trashed_data):
            # Get set with removed data
            removed_data = trashed_data.get(tabname)
            removedrows = len(removed_data)
            # If set is empty, don't do anything
            if removedrows == 0:
                continue
            table = self.tables[tabname]
            # Calculate total number of data rows we had in table
            totalrows = len(table.datarows) + removedrows
            # Print jobs
            plu = "" if removedrows == 1 else "s"
            perc = 100.0 * removedrows / totalrows
            print("  Table {0} cleaned: {1} row{2} ({3:.1f}%) removed".format(tabname, removedrows, plu, perc))
        return

    def __pump_data(self, table, datarows, strong_data):
        """Mark data rows as strong"""
        # Check if we got anything useful, bail if we didn't
        if len(datarows) == 0:
            return
        # Create sub-set for table if it doesn't have it yet
        if not table.name in strong_data:
            strong_data[table.name] = set()
        # Actually add data rows
        strong_data[table.name].update(datarows)
        return

    def __trash_data(self, table, datarows, trashed_data):
        """Mark data as removed"""
        # If no data was passed, bail - as usual
        if len(datarows) == 0:
            return
        # Create subset if it's not yet there
        if not table.name in trashed_data:
            trashed_data[table.name] = set()
        totrash = table.datarows.intersection(datarows)
        # Update both trashed data and source data
        trashed_data[table.name].update(totrash)
        table.datarows.difference_update(totrash)
        return

    def __restore_data(self, table, datarows, trashed_data):
        """Mark data as actual, if it is trashed"""
        # If no data was passed, bail - as usual
        if len(datarows) == 0:
            return
        torestore = trashed_data[table.name].intersection(datarows)
        # Update both trashed data and source data
        table.datarows.update(torestore)
        trashed_data[table.name].difference_update(torestore)
        return