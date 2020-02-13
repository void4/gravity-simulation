'''
Gravity Simulation
----------------------------
Last Edited: May 15th. 2017
By Hiroya Gojo
'''
import math
from math import log
import os
import pygame
import pygame.gfxdraw
import random
import sys

# Background Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
DARK_RED = (156, 43, 43)
LIGHT_GRAY = (40, 40, 40)
DARK_GRAY = (15, 15, 15)

# Initialize for program
pygame.init()
WIDTH = 128*2#4096#1920#256*2
HEIGHT = 128*2#4096#1080#256*2

size = (WIDTH, HEIGHT)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Gravity Simulation - Hiroya")

# Font and text
pygame.font.init()
font_type = "Times New Roman"
text_font_large = pygame.font.SysFont(font_type, 20)
text_font = pygame.font.SysFont(font_type, 15)
text_font_small = pygame.font.SysFont(font_type, 13)

text_space = text_font.render("Space to Restart", False, WHITE)
text_z = text_font.render("Z for path", False, WHITE)
text_x = text_font.render("X for border", False, WHITE)
text_c = text_font.render("C for color", False, WHITE)
text_s = text_font.render("Q to speed up", False, WHITE)
text_a = text_font.render("A to slow down", False, WHITE)
text_d = text_font.render("W for more mass", False, WHITE)
text_f = text_font.render("S for less mass", False, WHITE)
text_g = text_font.render("E for more objects", False, WHITE)
text_h = text_font.render("D for less objects", False, WHITE)
text_p = text_font.render("P to pause/unpause", False, WHITE)
text_o = text_font.render("O to save", False, WHITE)
text_i = text_font.render("I to hide UI", False, WHITE)

# Status messages
text_pause = text_font_large.render("Paused", False, DARK_RED)
text_saved = text_font.render("Saved!", False, DARK_RED)
text_error = text_font.render("Error encountered.", False, DARK_RED)

clock = pygame.time.Clock()
random.seed()

# Create objects and variable declarations
objects = []
file_position_x = []
file_position_y = []
number_of_objects = 1
start_mass = 50
SIM = 0
SIM_FIXED = 1
SIM_STEPS = 150
SIM_STEP_INC = 150
SIM_SEQUENTIAL = False
SIM_X = 7
SIM_Y = 25
game_speed = SIM_STEPS * WIDTH//4

CIRCLE_DRAW = False
CIRCLE_RADIUS = 1

# Create border
border_thickness = 5
border_right = (0, 0, border_thickness, size[1])
border_left = (size[0] - border_thickness, 0, border_thickness, size[1])
border_top = (0, 0, size[0], border_thickness)
border_down = (0, size[1] - border_thickness, size[0], border_thickness)

# Flags
done = False
pause = False
draw_path = False
draw_color = True
border = False
file_open = False
hide_controls = True

# For keeping time
# Last_saved_time and last_error_time starts at negative to prevent showing at beginning of the game
last_time = 0
last_saved_time = -1000
last_error_time = -1000
current_time = 0

# Constant
GRAV_CONST = 6.67408 * (10 ** (-11))

# Gets data from file
def read_from_file(str_name):
	# Checks if the file exists
	if os.path.isfile(str_name):
		global file_open
		file_open = True
		preset_file = open(str_name, "r")
		stored_data = preset_file.readlines()

		# Remove square brackets from list
		stored_data[2] =stored_data[2].replace("[", "").replace("]", "")
		stored_data[3] =stored_data[3].replace("[", "").replace("]", "")

		# Sets starting positions based on data
		global start_mass
		global numer_of_objects
		start_mass = int(stored_data[0])
		number_of_objects = int(stored_data[1])

		global file_position_x
		global file_position_y
		file_position_x = [int(x) for x in stored_data[2].split(', ')]
		file_position_y = [int(x) for x in stored_data[3].split(', ')]

		preset_file.close()
		return True
	return False

# Checks for file to open
if len(sys.argv) > 1:
	file_to_open = sys.argv[1]
	read_from_file(file_to_open)

