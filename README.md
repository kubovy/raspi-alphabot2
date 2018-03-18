# Raspberry Pi Zero Alphabot 2 Controll System

## MQTT API

The general convention of the topics follows the following format: `[service_name]/[state|control]/[module]/#`

Every state change SHOULD be accompanied by a `[service_name]/state/#` message published to the broker.

### General

* `[service_name]/state/status`

  is triggered when the robot get online/offline. This topic is also publish with the payload `OFF` as the robot's _last
  will_.

  | Payload  | Description      |
  | -------- | ---------------- |
  | `ON`     | Robot is online  |
  | `OFF`    | Robot is offline |

### Buzzer

This module controls the buzzer and responds to `[service_name]/control/buzzer/#` topic messages.

*  `[service_name]/state/buzzer`

  is triggered when the buzzer changes its state.

  | Payload  | Description   |
  | -------- | ------------- |
  | `ON`     | Buzzer is on  |
  | `OFF`    | Buzzer is off |

* `[service_name]/control/buzzer`

  controls the buzzer's state.

  | Payload  | Description     |
  | -------- | --------------- |
  | `ON`     | Sets buzzer on  |
  | `OFF`    | Sets buzzer off |


### Camera Servos

* `[service_name]/state/camera/[servo]/raw`

  is triggered when the camera roll or pitch is changed. Payload is the _RAW_ value of the servo's setting.

  | `servo`  | Description     |
  | -------- | --------------- |
  | `0`      | Roll Servo      |
  | `1`      | Pitch Servo     |

* `[service_name]/state/camera/[servo]/percent`

  is triggered when the camera roll or pitch is changed. Payload is the _PERCENTAGE_ value of the servo's setting
  between the defined _minumum_ and _maximum_ value defined for each servo - _minimum_ value equals 0%, _maximum_
  value equals 100%. The _minimum_ value corresponds to most left setting for roll and most down setting for pitch.
  The _maximum_ value corresponds to most right setting for roll and most up setting for pitch.

  | `servo`  | Description     |
  | -------- | --------------- |
  | `0`      | Roll Servo      |
  | `1`      | Pitch Servo     |

* `[service_name]/control/camera/[servo]/[type]`

  controls the servo's setting. If the value is in `percent` then the _minimum_ value equals 0%, _maximum_
  value equals 100%. If the value is in `degrees` then the _minimum_ value equals -90° and the _maximum_ value equals
  90°. The _minimum_ value corresponds to most left setting for roll and most down setting for pitch.
  The _maximum_ value corresponds to most right setting for roll and most up setting for pitch.

  | `servo`         | Description     |
  | --------------- | --------------- |
  | `0` or `roll`   | Roll Servo      |
  | `1` or `pitch`  | Pitch Servo     |

  | `type`     | Description             |
  | ---------- | ----------------------- |
  | `deg`      | Payload in degrees      |
  | `percent`  | Payload in percent      |
  | _NOTHING_  | Payload as _RAW_ value  |

### IR Sensor

* `[service_name]/state/ir`

  is triggered when IR code is received. The payload is the received IR code.

* `[service_name]/state/ir/state`

  is triggered when the IR receiver is switched on or off.

  | Payload  | Description     |
  | -------- | --------------- |
  | `ON`     | IR sensor is on  |
  | `OFF`    | IR sensor is off |


* `[service_name]/state/ir/control`

  is triggered when the IR receiver control mode is set on or off.

  | Payload  | Description     |
  | -------- | --------------- |
  | `ON`     | IR sensor control mode is on  |
  | `OFF`    | IR sensor control mode is off |

* `[service_name]/control/ir`

  set the state of the IR sensor

  | Payload   | Description     |
  | --------- | --------------- |
  | `ON`      | Turns the IR sensor on  |
  | `CONTROL` | Turns the IR sensor on in control mode  |
  | `OFF`     | Turns the IR sensor off |

### Joystick

* `[service_name]/state/joystick`

  is triggered when the joystick state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `NONE`    | Default position  |
  | `UP`      | Pushed up         |
  | `DOWN`    | Pushed down       |
  | `RIGHT`   | Pushed right      |
  | `LEFT`    | Pushed left       |
  | `CENTER`  | Center pushed     |


* `[service_name]/state/joystick/center`

  is triggered when the joystick's center state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `ON`      | Center pushed     |
  | `OFF`     | Center released   |


* `[service_name]/state/joystick/up`

  is triggered when the joystick's up state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `ON`      | Up pushed     |
  | `OFF`     | Up released   |

* `[service_name]/state/joystick/right`

  is triggered when the joystick's right state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `ON`      | Right pushed     |
  | `OFF`     | Right released   |

* `[service_name]/state/joystick/down`

  is triggered when the joystick's down state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `ON`      | Down pushed     |
  | `OFF`     | Down released   |

* `[service_name]/state/joystick/left`

  is triggered when the joystick's left state changes.

  | Payload   | Description       |
  | --------- | ----------------- |
  | `ON`      | Left pushed     |
  | `OFF`     | Left released   |

* `[service_name]/state/joystick/state`

  is triggered when the joystick's state changes.

  | Payload   | Description          |
  | --------- | -------------------- |
  | `ON`      | Joystick is enabled  |
  | `OFF`     | Joystick is disabled |

* `[service_name]/state/joystick/control`

  is triggered when the joystick's control state changes.

  | Payload   | Description     |
  | --------- | --------------- |
  | `ON`      | Turns the IR sensor on  |
  | `CONTROL` | Turns the IR sensor on in control mode  |
  | `OFF`     | Turns the IR sensor off |


* `[service_name]/control/joystick/state`

  set the state of the joystick.

  | Payload   | Description     |
  | --------- | --------------- |
  | `ON`      | Turns the Joystick on  |
  | `OFF`     | Turns the Joystick off |

* `[service_name]/control/joystick/control`

  set the control state of the joystick sensor

  | Payload    | Description                          |
  | ---------- | ------------------------------------ |
  | `NONE`     | Joystick control is disabled         |
  | `CAMERA`   | Joystick is controlling the camera   |
  | `MOVEMANT` | Joystick is controlling the movement |


### Pixels

* `[service_name]/state/led/[pixel]`
* `[service_name]/control/led`
* `[service_name]/control/led/[pixel]`


### TR Sensor

* `[service_name]/state/tr`
* `[service_name]/state/tr/measuring`
* `[service_name]/state/tr/delay`
* `[service_name]/control/tr`

### Ultrasonic Sensor

* `[service_name]/state/distance`
* `[service_name]/state/distance/measuring`
* `[service_name]/state/distance/delay`
* `[service_name]/control/distance`

### Wheels

* `[service_name]/state/move`
* `[service_name]/state/move/left`
* `[service_name]/state/move/right`
* `[service_name]/control/move/[direction]`
* `[service_name]/control/rotate/[direction]`
* `[service_name]/control/turn/[direction]`
* `[service_name]/control/stop`

