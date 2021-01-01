# w8.py - Brunner W8 GasControl Tool
Software for reading and programming the [Brunner W8 GasControl](https://www.w8system.it) gas scale. 

Software zum Auslesen und Programmieren der [Brunner W8 GasControl Gaswaage](https://www.w8system.it). 

**Note:** This software is not supported or endorsed by Brunner and in no way affiliated with the original manufacturer of the device. The information used for the creation of the software and presented below was acquired by observing bluetooth messages. The use of this software is at your own risk. It is possible that the software may damage your hardware. The author assumes no liability in case of damage. See [license](LICENSE) for details.


## Usage

Installation:

```
pip3 install git+https://github.com/danielfett/w8.git
```

Running the software:
```
$ w8 read_dataset
INFO:Device Manager:Discovered matching device with address e5:bb:49:af:ff:b5
INFO:Device [e5:bb:49:af:ff:b5]:Created
INFO:Device [e5:bb:49:af:ff:b5]:Connected
INFO:Device [e5:bb:49:af:ff:b5]:Sending command 73
{
    "serial": 122,
    "uptime": 3005,
    "measured_weight": 300,
    "tara_weight": 5500,
    "full_weight": 11000,
    "acc_x": 0,
    "acc_y": 0,
    "acc_z": 24,
    "temperature": 21,
    "flags": 12
}
```

Without additional parameters, the command starts scanning for bluetooth devices until one with the name "W8CARAVAN" is found. 
The command waits until a matching device is found. To stop the search, press Ctrl+C. It is possible to specify the MAC address of the scale manually:

```
$ w8 --mac e5:bb:49:af:ff:b5 read_settings
```


## Enabling Bluetooth LE

If the above command does not work out-of-the-box, you might have to enable Bluetooth Low-Energy. 

On Ubuntu, add the following two lines at the bottom of `/etc/bluetooth/main.conf`:

```
EnableLE=true
AttributeServer=true
```

Then restart bluetooth: `sudo service bluetooth restart`


## On the Raspberry Pi

This software works on a Raspberry Pi and was tested with the built-in bluetooth device. To use the software as the user `pi` (recommended!), you need to make the dbus policy changes [described here](https://www.raspberrypi.org/forums/viewtopic.php?t=108581#p746917).

## Available commands

### `read_dataset`

Reads a weight measurement from the scale. Data fields returned:

| Field               | Description                                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `serial`              | Serial number of the request/response. Seems to be incremented for each command issued.                                                           |
| `uptime`              | Uptime, probably in seconds.                                                                                                                      |
| `measured_weight`     | Current weight on the scale, calibrated to show 0 when nothing is on the scale. The tara setting does not influence this value.                   |
| `tara_weight`         | Tara weight as programmed into the scale.                                                                                                         |
| `full_weight`         | Full weight as programmed.                                                                                                                        |
| `acc_x`, `acc_y`, `acc_z` | Some scales seem to have an accelleration sensor to cancel out effects of a sloped mount of the scale. For me, the values returned were constant. |
| `temperature`         | Temperature of the scale.                                                                                                                         |
| `flags`               | Flags, meaning yet unknown.                                                                                                                       |

### `read_settings`

Read the tara and full weight settings. Data fields returned:

| Field       | Description                        |
| ----------- | ---------------------------------- |
| `tara_weight` | Tara weight in grams.              |
| `full_weight` | Full weight (gas weight) in grams. |

### `write_settings`

Write the tara and full weight settings. Expects two parameters, see **`read_settings`** for details.


### `read_status`

Read the status of the scale. Data fields returned:

| Field           | Description                             |
| --------------- | --------------------------------------- |
| `unknown_1`       | Unknown field.                          |
| `battery_percent` | Battery capacity estimation in percent. |
| `uptime`          | Uptime, probably in seconds.            |



## License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.