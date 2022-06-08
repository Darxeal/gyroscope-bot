import math
import pathlib
import threading
import keyboard
from flask import Flask, render_template
from flask_socketio import SocketIO

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.game_state_util import Vector3, Rotator, Physics, CarState, GameState, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from rlutilities.linear_algebra import axis_to_rotation, euler_to_rotation, vec3, mat3, dot, look_at
from rlutilities.simulation import Game
from rlutilities.mechanics import Reorient


def forward(ori: mat3) -> vec3:
    return vec3(ori[0, 0], ori[1, 0], ori[2, 0])


def up(ori: mat3) -> vec3:
    return vec3(ori[0, 2], ori[1, 2], ori[2, 2])


class GyroscopeBot(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.game = Game()
        self.initial_car_forward = vec3()
        self.initial_phone_forward = vec3()
        self.target_forward = vec3(0, 0, 1)
        self.target_up = vec3(0, 1, 0)
        self.prev_counter = -1

    def run_flask(self):
        app = Flask(__name__)
        socketio = SocketIO(app)

        @app.route("/")
        def index():
            return render_template("index.html")

        @socketio.on('orientation')
        def handle_orientation(data):
            # https://developer.mozilla.org/en-US/docs/Web/API/Window/deviceorientation_event
            pitch = (data["beta"]) / 180 * math.pi
            yaw = -(data["alpha"]) / 180 * math.pi
            roll = (data["gamma"]) / 180 * math.pi

            phone_orientation = euler_to_rotation(vec3(pitch, yaw, roll))
            phone_forward = forward(phone_orientation)
            phone_up = up(phone_orientation)

            my_car = self.game.cars[self.index]

            # store orientations when player releases the reset button on their phone
            if data["counter"] > self.prev_counter:
                self.prev_counter = data["counter"]
                self.initial_car_forward = my_car.forward()
                self.initial_phone_forward = forward(phone_orientation)

            initial_phone_angle = math.atan2(self.initial_phone_forward.y, self.initial_phone_forward.x)
            initial_car_angle = math.atan2(self.initial_car_forward.y, self.initial_car_forward.x)
            relative_angle = initial_car_angle - initial_phone_angle

            self.target_forward = dot(axis_to_rotation(vec3(z=relative_angle)), phone_forward)
            self.target_up = dot(axis_to_rotation(vec3(z=relative_angle)), phone_up)

        asset_folder = pathlib.Path(__file__).parent.absolute() / "assets"
        try:
            socketio.run(app, host="0.0.0.0", keyfile=asset_folder/"key.pem", certfile=asset_folder/"cert.pem", port=443)
        except Exception as e:
            print(e)

    def initialize_agent(self):
        self.game.read_field_info(self.get_field_info())

        self.flask_thread = threading.Thread(target=self.run_flask)
        self.flask_thread.start()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.game.read_packet(packet)

        # hold the bot in place for showcase/testing purposes
        if packet.game_info.is_round_active:
            self.set_game_state(GameState(cars={self.index: CarState(physics=Physics(
                location=Vector3(0, -2000, 500),
                velocity=Vector3(0, 0, 0),
            ))}))

        car = self.game.cars[self.index]
        reorient = Reorient(car)
        reorient.target_orientation = look_at(
            forward=self.target_forward,
            # up=dot(axis_to_rotation(car.forward() * 0.5), car.up())  # freestyling
            up=self.target_up
        )
        reorient.step(self.game.time_delta)
        
        self.renderer.draw_line_3d(car.position, car.position + self.target_forward * 130, self.renderer.cyan())
        self.renderer.draw_line_3d(car.position, car.position + car.forward() * 130, self.renderer.red())
        self.renderer.draw_line_3d(car.position, car.position + self.initial_car_forward * 120, self.renderer.yellow())

        # bindings for jump and boost, keys should not conflict with any ingame spectator controls
        reorient.controls.boost = keyboard.is_pressed("alt")
        reorient.controls.jump = keyboard.is_pressed("x")

        return reorient.controls
