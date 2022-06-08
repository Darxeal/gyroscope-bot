# Gyroscope Bot

A custom Rocket League bot ([RLBot](http://rlbot.org/)) that you can control with your smartphone's gyroscope.

![gif](showcase.gif)

The best way to have fun with it is on custom rings maps.

Here's a video of me trying to use it on _Panic's Air Race_: https://youtu.be/5xSMyHJ8Ixc

Note that the video is not a replay, I'm "spectating" the bot in **soft-attach** intentionally. Otherwise it's much harder to control because most of the time your perspective of your smartphone doesn't match your view of the car!

## How it works

The bot hosts a local [Flask](https://flask.palletsprojects.com/en/2.1.x/) server with [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/). You can access your PC's local IP in your smarthphone's browser, and the frontend uses the [DeviceOrientation API](https://developer.mozilla.org/en-US/docs/Web/API/Window/deviceorientation_event) to read your phone's orientation and sends it to the bot via websockets.

Sometimes and especially at the beginning the orientation of the car and your phone might not be synced. That's why there is a big button on the frontend - hold it, orient your phone so that it matches your view of the car, and release.

More controls if needed:
- `alt` - boost
- `x` - jump