# class object
class Object:
	def __init__ (self, mass, position_x, position_y, color):
		# Initialize mass and position
		self.mass = mass
		self.merged = False
		self.selected = False
		self.store_force_x = 0
		self.store_force_y = 0

		self.moved_path = 0

		self.color = color

		self.i_position_x = position_x
		self.i_position_y = position_y

		self.position_x = position_x
		self.position_y = position_y

		self.acceleration_x = 0
		self.acceleration_y = 0

		self.velocity_x = 0
		self.velocity_y = 0

		self.time = 0
		self.closeness = 0

		self.max_velocity = 0

	def calculate_radius(self):
		# Radius is dependent on mass
		# Assumes one unit of mass (1 * 10^11 kg) is equal to one m^2
		self.radius = math.sqrt((self.mass / 10 ** 11) / math.pi)

	def calculate_new_position(self):
		# Velocity is change in position
		self.position_x += self.velocity_x
		self.position_y += self.velocity_y

		self.moved_path += (self.velocity_x**2+self.velocity_y**2)**0.5

		self.time += 1
		target_x = WIDTH/2
		target_y = HEIGHT/2
		#TODO total force experienced? velocity delta?
		self.closeness += (((self.position_x - target_x)**2 + (self.position_y - target_y)**2)**0.5)**0.5

		velocity = (self.velocity_x**2 + self.velocity_y**2)**0.5
		if velocity > self.max_velocity:
			self.max_velocity = velocity

		if border:
			# Check each border for collision
			if self.position_x + self.radius > size[0]:
				# First move the object (to prevent repeated collision)
				self.position_x = size[0] - self.radius
				# Velocity is reversed
				self.velocity_x *= -1
			if self.position_x - self.radius < 0:
				self.position_x = self.radius
				self.velocity_x *= -1
			if self.position_y + self.radius > size[1]:
				self.position_y = size[1] - self.radius
				self.velocity_y *= -1
			if self.position_y - self.radius < 0:
				self.position_y = self.radius
				self.velocity_y *= -1

	def calculate_new_velocity(self, obj):
		# Find angle and force in x and y
		angle = self.calculate_angle(obj)
		force = self.calculate_force(obj)
		force_x = force * math.cos(angle)
		force_y = force * math.sin(angle)

		# Adds the force to the stored force
		self.store_force_x += force_x
		self.store_force_y += force_y

		# Newton's second law
		self.acceleration_x = force_x / self.mass
		self.acceleration_y = force_y / self.mass

		# Acceleration is change in velocity
		self.velocity_x += self.acceleration_x
		self.velocity_y += self.acceleration_y

	def calculate_angle(self, obj):
		# Use trig to get angle between two objects
		diff_x = obj.position_x - self.position_x
		diff_y = obj.position_y - self.position_y

		if diff_x != 0:
			angle = math.atan(diff_y / diff_x)
		else:
			angle = 0

		if diff_x < 0:
			angle += math.pi
		return angle

	def calculate_force(self, obj):
		# Equation for gravity (using big G)
		distance = math.sqrt((self.position_x - obj.position_x)**2 + (self.position_y - obj.position_y)**2)
		if distance == 0:
			return 0
		return GRAV_CONST * (self.mass * obj.mass)/ (distance**2)

	def collision(self, obj):
		# Gets distance beteween two objects
		difference_x = self.position_x - obj.position_x
		difference_y = self.position_y - obj.position_y
		position = math.sqrt(difference_x ** 2 + difference_y ** 2)

		# If the distance between the two is less than the two object's radii, they collided
		if position <= (self.radius + obj.radius):
			momentum_x = self.mass * self.velocity_x + obj.mass * obj.velocity_x
			momentum_y = self.mass * self.velocity_y + obj.mass * obj.velocity_y

			# Merges to the larger mass
			if self.mass > obj.mass:
				# Using conservation of momentum and assumes perfectly inelastic collision
				self.mass += obj.mass
				self.velocity_x = momentum_x / self.mass
				self.velocity_y = momentum_y / self.mass

				# Merged objects disappear
				obj.merged = True

				# Recalculates radius based on new mass
				self.calculate_radius()
			else:
				obj.mass += self.mass
				obj.velocity_x = momentum_x / obj.mass
				obj.velocity_y = momentum_y / obj.mass
				self.merged = True
				obj.calculate_radius()

	def getMeasure(self):

		#if self.time == 0 or self.merged:
		#	return -1
		#return log(self.closeness/self.time)

		#d = ((self.position_x-WIDTH//2)**2 + (self.position_y-HEIGHT//2)**2)**0.5
		#return log(d)
		if self.moved_path <= 0:
			return 0
		return log(self.moved_path)

	def getMeasure2(self):
		if self.max_velocity <= 1:
			return 0
		return log(self.max_velocity)

	def draw_initial(self):
		def clamp(f):
			return min(255,max(0,int(f)))

		measure = self.getMeasure()
		#TODO 255-
		mval = clamp(measure/largest_value*255)
		alpha = mval

		measure2 = self.getMeasure2()
		mval2 = clamp(measure2/largest_value2*255)
		blue = mval2
		if self.merged:
			red = 255
			green = 0
		else:
			red = 0#255
			green = 255#255

		if CIRCLE_DRAW:
			surface = pygame.Surface((100,100))
			surface.set_colorkey((0,0,0))
			#print(self.i_position_x, alpha)
			surface.set_alpha(alpha)

			pygame.draw.circle(surface, [red,green,blue,255], (50,50), CIRCLE_RADIUS)
			screen.blit(surface, [int(self.i_position_x)-50-CIRCLE_RADIUS/2, int(self.i_position_y)-50-CIRCLE_RADIUS/2])
		else:
			pygame.gfxdraw.pixel(screen, int(self.i_position_x), int(self.i_position_y), [red,green,blue,alpha])
		#pygame.draw.circle(screen, [255,255,255,255], [int(self.i_position_x), int(self.i_position_y)], 4)

	def draw_object(self):

		self.draw_initial()

		if not self.merged:
			# If an object is selected, draw an outline around them

			if self.selected:
				pygame.draw.circle(screen, DARK_RED, [int(self.position_x), int(self.position_y)], int(self.radius) + 4)

			# Draw objects. If/else for diff color modes
			if draw_color:
				pygame.draw.circle(screen, self.color, [int(self.position_x), int(self.position_y)], int(self.radius))
			else:
				pygame.draw.circle(screen, WHITE, [int(self.position_x), int(self.position_y)], int(self.radius))

