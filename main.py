import random

import numpy as np
import pygame
import math

#from pygame.examples.go_over_there import delta_time

# Physics engine will display a screen with multiple objects
# Every object can be defined as having these characteristics: Mass, Velocity, Position

# Constants
# Gravitational Constant
G = 6.67e-11
# Simulation time
current_time = 0
# Real World seconds per frame
dt = 1800
DEBUG = False

# Set up pygame screen
pygame.init()
screen_height = 800
screen_width = 1300
CenterX = screen_width // 2
CenterY = screen_height // 2

# Set up screen
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
center = (screen_width / 2, screen_height / 2)
# size conversions, this is a 0.5e-6 scale model
pixel_scale = 0.5e-6

# Colours definers
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Font
font = pygame.font.Font(None, 30)

# Frame Limiter
FPS = 60

# Images for Play/Pause button
play_image = pygame.image.load('Images/Play.png').convert_alpha()
pause_image = pygame.image.load('Images/Pause.png').convert_alpha()


# Classes
class body:
    def __init__(self, mass, velocity, position, radius, name):
        self.mass = mass
        # Use of NP array so vector calculations can be done
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.acceleration = np.array([0.0, 0.0], dtype=float)
        self.radius = radius
        self.name = name
        self.past_positions = []
        # Calculate a hit box area
        self.hit_box_surface = pygame.Surface(
            (self.radius * 2, self.radius * 2))  # make a surface that is around the object


class menu:
    def __init__(self, height, width, pos):
        self.surface = pygame.Surface((height, width))
        self.surface_position = pos
        self.visible = True
        self.body = None
        self.line_space = 5
        self.line_start = 0
        self.categories = ["Mass:", "Velocity:", "Radius:", "Size:", "Name:"]

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def generate_data(self, body):
        text = ["OBJECT DATA:",
                f'Body: {body.name}',
                f'Mass: {body.mass}kg',
                f'Velocity: {int(np.linalg.norm(body.velocity))}m/s']
        return text

    def add_to_menu(self, text):
        self.surface.fill(BLACK)  # Remove all previous data
        current_y = self.line_start

        for line in text:
            text_surface = font.render(line, True, WHITE)
            self.surface.blit(text_surface, (10, current_y))
            current_y += self.line_space + text_surface.get_height()

    def draw_data_input(self, pos):
        # Draw categories
        self.surface.fill(BLACK)
        current_y = self.line_start
        for category in self.categories:
            text_surface = font.render(category, True, WHITE)
            self.surface.blit(text_surface, (pos, current_y))  # At 10 from the menu surface
            current_y += self.line_space + text_surface.get_height()

    def draw_menu(self):
        if self.visible:
            screen.blit(self.surface, self.surface_position)


def create_new_body(mass, velocity, radius, size, name):
    new_body = body(mass, [0, velocity], [radius, 0], size, name)
    bodies.append(new_body)


def calculate_gravity(bodies):
    # Initialise bodies with no acceleration
    for body in bodies:
        body.acceleration = np.zeros(2, dtype=float)

    for i, body1 in enumerate(bodies):
        # Cycle through all the bodies in the body list
        for j, body2 in enumerate(bodies):
            # Only if the 2 bodies are different, run the calculations
            if i != j:
                # Find vector direction by getting the distance and normalising it
                resultant_vector = body2.position - body1.position  # r = p2-p1 calculates the direction of vector
                resultant_direction = max(np.linalg.norm(resultant_vector),
                                          1e-20)  # Find the direction by normalising vector, set lowest value to 1e-20
                # max(a, b) returns the bigger value, either the calculated value or the set value

                # make sure we are never dealing with negatives
                if resultant_direction > 0:
                    # Use Newtons equation to calculate the force magnitude between the 2 bodies
                    force_magnitude = (G * body1.mass * body2.mass) / (resultant_direction ** 2)
                    # Get the force vector with r^ = r / |r| UNIT vector equation
                    force_vector = force_magnitude * (
                            resultant_vector / resultant_direction)
                    # Apply forces to body F = m * a -> a = F/m
                    body1.acceleration += force_vector / body1.mass

