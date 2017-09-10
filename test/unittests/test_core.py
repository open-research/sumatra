"""
Unit tests for the sumatra.core module
"""

import unittest

from sumatra.core import _Registry as Registry


class TestRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = Registry.__new__(Registry)  # hack to create new instance for each test
        self.registry.__init__()

    class ComponentBaseType(object):

        required_attributes = ["quaeck", "swim"]

    class ConcreteType(ComponentBaseType):
            name = "ItsName"
            quaeck = True

            def swim(self):
                pass

    def test_always_returns_same_instance(self):
        for unused in range(10):
            self.assertEquals(Registry(), Registry())

    def test_registry_empty_at_startup(self):
        self.assertEquals(len(self.registry.components), 0)

    def test_registry_can_add_classes_as_component_types(self):
        self.registry.add_component_type(self.ComponentBaseType)

    def test_cannot_add_classes_without_required_attributes_attribute(self):
        self.assertRaises(TypeError, self.registry.add_component_type, str)

    def test_registry_can_register_classes_for_base_types(self):
        self.registry.add_component_type(self.ComponentBaseType)
        self.registry.register(self.ConcreteType)
        self.assertEquals(len(self.registry.components), 1)
        self.assertEquals(len(self.registry.components[self.ComponentBaseType]), 1)

    def test_registers_classes_with_their_name_attribute(self):
        self.registry.add_component_type(self.ComponentBaseType)
        self.registry.register(self.ConcreteType)
        self.assertIn(self.ConcreteType.name, self.registry.components[self.ComponentBaseType])

    def test_registers_classes_without_name_attribute_with_their_cls_name(self):
        class TypeWithoutNameAttribute(self.ComponentBaseType):
            quaeck = True
            swim = False
        self.registry.add_component_type(self.ComponentBaseType)
        self.registry.register(TypeWithoutNameAttribute)
        self.assertIn("TypeWithoutNameAttribute", self.registry.components[self.ComponentBaseType])

    def test_registry_can_not_register_classes_without_base_type(self):
        self.assertRaises(TypeError, self.registry.register, self.ConcreteType)
        self.assertEquals(len(self.registry.components), 0)

    def test_rejects_classes_not_correctly_implementing_base_type(self):
        class InvalidType(self.ComponentBaseType):
            pass
        self.assertRaises(TypeError, self.registry.register, InvalidType)
        self.assertEquals(len(self.registry.components), 0)

    def test_returns_registered_types(self):
        self.registry.add_component_type(self.ComponentBaseType)
        self.registry.register(self.ConcreteType)
        self.assertEquals(self.registry.components[self.ComponentBaseType][self.ConcreteType.name],
                          self.ConcreteType)