def open_preset(number):
	global last_time
	global last_error_time
	global current_time
	# There's probably a better way to do this :/
	if number == 0:
		condition = pressed[pygame.K_KP0] or pressed[pygame.K_0]
	if number == 1:
		condition = pressed[pygame.K_KP1] or pressed[pygame.K_1]
	if number == 2:
		condition = pressed[pygame.K_KP2] or pressed[pygame.K_2]
	if number == 3:
		condition = pressed[pygame.K_KP3] or pressed[pygame.K_3]
	if number == 4:
		condition = pressed[pygame.K_KP4] or pressed[pygame.K_4]
	if number == 5:
		condition = pressed[pygame.K_KP5] or pressed[pygame.K_5]
	if number == 6:
		condition = pressed[pygame.K_KP6] or pressed[pygame.K_6]
	if number == 7:
		condition = pressed[pygame.K_KP7] or pressed[pygame.K_7]
	if number == 8:
		condition = pressed[pygame.K_KP8] or pressed[pygame.K_8]
	if number == 9:
		condition = pressed[pygame.K_KP9] or pressed[pygame.K_9]

	# If condition is met, load the corresponding file
	if current_time > delay + last_time and condition:
		last_time = current_time
		if read_from_file("preset" + str(number) + ".txt"):
			init_objects()
		else:
			last_error_time = current_time

from prng import perm

p = perm(WIDTH*HEIGHT)

stopped_indexes = {}
all_indexes = {}
#TODO continue simulation!

