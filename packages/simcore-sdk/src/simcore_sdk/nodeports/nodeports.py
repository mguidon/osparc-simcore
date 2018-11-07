"""this module allows to get the data to import from the connected previous nodes and to set the
    data going to following nodes.
"""
import logging
from pathlib import Path

from simcore_sdk.nodeports import (data_items_utils, dbmanager, exceptions,
                                   serialization)
from simcore_sdk.nodeports._data_items_list import DataItemsList
from simcore_sdk.nodeports._items_list import ItemsList
from simcore_sdk.nodeports._schema_items_list import SchemaItemsList

log = logging.getLogger(__name__)

def _check_payload_schema(payloads, schemas):
    if len(payloads) != len(schemas):
        if len(payloads) > len(schemas):
            raise exceptions.InvalidProtocolError(None, msg="More payload than schemas!")


#pylint: disable=C0111, R0902
class Nodeports:
    """This class allow the client to access the inputs and outputs assigned to the node."""
    _version = "0.1"
    #pylint: disable=R0913
    def __init__(self, version: str, input_schemas: SchemaItemsList=None, output_schemas: SchemaItemsList=None, 
                                    input_payloads: DataItemsList=None, outputs_payloads: DataItemsList=None):
        log.debug("Initialising Nodeports object with version %s, inputs %s and outputs %s", version, input_payloads, outputs_payloads)
        if self._version != version:
            raise exceptions.WrongProtocolVersionError(self._version, version)

        if not input_schemas:
            input_schemas = SchemaItemsList()
        self._input_schemas = input_schemas
        if not output_schemas:
            output_schemas = SchemaItemsList()
        self._output_schemas = output_schemas

        if input_payloads is None:
            input_payloads = DataItemsList()
        self._inputs_payloads = input_payloads
        _check_payload_schema(self._inputs_payloads, self._input_schemas)

        if outputs_payloads is None:
            outputs_payloads = DataItemsList()
        self._outputs_payloads = outputs_payloads
        _check_payload_schema(self._outputs_payloads, self._output_schemas)


        self._inputs = ItemsList(self._input_schemas, self._inputs_payloads)
        self._outputs = ItemsList(self._output_schemas, self._outputs_payloads)
        self._inputs.get_node_from_node_uuid_cb = self.get_node_from_node_uuid
        self._outputs.change_notifier = self.save_to_json
        self._outputs.get_node_from_node_uuid_cb = self.get_node_from_node_uuid

        self.db_mgr = None
        self.autoread = False
        self.autowrite = False

        log.debug("Initialised Nodeports object with version %s, inputs %s and outputs %s", version, input_payloads, outputs_payloads)

    @property
    def inputs(self) -> ItemsList:
        log.debug("Getting inputs with autoread: %s", self.autoread)
        if self.autoread:
            self.update_from_json()
        return self._inputs

    @inputs.setter
    def inputs(self, value):
        # this is forbidden
        log.debug("Setting inputs with %s", value)
        raise exceptions.ReadOnlyError(self._inputs)
        #self.__inputs = value

    @property
    def outputs(self) -> ItemsList:
        log.debug("Getting outputs with autoread: %s", self.autoread)
        if self.autoread:
            self.update_from_json()
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        # this is forbidden
        log.debug("Setting outputs with %s", value)
        raise exceptions.ReadOnlyError(self._outputs)
        #self.__outputs = value

    async def get(self, item_key: str):
        try:
            return await self.inputs[item_key].get()
        except exceptions.UnboundPortError:
            # not available try outputs
            pass
        # if this fails it will raise an exception
        return await self.outputs[item_key].get()
    
    async def set(self, item_key: str, item_value):
        try:
            await self.inputs[item_key].set(item_value)
        except exceptions.UnboundPortError:
            # not available try outputs
            pass
        # if this fails it will raise an exception
        return await self.outputs[item_key].set(item_value)
    
    async def set_file_by_keymap(self, item_value:Path):
        for output in self.outputs:
            if data_items_utils.is_file_type(output.type):
                if output.fileToKeyMap:
                    if item_value.name in output.fileToKeyMap:
                        await output.set(item_value)
                        return
        raise exceptions.PortNotFound(msg="output port for item {item} not found".format(item=str(item_value)))

    def update_from_json(self):
        log.debug("Updating json configuration")
        if not self.db_mgr:
            raise exceptions.NodeportsException("db manager is not initialised")
        updated_nodeports = serialization.create_from_json(self.db_mgr)
        # copy from updated nodeports
        # pylint: disable=W0212
        self._input_schemas = updated_nodeports._input_schemas
        self._output_schemas = updated_nodeports._output_schemas
        self._inputs_payloads = updated_nodeports._inputs_payloads
        self._outputs_payloads = updated_nodeports._outputs_payloads

        self._inputs = ItemsList(self._input_schemas, self._inputs_payloads)
        self._outputs = ItemsList(self._output_schemas, self._outputs_payloads)
        self._inputs.get_node_from_node_uuid_cb = self.get_node_from_node_uuid
        self._outputs.change_notifier = self.save_to_json
        self._outputs.get_node_from_node_uuid_cb = self.get_node_from_node_uuid
        log.debug("Updated json configuration")

    def save_to_json(self):
        log.info("Saving Nodeports object to json")
        serialization.save_to_json(self)

    def get_node_from_node_uuid(self, node_uuid):
        if not self.db_mgr:
            raise exceptions.NodeportsException("db manager is not initialised")
        return serialization.create_nodeports_from_uuid(self.db_mgr, node_uuid)


_db_manager = dbmanager.DBManager()
# create initial Simcore object
PORTS = serialization.create_from_json(_db_manager, auto_read=True, auto_write=True)
