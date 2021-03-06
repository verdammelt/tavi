# -*- coding: utf-8 -*-
"""Provides various field types."""
import re
import collections
import datetime
from bson import ObjectId
from pymongo.errors import InvalidId
from tavi import EmbeddedList
from tavi.base.fields import BaseField
from tavi.documents import EmbeddedDocument
from tavi.errors import TaviTypeError


class BooleanField(BaseField):
    """Represents a boolean field for a Mongo Document. Supports all the
    validations of *BaseField*.

    """
    def validate(self, instance, value):
        super(BooleanField, self).validate(instance, value)

        if value and not isinstance(value, bool):
            instance.errors.add(self.name, "must be a valid boolean")


class DateTimeField(BaseField):
    """Represents a naive datetime for a Mongo Document.
    Supports all the validations in *BaseField*.

    """
    def validate(self, instance, value):
        """Validates the field."""
        super(DateTimeField, self).validate(instance, value)

        if None != value and not isinstance(value, datetime.datetime):
            instance.errors.add(self.name, "must be a valid date and time")


class FloatField(BaseField):
    """Represents a floating point number for a Mongo Document.

    Supports all the validations in *BaseField* and the following:

    min_value -- validates the minimum value the field value can be
    max_value -- validates the maximum value the field value can be

    """
    def __init__(self, name, min_value=None, max_value=None, **kwargs):
        super(FloatField, self).__init__(name, **kwargs)

        self.min_value = None if None == min_value else float(min_value)
        self.max_value = None if None == max_value else float(max_value)

    def validate(self, instance, value):
        """Validates the field."""
        super(FloatField, self).validate(instance, value)

        if None != value:
            if isinstance(value, int):
                value = float(value)

            if not isinstance(value, float):
                instance.errors.add(self.name, "must be a float")

            if not None == self.min_value and value < self.min_value:
                instance.errors.add(
                    self.name,
                    "is too small (minimum is %s)" % self.min_value
                )

            if not None == self.max_value and value > self.max_value:
                instance.errors.add(
                    self.name,
                    "is too big (maximum is %s)" % self.max_value
                )


class IntegerField(BaseField):
    """Represents a integer number for a Mongo Document.

    Supports all the validations in *BaseField* and the following:

    min_value -- validates the minimum value the field value can be
    max_value -- validates the maximum value the field value can be

    """
    def __init__(self, name, min_value=None, max_value=None, **kwargs):
        super(IntegerField, self).__init__(name, **kwargs)

        self.min_value = None if None == min_value else int(min_value)
        self.max_value = None if None == max_value else int(max_value)

    def validate(self, instance, value):
        """Validates the field."""
        super(IntegerField, self).validate(instance, value)

        if None != value:
            if not isinstance(value, int):
                instance.errors.add(self.name, "must be a integer")

            if not None == self.min_value and value < self.min_value:
                instance.errors.add(
                    self.name,
                    "is too small (minimum is %s)" % self.min_value
                )

            if not None == self.max_value and value > self.max_value:
                instance.errors.add(
                    self.name,
                    "is too big (maximum is %s)" % self.max_value
                )


class ObjectIdField(BaseField):
    """Represents an Object Id generated by Mongo. Supports all the validations
    in *BaseField*.

    """
    def __set__(self, instance, raw_value):
        if raw_value is not None:
            try:
                value = ObjectId(raw_value)
            except InvalidId:
                value = raw_value
        else:
            value = None

        super(ObjectIdField, self).__set__(instance, value)

    def validate(self, instance, value):
        """Validates the field."""
        super(ObjectIdField, self).validate(instance, value)

        if value is not None:
            if not isinstance(value, ObjectId):
                instance.errors.add(self.name, "must be a valid Object Id")


class StringField(BaseField):
    """Represents a String field for a Mongo Document.

    Supports all the validations in *BaseField* and the following:

    length     -- validates the field value has an exact length; default is
                  *None*

    min_length -- ensures field has a minimum number of characters; default is
                  *None*

    max_length -- ensures field is not more than a maximum number of
                  characters; default is *None*

    pattern    -- validates the field matches the given regular expression
                  pattern; default is *None*

    """
    def __init__(
        self, name,
        length=None, min_length=None, max_length=None, pattern=None,
        **kwargs
    ):

        super(StringField, self).__init__(name, **kwargs)

        self.length = length
        self.min_length = min_length
        self.max_length = max_length
        self.regex = re.compile(pattern) if pattern else None

    def __set__(self, instance, unstripped_value):
        if unstripped_value:
            value = self._ensure_unicode_string(unstripped_value).strip()
        else:
            value = None

        super(StringField, self).__set__(instance, value)

    def _ensure_unicode_string(self, value):
        if not isinstance(value, basestring):
            value = str(value)
        if isinstance(value, str):
            value = unicode(value, "utf-8")
        return value

    def validate(self, instance, value):
        """Validates the field."""
        super(StringField, self).validate(instance, value)
        val_length = len(value) if value else None

        if self.required and '' == value:
            instance.errors.add(self.name, "is required")

        if self.length and self.length != val_length:
            instance.errors.add(
                self.name,
                "is the wrong length (should be %s characters)" % self.length
            )

        if self.min_length and val_length < self.min_length:
            instance.errors.add(
                self.name,
                "is too short (minimum is %s characters)" % self.min_length
            )

        if self.max_length and val_length > self.max_length:
            instance.errors.add(
                self.name,
                "is too long (maximum is %s characters)" % self.max_length
            )

        if self.regex and value and self.regex.match(value) is None:
            instance.errors.add(self.name, "is in the wrong format")


class EmbeddedField(BaseField):
    """Represents an embedded Mongo document. Raises a TaviTypeError if *doc*
    is not a tavi.document.EmbeddedDocument.

    """
    def __init__(self, name, doc, **kwargs):
        super(EmbeddedField, self).__init__(name, **kwargs)
        doc_instance = doc()

        if not isinstance(doc_instance, EmbeddedDocument):
            raise TaviTypeError(
                "expected %s to be a subclass of "
                "tavi.document.EmbeddedDocument" %
                doc_instance.__class__.__name__
            )

        self.doc_class = doc
        self.value = self.default or doc_instance

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if value:
            if not isinstance(value, EmbeddedDocument):
                raise TaviTypeError(
                    "expected %s to be a subclass of "
                    "tavi.document.EmbeddedDocument" %
                    value.__class__
                )

            if not self.value:
                self.value = self.doc_class()

            for field in value.fields:
                embedded_value = getattr(value, field, None)
                setattr(self.value, field, embedded_value)
        else:
            self.value = value


class ListField(BaseField):
    """Represents a list of embedded document fields."""
    def __init__(self, name, type_, **kwargs):
        super(ListField, self).__init__(name, **kwargs)
        self._type = type_

    def __get__(self, instance, owner):
        if self.attribute_name not in instance.__dict__:
            setattr(
                instance,
                self.attribute_name,
                EmbeddedList(self.name, self._type)
            )
        return getattr(instance, self.attribute_name)

    def __set__(self, instance, value):
        pass


class ArrayField(BaseField):
    """Represents an array field for a Mongo Document.

    Supports all the validations in *BaseField* and the following:

    length        -- validates the field value has an exact length; default is
                     *None*

    min_length    -- ensures field has a minimum number of items; default is
                     *None*

    max_length    -- ensures field is not more than a maximum number of
                     items; default is *None*

    validate_item -- a function which is run against each item in the field.
                     Must accept the ArrayField instance, the Document
                     instance, and the item as arguments.  Default is *None*
    """
    def __init__(
        self, name,
        length=None, min_length=None, max_length=None, pattern=None,
        validate_item=None, **kwargs
    ):
        super(ArrayField, self).__init__(name, **kwargs)

        self.length = length
        self.min_length = min_length
        self.max_length = max_length
        if validate_item is not None and not callable(validate_item):
            raise ValueError("validate_item must be callable or None")
        self.validate_item = validate_item

    def validate(self, instance, value):
        """Validates the field."""
        super(ArrayField, self).validate(instance, value)
        if (value is not None and
                not isinstance(value, collections.MutableSequence)):
            instance.errors.add(self.name, "is not a list.")

        val_length = len(value) if value else None

        if self.required and not value:
            instance.errors.add(self.name, "is required")

        if self.length and self.length != val_length:
            instance.errors.add(
                self.name,
                "is the wrong length (should be %s items)" % self.length
            )

        if self.min_length and val_length < self.min_length:
            instance.errors.add(
                self.name,
                "is too short (minimum is %s items)" % self.min_length
            )

        if self.max_length and val_length > self.max_length:
            instance.errors.add(
                self.name,
                "is too long (maximum is %s items)" % self.max_length
            )

        if self.validate_item and value is not None:
            for item in value:
                self.validate_item(self, instance, item)

    def __get__(self, instance, owner):
        if self.attribute_name not in instance.__dict__:
            setattr(
                instance,
                self.attribute_name,
                []
            )
        return getattr(instance, self.attribute_name) or []