ITER = 0
def init_objects():
	global file_position_x
	global file_position_y
	global file_open
	global objects

	global ITER
	global game_speed
	global screenshot

	# Resets screen regardless of flag draw_path
	screen.fill(BLACK)
	del objects[:]
	#objects = []
	if not file_open:
		file_position_x[:] = []
		file_position_y[:] = []

	objects.append(Object(1 * start_mass* (10**11), WIDTH/2 + 25, HEIGHT/2 + 25, [255,0,0]))
	objects[-1].velocity_x = 2
	objects[-1].calculate_radius()

	objects.append(Object(1 * start_mass* (10**11), WIDTH/2 - 25, HEIGHT/2 - 25, [255,0,0]))
	objects[-1].velocity_x = -2
	objects[-1].calculate_radius()

	for i in range(number_of_objects):
		# Mass must be in 10^11kg scale (because gravity would be too weak otherwise)
		mass = start_mass * (10 ** 11)
		if file_open:
			position_x = file_position_x[i]
			position_y = file_position_y[i]
		else:
			if SIM:
				index = 0
				game_speed = 1
				position_x = SIM_X if SIM_FIXED else random.randint(0, WIDTH-1)
				position_y = SIM_Y if SIM_FIXED else random.randint(0, HEIGHT-1)
			else:
				if SIM_SEQUENTIAL:
					position_x = ITER%WIDTH
					position_y = ITER//WIDTH

				else:
				# Randomized position
					try:
						while True:
							index = next(p)
							position_x = index%WIDTH
							position_y = index//WIDTH

							if index not in stopped_indexes:
								break
							else:
								mobj = stopped_indexes[index]#Object(mass, position_x, position_y, (255,255,255))
								old_objects.append(mobj)
					except StopIteration:
						screenshot = True
						index = 0
						position_x = 0
						position_y = 0
				#random.randint(0, size[0])
				#random.randint(0, size[1])
			# Stores position in var for saving
			file_position_x.append(position_x)
			file_position_y.append(position_y)
		# Randomized color

		if index in all_indexes:
			objects.append(all_indexes[index])
		else:
			color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
			# Add the object and calculate radius
			objects.append(Object(mass, position_x, position_y, color))
			objects[-1].calculate_radius()


	# File open only works on first run
	file_open = False

	ITER += 1

# Starts offself.closeness/self.time
init_objects()

old_objects = []
largest_value = 1.1
largest_value2 = 0
screenshot = False

def next_iter():
	global largest_value, largest_value2
	last = objects[-1]
	old_objects.append(last)
	measure = last.getMeasure()
	if measure > largest_value:
		largest_value = measure
		print(largest_value, last.i_position_x, last.i_position_y)
	measure2 = last.getMeasure2()
	if measure2 > largest_value2:
		largest_value2 = measure2
	init_objects()

