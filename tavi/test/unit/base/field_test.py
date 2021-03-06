# -*- coding: utf-8 -*-
import unittest
from tavi.base.fields import BaseField
from tavi.errors import Errors


class BaseFieldTest(unittest.TestCase):
    def setUp(self):
        self.field = BaseField("my_field")

    def test_has_a_name(self):
        self.assertEqual("my_field", self.field.name)

    def test_sets_default_value_for_required_attribute(self):
        self.assertFalse(self.field.required, "expected required to be False")

    def test_sets_default_value_for_default_attribute(self):
        self.assertIsNone(self.field.default)

    def test_supports_required_attribute(self):
        class Target(object):
            f = BaseField("my_field", required=True)
            errors = Errors()

        t = Target()
        t.f = None
        self.assertEqual(["My Field is required"], t.errors.full_messages)

        t.f = 42
        self.assertEqual(0, t.errors.count)

    def test_supports_default_value(self):
        class Target(object):
            f = BaseField("my_field", default=1)
            errors = Errors()

        t = Target()
        self.assertEqual(1, t.f)
        t.f = 42
        self.assertEqual(42, t.f)

    def test_validates_choices(self):
        class Target(object):
            f = BaseField("my_field", choices=['type_a', 'type_b'])
            errors = Errors()

        t = Target()
        t.f = "not a choice"
        self.assertEqual(
            ["My Field value must be in list"],
            t.errors.full_messages
        )

        t.f = "type_a"
        self.assertEqual(0, t.errors.count)

    def test_accepts_a_persist_keyword_argument(self):
        class Target(object):
            f = BaseField("my_field", persist=False)
            errors = Errors()

        Target()

    def test_multiple_fields_do_not_share_attributes(self):
        another_field = BaseField("another_field")
        self.assertEqual("my_field", self.field.name)
        self.assertEqual("another_field", another_field.name)

    def test_default_value_is_validated(self):
        class TestField(BaseField):
            def validate(self, instance, value):
                super(TestField, self).validate(instance, value)
                if value == -1:
                    instance.errors.add(self.name, "value cannot be -1")

        class Target(object):
            afield = TestField("afield", default=-1)
            errors = Errors()

        t = Target()

        self.assertEqual(-1, t.afield)
        self.assertEqual(1, t.errors.count)

    def test_default_value_is_set_if_field_is_required(self):
        class Target(object):
            f = BaseField("my_field", default=1, required=True)
            errors = Errors()

        t = Target()
        t.f = None
        self.assertEqual(1, t.f)
