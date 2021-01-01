import argparse
import logging
import json

def run():
    from . import W8Device, W8DeviceManager
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mac", help="Provide device MAC address, disable scanning.", nargs="?"
    )
    parser.add_argument("-v", help="Enable verbose logging.", action="store_true")
    parser.add_argument(
        "--device",
        help="Provide name of bluetooth adapter.",
        default="hci0",
    )
    subparsers = parser.add_subparsers(title="command", dest="command", required=True)

    for command_name, command in W8Device.COMMANDS.items():
        subparser = subparsers.add_parser(command_name.lower())
        for argument in command.request_contents:
            subparser.add_argument(argument, type=int)

    args = parser.parse_args()

    manager = W8DeviceManager(adapter_name=args.device)

    def handle_command_result(device, dataset):
        print(json.dumps(dataset, indent=4))
        device.disconnect()
        manager.stop()

    def handle_error(device, error):
        print(error)
        manager.stop()

    def handle_ready(device):
        command = args.command.upper()
        parameter_values = (
            getattr(args, param_name)
            for param_name in W8Device.COMMANDS[command].request_contents
        )
        device.run_command(command, handle_command_result, *(parameter_values))

    manager.cb_ready = handle_ready
    manager.cb_error = handle_error

    if args.v:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)
    if args.v:
        logging.getLogger().info("Log level raised to DEBUG.")

    if args.mac:
        manager.add_device(args.mac)
    else:
        manager.start_discovery()
    manager.run()