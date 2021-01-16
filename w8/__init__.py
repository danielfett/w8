import struct
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, Tuple
from gi.repository import GObject

import gatt
import logging


class CommandNotFinishedException(Exception):
    pass


@dataclass
class W8Command:
    opcode: int
    response_format: str = ""
    response_contents: Tuple = tuple()
    request_format: str = ""
    request_contents: Tuple = tuple()


class W8DeviceManager(gatt.DeviceManager):
    w8_devices: Dict = {}

    def __init__(self, timeout, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger("Device Manager")
        self.log.debug("Started.")
        GObject.timeout_add_seconds(timeout, self.stop)

    def add_device(self, mac_address):
        self.log.debug("Adding device...")
        device = W8Device(
            cb_ready=self.cb_ready,
            cb_error=self.cb_error,
            cb_disconnect=self.cb_disconnect,
            mac_address=mac_address,
            manager=self,
        )
        self.w8_devices[mac_address] = device
        device.connect()
        return device

    def device_discovered(self, device):
        if device.alias() == "W8CARAVAN" and device.mac_address not in self.w8_devices:
            self.log.info(
                f"Discovered matching device with address {device.mac_address}"
            )
            self.add_device(device.mac_address)
        else:
            self.log.info(
                f"Found other device, alias={device.alias()} mac={device.mac_address}"
            )


class W8Device(gatt.Device):
    TIMEOUT = timedelta(seconds=5)
    COMMANDS: Dict[str, W8Command] = {
        # example response:
        # 490a4f000000b95beb5f00000000cc10f401e803
        # 0 1 2 3 4 5 6 7 8 9 1
        #                     0 1 2 3 4 5 6 7 8 9
        "READ_DATASET": W8Command(
            opcode=0x49,
            response_format="<IQHHHhhhBB",
            response_contents=(
                "serial",
                "uptime",
                "measured_weight",
                "tara_weight",
                "full_weight",
                "acc_x",
                "acc_y",
                "acc_z",
                "temperature",
                "flags",
            ),
        ),
        # example response:
        # 430a7c15f82a
        # 0 1 2 3 4 5 6
        #
        "READ_SETTINGS": W8Command(
            opcode=0x43,
            response_format="<HH",
            response_contents=("tara_weight", "full_weight"),
        ),
        # example response:
        # 530a0064a461eb5f00000000
        # 0 1 2 3 4 5 6 7 8 9 1
        #                     0 1 2
        "READ_STATUS": W8Command(
            opcode=0x53,
            response_format="<BBQ",
            response_contents=("unknown_1", "battery_percent", "uptime",),
        ),
        # example request:
        # 420abbbbcccc
        # 0 1 2 3 4 5 6
        "WRITE_SETTINGS": W8Command(
            opcode=0x42,
            request_contents=("tara_weight", "full_weight"),
            request_format="<HH",
        ),
    }
    cb_command_result: Optional[Callable] = None
    cb_ready: Callable

    command_started: Optional[datetime] = None
    command_expected: Optional[W8Command] = None
    response_buffer: Optional[bytes] = None

    def __init__(self, cb_ready, cb_error, cb_disconnect, *args, **kwargs):
        self.cb_ready = cb_ready
        self.cb_error = cb_error
        self.cb_disconnect = cb_disconnect
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(f"Device [{self.mac_address}]")
        self.log.info("Created")

    def connect_succeeded(self):
        super().connect_succeeded()
        self.log.info("Connected")

    def connect_failed(self, error):
        super().connect_failed(error)
        self.log.info(f"Connection failed: {error}")
        self.cb_error(self, error)

    def _connect(self):
        self.log.debug("Connecting... ")
        super()._connect()

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        del self.manager.w8_devices[self.mac_address]
        self.log.info("Disconnected")
        self.cb_disconnect(self)

    def services_resolved(self):
        super().services_resolved()

        self.log.debug("Resolved services")
        for service in self.services:
            self.log.debug(f"Service [{service.uuid}]")
            for characteristic in service.characteristics:
                self.log.debug(f"   Characteristic [{characteristic.uuid}]")
                if characteristic.uuid.startswith("00001235"):
                    # Properties: Write without response
                    # Handle: 0x000b
                    # Writes only go to this char.
                    self.write_characteristic = characteristic
                if characteristic.uuid.startswith("00001236"):
                    # Properties: Notify, Read
                    # Handle: 0x000d
                    # Reads only come from this char.
                    characteristic.enable_notifications()
        self.cb_ready(self)

    def reset_command_buffer(self, started=None, expected=None):
        self.command_started = started
        self.command_expected = expected
        self.command_identified = None
        self.response_buffer = None

    def timeout_command(self):
        if self.command_started is None:
            # no command running - nothing to do
            pass
        else:
            if self.command_started < datetime.now() - self.TIMEOUT:
                self.reset_command_buffer()
                self.log.error("Timed out while expecting response.")

    def run_command(self, command_name: str, callback: Callable, *params):
        self.timeout_command()
        if self.command_started is not None:
            raise CommandNotFinishedException(
                "Previous command has not finished processing yet."
            )
        self.cb_command_result = callback
        command = self.COMMANDS[command_name]
        preambel_bytes = bytes([command.opcode, 0x0A])
        parameters_bytes = struct.pack(command.request_format, *params,)
        self.reset_command_buffer(datetime.now(), command)
        self.log.info(f"Sending command {command.opcode}")
        self.write_characteristic.write_value(preambel_bytes + parameters_bytes)

    def characteristic_value_updated(self, characteristic, value):
        self.log.debug(f"Received response: {value.hex()}")
        self.timeout_command()
        if self.response_buffer is None:
            self.log.debug("Assuming first message in batch.")
            # This must be the first message in a batch.
            if value[1] != 0x0A:
                raise Exception(
                    "Unexpected message received. "
                    "Reason: First message in batch, but 2nd byte is not 0x0A. "
                )
            # This must be the proper response.
            if value[0] != self.command_expected.opcode:
                raise Exception(
                    "Unexpected message received. "
                    f"Reason: Expected opcode {self.command_expected.opcode}, but received opcode {value[0]}. "
                )
            self.response_buffer = value[2:]
            self.try_process_message()
        else:
            self.log.debug("Assuming follow-up message.")
            # This must be a follow-up message
            self.response_buffer += value
            self.try_process_message()

    def try_process_message(self):
        self.log.debug(f"Processing message {self.response_buffer.hex()}")
        expected_length = struct.calcsize(self.command_expected.response_format)
        if len(self.response_buffer) < expected_length:
            self.log.debug(
                f"Received incomplete message ({len(self.response_buffer)} < {expected_length})."
            )
            return None
        else:
            self.log.debug("Finished message.")
        if len(self.response_buffer) > expected_length:
            self.log.error(
                f"Received {len(self.response_buffer) - expected_length} "
                f"extra bytes: (message) {self.response_buffer[:expected_length]} "
                f"+ (extra) {self.response_buffer[expected_length:]}"
            )
        command = self.command_expected

        dataset = dict(
            zip(
                command.response_contents,
                struct.unpack(command.response_format, self.response_buffer),
            )
        )
        self.reset_command_buffer()
        self.cb_command_result(self, dataset)
        return True