def calculate_gravitational_potential(bodies, toggle_arrows):
    if toggle_arrows:
        for i, body1 in enumerate(bodies):
            for j, body2 in enumerate(bodies):
                if i != j:
                    # Calculate distance and other variables
                    direction = body2.position - body1.position
                    distance = np.linalg.norm(direction)
                    direction_unit_vector = direction / distance

                    mass1 = body1.mass
                    mass2 = body2.mass
                    # Calculate where Phi is 0 by this equation
                    '''
                    Phi = -GM/R1 
                    Phi net = -GM1/R1 - GM2/R2
                    Phi net = 0
                    GM1/R1 = -GM2/R2 --> ignore signs, only worry about magnitudes being equal
                    GM1/R1 = GM2/R2 Remove Like terms
                    M1/R1 = M2/R2  (R1 + R2 = D) Put all in terms of R1
                    M1/R1 = M2/(D - R1) --> M1D - M1R1 = M2R1 --> M1D = M2R1 + M1R1
                    M1D = R1(M2 + M1)
                    final equation
                    R1 = M1D/(M2 + M1) 
                    '''

                    R1 = (distance * mass1) / (mass1 + mass2)

                    zero_point_real = (body1.position + (direction_unit_vector * R1))
                    zero_point_x = zero_point_real[0] * pixel_scale + CenterX
                    zero_point_y = zero_point_real[1] * pixel_scale + CenterY
                    zero_point = (zero_point_x, zero_point_y)
                    begin_point_x = body1.position[0] * pixel_scale + CenterX
                    begin_point_y = body1.position[1] * pixel_scale + CenterY
                    begin_point = (begin_point_x, begin_point_y)

                    # Draw an arrow
                    DrawArrow(begin_point, zero_point, (body1.radius + body2.radius)//2)


def update_bodies(bodies, dt):
    for body in bodies:
        # use suvat to solve for new speed
        body.velocity += body.acceleration * dt  # v=u+at
        # update position with suvat
        body.position += body.velocity * dt  # s=s1 + s2 (s2 = v * dt)


def draw_body(bodies):
    for body in bodies:
        # Find where body would be on screen based on pixel scale
        body_x = int(body.position[0] * pixel_scale) + CenterX
        body_y = int(body.position[1] * pixel_scale) + CenterY

        # Trajectory tracking
        if trajectories_on and not paused:
            body.past_positions.append([body.position[0], body.position[1]])
            if len(body.past_positions) > 500:
                body.past_positions.pop(0)
        if not trajectories_on:
            body.past_positions = []


        # Calculate a hit box area
        hit_box_rect = body.hit_box_surface.get_rect(
            center=(body_x, body_y))  # Centre the rectangle at the bodies coordinates
        body.hit_box_rect = hit_box_rect
        pygame.draw.circle(screen, WHITE, (body_x, body_y),
                           body.radius)  # The scale of the object is determined by mass


def check_planet_hitboxes(bodies, pos):
    for body in bodies:
        hitbox_rect = body.hit_box_surface.get_rect(center=(int(body.position[0] * pixel_scale) + CenterX,
                                                            int(body.position[
                                                                    1] * pixel_scale) + CenterY))  # find the rectangle for that surface
        # Collidepoint() checks if the event was on the rectangle
        if hitbox_rect.collidepoint(pos):
            return True, body
    return False, None


def draw_pause_buttons():
    if paused:
        screen.blit(pause_image, (50, 50))
    else:
        screen.blit(play_image, (50, 50))


def on_pause(pos):
    if 50 <= pos[0] <= 120 and 50 <= pos[1] <= 120:
        return True


def name_bodies(bodies):
    for body in bodies:
        name = body.name
        text_surface = font.render(name, True, WHITE)
        text_x = (body.position[0] * pixel_scale) + CenterX
        text_y = (body.position[1] * pixel_scale) + CenterY
        screen.blit(text_surface, (text_x + body.radius, text_y - 2 * body.radius))


def draw_clock(new_time):
    # Days
    days = new_time // 86400
    new_time %= 86400

    # Hours
    hours = new_time // 3600
    new_time %= 3600

    clock_text = f' T+ {days}:Days  {hours}:Hours'
    clock_surface = font.render(clock_text, True, WHITE)
    screen.blit(clock_surface, (screen_width * 0.75, 70))


def draw_input_boxes(x, y):
    current_y = y
    input_boxes = []
    for i in range(5):
        input_box_rect = pygame.Rect(x, current_y - 4, 100, 26)
        pygame.draw.rect(screen, RED, pygame.Rect(x, current_y - 4, 100, 26), 2)
        input_boxes.append(input_box_rect)
        current_y += 29
    return input_boxes


def display_input_numbers(x, y):
    current_y = y
    mass_surface = font.render(mass_text, True, WHITE)
    velocity_surface = font.render(velocity_text, True, WHITE)
    radius_surface = font.render(radius_text, True, WHITE)
    size_surface = font.render(size_text, True, WHITE)
    name_surface = font.render(name_text, True, WHITE)

    surfaces = [mass_surface, velocity_surface, radius_surface, size_surface, name_surface]

    for surface in surfaces:
        screen.blit(surface, (x, current_y))
        current_y += 29

def TimeWarpForward(dt):
    dt *= 2
    return dt
def TimeWarpBackward(dt):
    dt /= 2
    return dt

def DrawArrow(beginPoint, endPoint, scale):
    # Define locals
    end = endPoint
    dx = endPoint[0] - beginPoint[0]
    dy = endPoint[1] - beginPoint[1]
    angle = math.atan2(dy, dx)

    # Calculate the two arrowhead lines (forming a small triangle)
    left_x = end[0] - scale * math.cos(angle - math.pi / 6) * 5
    left_y = end[1] - scale * math.sin(angle - math.pi / 6) * 5
    right_x = end[0] - scale * math.cos(angle + math.pi / 6) * 5
    right_y = end[1] - scale * math.sin(angle + math.pi / 6) * 5

    # First drw the line from point to point
    pygame.draw.line(screen, pygame.Color('blue'), beginPoint, endPoint, scale)
    # Draw arrow head
    pygame.draw.polygon(screen, pygame.Color('blue'), [(end[0], end[1]), (left_x, left_y), (right_x, right_y)])

def DrawTrajectories(bodies):
    for body in bodies:
        # For every point in the trajectory point draw a line
        for i in range(len(body.past_positions) - 1):
            pygame.draw.line(screen, pygame.Color('white'),
                             ((body.past_positions[i][0] * pixel_scale) + CenterX, (body.past_positions[i][1] * pixel_scale) + CenterY),
                             ((body.past_positions[i+1][0] * pixel_scale) + CenterX, (body.past_positions[i+1][1] * pixel_scale)+ CenterY), body.radius//2)

def LockPlanet(body, locked):
    global CenterX
    global CenterY
    global offset_x
    global offset_y

    if locked and body != None:
        CenterX = -(body.position[0] * pixel_scale) + screen_width / 2 + offset_x
        CenterY = -(body.position[1] * pixel_scale) + screen_height / 2 + offset_y


if __name__ == '__main__':
    # Main

    # Class definitions

    # Bodies
    Earth = body(5.24e24, [0, 0], [0, 0], 10, "Earth")
    Minmus = body(3.5e22, [0, -600], [-900000000, 0], 2, "Minmus")
    Moon = body(7.37e22, [0, -954], [-384000000, 0], 6, "Moon")
    Asteroid = body(27.0e6, [0, 760], [600000000, 0], 2, "Asteroid 1")
    Asteroid1 = body(27.0e6, [0, 660], [500000000, 0], 2, "Asteroid 2")
    Asteroid2 = body(27.0e6, [0, 660], [400000000, 0], 2, "Asteroid 3")
    GeoSat = body(120, [0, 2940], [40430423, 0], 1, "Geo Sat")
    Sun = body(1.989e30, [0, 0], [0, 0], 20, "The Sun")
    Moon2 = body(7.37e22, [0, 954 + 29785], [1.496e11 + 384000000, 0], 2, "Moon")
    Mercury = body(3.30e23, [0, 47360], [5.79e10, 0], 2, "Mercury")
    Venus = body(4.87e24, [0, 35020], [1.08e11, 0], 2, "Venus")
    Earth2 = body(5.97e24, [0, 29780], [1.496e11, 0], 2, "Earth")
    Mars = body(6.42e23, [0, 24070], [2.28e11, 0], 2, "Mars")
    Jupiter = body(1.90e27, [0, 13070], [7.78e11, 0], 5, "Jupiter")
    Saturn = body(5.68e26, [0, 9680], [1.43e12, 0], 4, "Saturn")
    Uranus = body(8.68e25, [0, 6800], [2.87e12, 0], 3, "Uranus")
    Neptune = body(1.02e26, [0, 5430], [4.50e12, 0], 3, "Neptune")
    Phobos = body(1.07e16, [0, 24070 + 2138], [2.28e11 + 9.376e6 , 0], 2, "Phobos")
    Deimos = body(1.48e15, [0, 24070 + 1350], [2.28e11 + 2.346e7, 0], 2, "Deimos")
    # Menus
    # 0.666 and 0.75 are static screen size percentages to make sure they work on any screen size, ignore
    data_menu = menu(350, 600, (50, screen_height * 0.666))
    input_menu = menu(350, 600, (screen_width * 0.75, screen_height * 0.666))
    input_boxes = []


    # Systems
    # System1
    #bodies = [Earth, Moon, Asteroid, Asteroid1, Asteroid2, Minmus, GeoSat]
    # System 2
    #bodies = [Earth, Moon]
    # System 3
    #bodies = [Earth, Moon, Asteroid, Asteroid1, Asteroid2]
    # System 4
    bodies = [Sun, Mercury, Venus, Earth2, Moon2, Mars, Phobos, Deimos, Jupiter, Saturn, Neptune]
    # Empty Sys
    #bodies = []
    '''
    for i in range(50):
        bodies.append(
            body(5.24e24, [0, 0], [
                random.randint(0,2000000000000), random.randint(0,200000000000)
            ], 10, "Earth")
        )
    '''

    # Initialise variables
    selected_planet = None
    planet_locked = False
    trajectories_on = True
    mouse_dragging = False
    toggle_arrows = False
    shifting = False
    running = True
    paused = True
    input_menu.visible = False
    current_box = -1
    last_mouse_pos = None
    mass_text = ""
    velocity_text = ""
    radius_text = ""
    size_text = ""
    name_text = ""
    offset_x = 0
    offset_y = 0

    # Extras
    trajectory_list = []

    while running:

        # Fill Background
        screen.fill(BLACK)
        # Lock FPS to 60
        clock.tick(FPS)

        # Calculate Physics
        if not paused:
            calculate_gravity(bodies)
            # Update Physics
            update_bodies(bodies, dt)


        # Handle Events

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            # If event is Quit
            if event.type == pygame.QUIT:
                running = False

            # Check Mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check Pause Button
                if on_pause(mouse_pos):
                    if paused:
                        paused = False
                    else:
                        paused = True

                else:
                    # Check if body is selected
                    # Check Hitboxes return True, the body
                    if check_planet_hitboxes(bodies, event.pos)[0]:
                        # Make menu visable
                        data_menu.show()
                        # Display the bodies data
                        selected_planet = check_planet_hitboxes(bodies, event.pos)[1]
                        # If Shifting lock onto the planet
                        if shifting:
                            planet_locked = True
                            # Lock with the returned planet
                        else:
                            planet_locked = False

                    else:
                        # Hide menu if you click anywhere else
                        data_menu.hide()

                    # Check if a box was hit
                    box_clicked = False
                    for i, box in enumerate(input_boxes):
                        if box.collidepoint(event.pos):
                            current_box = i
                            box_clicked = True
                        if not box_clicked:
                            current_box = -1  # Points to Null Box



            # Check keyboard

            # Check If the input shows or hides the input menus
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SEMICOLON:
                    input_menu.show()
                if event.key == pygame.K_QUOTE:
                    input_menu.hide()

                # Toggle shifting
                if event.key == pygame.K_LSHIFT:
                    shifting = True

                # Show/Hide Trajectories:
                if event.key == pygame.K_BACKSLASH:
                    trajectories_on = not trajectories_on
                    trajectory_list = []
                # Show/Hide Potential Arrows
                if event.key == pygame.K_PERIOD:
                    toggle_arrows = not toggle_arrows
                # Time Warping
                if event.key == pygame.K_RIGHTBRACKET:
                    dt = TimeWarpForward(dt)
                if event.key == pygame.K_LEFTBRACKET:
                    dt = TimeWarpBackward(dt)
                if event.key == pygame.K_SLASH:
                    dt = 1800
                # Move around the screen
                if event.key == pygame.K_TAB:
                    CenterX = screen_width // 2
                    CenterY = screen_height // 2
                    planet_locked = False
                    selected_planet = None
                    offset_x = 0
                    offset_y = 0

                if event.key == pygame.K_UP:
                    if planet_locked:
                        offset_y += 50
                    else:
                        CenterY += 50
                if event.key == pygame.K_DOWN:
                    if planet_locked:
                        offset_y -= 50
                    else:
                        CenterY -= 50
                if event.key == pygame.K_LEFT:
                    if planet_locked:
                        offset_x += 50
                    else:
                        CenterX += 50
                if event.key == pygame.K_RIGHT:
                    if planet_locked:
                        offset_x -= 50
                    else:
                        CenterX -= 50

                # Zooming with shift
                if event.key == pygame.K_EQUALS:
                    if shifting:
                        pixel_scale *= 2
                    else:
                        pixel_scale += 0.005e-6
                if event.key == pygame.K_MINUS:
                    if shifting:
                        pixel_scale /= 2
                    else:
                        pixel_scale -= 0.005e-6

                # find the box to enter inputs into
                # Handle the display text
                # Handle backspace for the current box
                if event.key == pygame.K_BACKSPACE:
                    if current_box == 0:
                        mass_text = mass_text[:-1]
                    elif current_box == 1:
                        velocity_text = velocity_text[:-1]
                    elif current_box == 2:
                        radius_text = radius_text[:-1]
                    elif current_box == 3:
                        size_text = size_text[:-1]
                    elif current_box == 4:
                        name_text = name_text[:-1]
                elif event.key != pygame.K_RETURN:
                    if current_box == 0:
                        mass_text += event.unicode
                    elif current_box == 1:
                        velocity_text += event.unicode
                    elif current_box == 2:
                        radius_text += event.unicode
                    elif current_box == 3:
                        size_text += event.unicode
                    elif current_box == 4:
                        name_text += event.unicode

                # If the Enter key is pressed make a new body
                if event.key == pygame.K_RETURN:
                    if mass_text == "" or velocity_text == "" or radius_text == "" or size_text == "" or name_text == "":
                        pass
                    else:
                        create_new_body(mass=float(mass_text),
                                        velocity=float(velocity_text),
                                        radius=float(radius_text),
                                        size=int(size_text),
                                        name=str(name_text))
                        # reset the strings
                        mass_text = ""
                        velocity_text = ""
                        radius_text = ""
                        size_text = ""
                        name_text = ""

            # Untoggle shifting
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    shifting = False





        # Display handling

        # Draw menus
        data_menu.draw_menu()
        input_menu.draw_menu()

        # Draw planets and their data
        # Draw arrows
        calculate_gravitational_potential(bodies, toggle_arrows)
        draw_body(bodies)
        DrawTrajectories(bodies)
        # Draw body names
        name_bodies(bodies)

        # Update the data menu data
        if data_menu.visible and selected_planet is not None:
            text = data_menu.generate_data(selected_planet)
            data_menu.add_to_menu(text)

        if input_menu.visible:
            # 0.83 and 0.65 are screen offsets to allow any screen size, ignore them
            input_menu.draw_data_input(0)
            input_boxes = draw_input_boxes(screen_width * 0.83, screen_height * 0.65)
            display_input_numbers(screen_width * 0.83, screen_height * 0.65)

        # Button Handling
        draw_pause_buttons()

        # Time handling
        # Update time, if simulation is paused increment normal delta time
        # If paused, delta time is 0
        if not paused:
            # Update time
            current_time += dt
        if paused:
            current_time += 0

        # Update Simulation Clock
        draw_clock(current_time)

        # DEBUGGING
        if DEBUG:
            print(shifting)

        # Lock now
        # Planet Locking
        LockPlanet(selected_planet, planet_locked)

        # Update next frame of simulation
        pygame.display.flip()