# Main loop
while not done:
	# Update time
	current_time += 1
	delay = 20

	# Exiting game
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True


	# Key press
	pressed = pygame.key.get_pressed()
	if pressed[pygame.K_SPACE] and current_time > delay + last_time:
		# Delete objects and reinitialize for new set of objects
		last_time = current_time
		next_iter()

	# Path
	elif pressed[pygame.K_z] and current_time > delay + last_time:
		last_time = current_time
		draw_path = not draw_path

	# Border
	elif pressed[pygame.K_x] and current_time > delay + last_time:
		last_time = current_time
		border = not border
		# Border needs to disappear
		screen.fill(BLACK)

	# Color
	elif pressed[pygame.K_c] and current_time > delay + last_time:
		last_time = current_time
		draw_color = not draw_color

	# Game speed +
	elif pressed[pygame.K_q]:
		game_speed += 1

	# Game speed -
	elif pressed[pygame.K_a]:
		if game_speed > 1:
			game_speed -= 1

	# Mass +
	elif pressed[pygame.K_w]:
		start_mass += 1

	# Mass -
	elif pressed[pygame.K_s]:
		if start_mass > 1:
			start_mass -= 1

	# Num +
	elif pressed[pygame.K_e]:
		number_of_objects += 1

	# Num -
	elif pressed[pygame.K_d]:
		if number_of_objects > 1:
			number_of_objects -= 1

	# Pause
	elif pressed[pygame.K_p] and current_time > delay + last_time:
		last_time = current_time
		pause = not pause

	# Save
	elif pressed[pygame.K_o] and current_time > delay + last_time:
		last_time = current_time
		last_saved_time = current_time
		current_files = os.listdir("./")
		# Look through each preset for a number preset that doesn't exist yet
		# There must be one usable file name in current_files + 1
		num_for_file = -1
		for j in range(len(current_files) + 1):
			str_to_check = "preset" + str(j) + ".txt"
			current_use = True
			# Only use file name if it isn't the same as the other file names in the directory
			for i in range(len(current_files)):
				if current_files[i] == str_to_check:
					current_use = False
					break
			# Exit if match was found
			if current_use:
				num_for_file = j
				break
		# Save current in file
		save_file = open("preset" + str(num_for_file) + ".txt", "w")
		save_file.write(str(start_mass) + '\n')
		save_file.write(str(number_of_objects) + '\n')
		save_file.write(str(file_position_x) + '\n')
		save_file.write(str(file_position_y))
		save_file.close()

	# Wtf
	elif pressed[pygame.K_m] and current_time > delay + last_time:
		last_time = current_time
		GRAV_CONST *= -1

	# Hide UI
	elif pressed[pygame.K_i] and current_time > delay + last_time:
		last_time = current_time
		hide_controls = not hide_controls
		if hide_controls:
			screen.fill(BLACK)

	# Checks for number press between 0 to 9 -> opens the corresponding file
	for i in range(10):
		open_preset(i)

	# Check if player clicked on an object
	if pygame.mouse.get_pressed()[0]:
		# To check whether to deselect item
		for i in objects:
			# Deselect all other objects
			i.selected = False
			# Find distance between mouse and object
			mouse_pos = pygame.mouse.get_pos()
			distance = math.sqrt((mouse_pos[0] - i.position_x)**2 + (mouse_pos[1] - i.position_y)**2)
			# If the distance is smaller than the radius, the mouse is in the object and is selected
			if i.radius > distance:
				# Current object is selected
				i.selected = True
				break

	# If paused, don't need to run code
	if not pause:
		# Run multiple times for larger game_speed
		for num in range(game_speed):
			# Checks for collision and deletes y if applicable

			for x in objects:
				for y in objects:
					if x != y and not x.merged and not y.merged:
						x.collision(y)

			# Zeroes out acceleration and old gravitational force
			for x in objects:
				x.acceleration_x = 0
				x.acceleration_y = 0
				x.store_force_x = 0
				x.store_force_y = 0

			# Calculates new velocity based on force of gravity
			for x in objects:
				for y in objects:
					if x != y and not x.merged and not y.merged:
						x.calculate_new_velocity(y)

			# Calculates position based on velocity
			for x in objects:
				x.calculate_new_position()

			index = objects[-1].i_position_x+objects[-1].i_position_y*WIDTH
			if objects[-1].merged:
				#TODO store velocity!, just mark it as green or something
				stopped_indexes[index] = objects[-1]

			#XXX .merged might screw up other measurements
			if objects[-1].merged or objects[-1].time > SIM_STEPS:
				all_indexes[index] = objects[-1]
				next_iter()



		# Fill screen
		if not draw_path:
			screen.fill(BLACK)

		for o in old_objects:
			o.draw_initial()

		if screenshot:
			pygame.image.save(screen, f"screen-{SIM_STEPS}.png")
			print("STOPPED:", len(stopped_indexes), len(stopped_indexes)/(WIDTH*HEIGHT)*100, "%%")
			SIM_STEPS += SIM_STEP_INC
			old_objects = []
			objects = []
			screenshot = False
			p = perm(WIDTH*HEIGHT)
			init_objects()

		# Draw
		for i in objects:
			i.draw_object()


	if not hide_controls:
		# Rectangle for top bar
		pygame.draw.rect(screen, LIGHT_GRAY, (0, 0, size[0], 40))

		# Draw boxes to clear the text
		pygame.draw.rect(screen, DARK_GRAY, (0, 90, 80, 30))
		pygame.draw.rect(screen, DARK_GRAY, (size[0] - 140, 40, 140, 40))

		# If an object is selected, display its information
		for i in objects:
			if i.selected and not i.merged:
				object_information_x = "X  Position: " + str(round(i.position_x, 2))
				object_information_y = "Y  Position: " + str(size[1] - round(i.position_y, 2))
				object_information_vel_x = "X  Velocity: "  + str(round(i.velocity_x, 3)) + "m/s"
				object_information_vel_y = "Y  Velocity: "  + str(round(-i.velocity_y, 3)) + "m/s"
				object_information_acc_x = "X  Acceleration: " + str(round(i.acceleration_x, 5)) + "m/s^2"
				object_information_acc_y = "Y  Acceleration: " + str(round(-i.acceleration_y, 5)) + "m/s^2"
				object_information_force_x = "X  Force: " + str('%.3e' % i.store_force_x) + "N"
				object_information_force_y = "Y  Force: " + str('%.3e' % -i.store_force_y) + "N"
				# Display the text
				text_display_x = text_font_small.render(object_information_x, False, WHITE)
				text_display_y = text_font_small.render(object_information_y, False, WHITE)
				text_display_vel_x = text_font_small.render(object_information_vel_x, False, WHITE)
				text_display_vel_y = text_font_small.render(object_information_vel_y, False, WHITE)
				text_display_acc_x = text_font_small.render(object_information_acc_x, False, WHITE)
				text_display_acc_y = text_font_small.render(object_information_acc_y, False, WHITE)
				text_display_force_x = text_font_small.render(object_information_force_x, False, WHITE)
				text_display_force_y = text_font_small.render(object_information_force_y, False, WHITE)
				screen.blit(text_display_x, (600, 4))
				screen.blit(text_display_y, (600, 25))
				screen.blit(text_display_vel_x, (760, 4))
				screen.blit(text_display_vel_y, (760, 25))
				screen.blit(text_display_acc_x, (900, 4))
				screen.blit(text_display_acc_y, (900, 25))
				screen.blit(text_display_force_x, (1100, 4))
				screen.blit(text_display_force_y, (1100, 25))

		# Game speed change
		text_speed = text_font.render("Speed: " + str(game_speed) + "x", False, WHITE)
		screen.blit(text_speed, (10, 14))
		screen.blit(text_s, (10, 40))
		screen.blit(text_a, (10, 55))
		screen.blit(text_p, (10, 70))

		# Mass Change
		text_mass = text_font.render("Init Mass: " + str(start_mass) + "*10^11 kg", False, WHITE)
		screen.blit(text_mass, (190, 14))
		screen.blit(text_d, (190, 40))
		screen.blit(text_f, (190, 55))

		# Number change
		text_number = text_font.render("Init Number: " + str(number_of_objects), False, WHITE)
		screen.blit(text_number, (400, 14))
		screen.blit(text_g, (400, 40))
		screen.blit(text_h, (400, 55))

		# Instructions
		screen.blit(text_space, (10, size[1] - 100))
		screen.blit(text_z, (10, size[1] - 75))
		screen.blit(text_x, (10, size[1] - 50))
		screen.blit(text_c, (10, size[1] - 25))
		screen.blit(text_o, (size[0] - 80, 40))
		screen.blit(text_i, (600, size[1] - 25))

		# Displays when paused
		if pause:
			screen.blit(text_pause, (10, 90))

		# Displays saved when a game is saved
		if last_saved_time + 60 > current_time:
			screen.blit(text_saved, (size[0] - 80, 55))

		# Displays when loading game causes error
		if last_error_time + 60 > current_time:
			screen.blit(text_error, (size[0] - 130, 55))

		# Wtf 2
		if GRAV_CONST > 0:
			text_m = text_font_small.render("M for antigravity (FOR FUN)", False, GRAY)
		else:
			text_m = text_font_small.render("M for antigravity (FOR FUN)", False, DARK_RED)

		screen.blit(text_m, (size[0] - 160, size[1] - 20))

	# Border drawing
	if border:
		pygame.draw.rect(screen, DARK_RED, border_right)
		pygame.draw.rect(screen, DARK_RED, border_left)
		pygame.draw.rect(screen, DARK_RED, border_top)
		pygame.draw.rect(screen, DARK_RED, border_down)

	# Updates
	pygame.display.flip()

	# 60 FPS
	clock.tick(30)


pygame.quit()

#for o in old_objects:
