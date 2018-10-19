# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from .base_model_ import Model
from .. import util


class InlineResponse204(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, data: object=None, error: object=None):  # noqa: E501
        """InlineResponse204 - a model defined in OpenAPI

        :param data: The data of this InlineResponse204.  # noqa: E501
        :type data: object
        :param error: The error of this InlineResponse204.  # noqa: E501
        :type error: object
        """
        self.openapi_types = {
            'data': object,
            'error': object
        }

        self.attribute_map = {
            'data': 'data',
            'error': 'error'
        }

        self._data = data
        self._error = error

    @classmethod
    def from_dict(cls, dikt) -> 'InlineResponse204':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_204 of this InlineResponse204.  # noqa: E501
        :rtype: InlineResponse204
        """
        return util.deserialize_model(dikt, cls)

    @property
    def data(self) -> object:
        """Gets the data of this InlineResponse204.


        :return: The data of this InlineResponse204.
        :rtype: object
        """
        return self._data

    @data.setter
    def data(self, data: object):
        """Sets the data of this InlineResponse204.


        :param data: The data of this InlineResponse204.
        :type data: object
        """

        self._data = data

    @property
    def error(self) -> object:
        """Gets the error of this InlineResponse204.


        :return: The error of this InlineResponse204.
        :rtype: object
        """
        return self._error

    @error.setter
    def error(self, error: object):
        """Sets the error of this InlineResponse204.


        :param error: The error of this InlineResponse204.
        :type error: object
        """

        self._error = error
