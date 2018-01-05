#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2015 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module that provides the Attribute class


"""
#from __future__ import absolute_import

__entity_classes__ = ("entity", "architecture", "configuration", "package",
                      "procedure", "function", "type", "subtype",
                      "constant", "signal", "variable", "file",
                      "component", "label", "literal", "units",
                      "group", "property", "sequence")


__registered_type_mark__ = {}

def register_new_type_mark(type_mark, expression_func, validate_func=lambda x:True):
    __registered_type_mark__[type_mark] = (expression_func, validate_func)

__registered_attributes__ = []

def Attribute(identifier, type_mark="string"):
    for attr in __registered_attributes__ :
        if attr._is_same(identifier, type_mark) :
            return attr
    attr = _Attribute(identifier, type_mark)
    __registered_attributes__.append(attr)
    return attr

def get_Attributes():
    return __registered_attributes__


class _Attribute():
    def __init__(self, identifier, type_mark="string"):
        type_mark = type_mark.lower()
        if type_mark not in __registered_type_mark__ :
            raise ValueError("type_mark '{}' not managed".format(type_mark))
        self._identifier = identifier
        self._type_mark = type_mark
        self._expression_func = __registered_type_mark__[self._type_mark][0]
        self._validate_func = __registered_type_mark__[self._type_mark][1]
        self._specs = []

    def register(self, obj, value, entity_class="signal"):
        entity_class = entity_class.lower()
        if not entity_class in __entity_classes__ :
            raise ValueError("Illegal entity_class '{}'".format(entity_class))
        self._validate_func(value)
        self._specs.append((obj, value, entity_class))
    
    def get_spec_list(self, get_obj_name_func):
        specs = []
        for s in self._specs :
            obj, value, entity_class = s
            str_value = self._expression_func(value)
            entity_name = get_obj_name_func(obj)
            if entity_name :
                specs.append("attribute %s of %s : %s is %s;" % (self._identifier, entity_name, entity_class, str_value))
        return specs
   
    def __str__(self):
        return "attribute %s : %s;" % (self._identifier, self._type_mark)

#     def get_specification_str(self, entity_name, entity_class, value):
#         str_value = self.expression_func(value)
#         return "attribute %s of %s : %s is %s;" % (self._identifier, entity_name, entity_class.lower(), str_value)
#     
#     def validate_entity_class(self, entity_class):
#         return entity_class.lower() in __entity_classes__
#         
#     def validate_value(self, value):
#         return self.validate_func(value)
    
    def _is_same(self, identifier, type_mark):
        if identifier.lower() == self._identifier.lower() :
            if type_mark.lower() == self._type_mark :
                return True
        return False
    
# Register string type mark
def string_expression(value):
    return '"%s"' % value
def string_validate(value):
    if not isinstance(value, str) :
        raise TypeError("value ({}) must be a string".format(value))
register_new_type_mark("string", string_expression, string_validate)