import os
import neat
import pickle
import pygame
import pygame.gfxdraw
from sys import exit
from random import randint, choice

class Ball():
	def __init__(self,width,height,screen):
		self.screen = screen
		self.screen_width = width
		self.screen_height = height
		self.radius = 8
		self.rect = pygame.Rect(width/2 - self.radius,height/2 - self.radius,2*self.radius,2*self.radius)
		self.x_vel = choice([-5,5])
		self.y_vel = choice([-6,-5-4,-3,-2,-1,1,2,3,4,5,6])

	def move(self,left_paddle,right_paddle):
		if (self.rect.top < 0) or (self.rect.bottom > self.screen_height):
			self.y_vel *= -1

		self.rect.x += self.x_vel
		self.rect.y += self.y_vel
		hit = None 

		if (self.rect.colliderect(left_paddle.rect)and self.rect.left>=0):
			hit = 1
			self.x_vel *= -1
			self.y_vel += left_paddle.vel
			self.rect.x += self.x_vel
		if (self.rect.colliderect(right_paddle.rect)and self.rect.right<=self.screen_width):
			hit = 2
			self.x_vel *= -1
			self.y_vel += right_paddle.vel
			self.rect.x += self.x_vel
		return hit

	def update(self,left_paddle,right_paddle):
		hit = self.move(left_paddle,right_paddle)
		score = None
		reset = False
		if self.rect.right <= 0:
			score = 2
			reset = True
		if self.rect.left >= self.screen_width:
			score = 1
			reset = True

		# Antialiased Circle Drawing
		pygame.gfxdraw.aacircle(self.screen,self.rect.center[0],self.rect.center[1],self.radius,(255,255,255))
		pygame.draw.ellipse(self.screen, 'white', self.rect)

		return score, hit, reset

	def reset(self):
		self.rect.center = (self.screen_width/2, self.screen_height/2)
		self.x_vel = choice([-5,5])
		self.y_vel = choice([-6,-5-4,-3,-2,-1,1,2,3,4,5,6])

class Paddle():
	def __init__(self, side, width, height, screen):
		self.screen = screen
		self.screen_width = width
		self.screen_height = height
		self.length = 60
		self.width = 5
		self.pad = 5
		self.vel = 0
		self.side = side
		if self.side:
			self.rect = pygame.Rect(width - self.width - self.pad,height/2 - self.length/2, self.width, self.length)
		else:
			self.rect = pygame.Rect(self.pad,height/2 - self.length/2, self.width, self.length)

	def move(self):
		self.rect.top += self.vel
		if self.rect.top <= 5: self.rect.top = 5
		if self.rect.bottom >= self.screen_height - 5: self.rect.bottom = self.screen_height - 5

	def update(self):
		self.move()
		pygame.gfxdraw.rectangle(self.screen,self.rect,(255,255,255))
		pygame.draw.rect(self.screen,(255,255,255),self.rect)

	def reset(self):
		if self.side:
			self.rect.x = self.screen_width - self.width - self.pad
			self.rect.y = self.screen_height/2 - self.length/2
		else:
			self.rect.x = self.pad
			self.rect.y = self.screen_height/2 - self.length/2

class Fps():
	def __init__(self):
		self.counter = 0
		self.start_time = 0
		self.time_passed = 0
		self.update_freq = 500
		self.fps = 0

	def get_start_time(self):
		if self.counter == 0:
			self.start_time = pygame.time.get_ticks()

	def update(self):
		self.counter += 1
		self.time_passed = (pygame.time.get_ticks() - self.start_time)
		# print(f'Counter: {self.counter}, time passed: {self.time_passed}, FPS: {self.fps}')
		if self.time_passed >= self.update_freq:
			avg_time = self.time_passed/self.counter
			self.fps = int(1000/avg_time)
			# print(f'FPS: {self.fps}')
			self.counter = 0
   

class Pong_Game():
	def __init__(self):
		pygame.display.set_caption('Pong Game')
		self.width = 640
		self.height = 360
		self.fps_bound = 60
		self.no_of_hits = [0,0]
		self.score = [0,0]
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		self.display_font = pygame.font.SysFont('cambria', 25)
		self.ball = Ball(self.width,self.height,self.screen)
		self.left_paddle = Paddle(0,self.width,self.height,self.screen)
		self.right_paddle = Paddle(1,self.width,self.height,self.screen)
		self.fps = Fps()

	def game_loop(self):
		# Single Frame, it returns the necessary inputs
		# Events
		self.check_for_events()

		self.screen.fill('#262626')
		pygame.draw.aaline(self.screen,(255,255,255),(self.width/2,-5),(self.width/2,self.height+5))

		# Display fps
		self.display_fps()

		# Display Score
		self.display_score_or_hit('score')

		# Update Paddles And Ball
		self.left_paddle.update()
		self.right_paddle.update()
		score, hit, reset = self.ball.update(self.left_paddle,self.right_paddle)
		if score: self.score[score-1] += 1
		if hit: self.no_of_hits[hit-1] += 1

		if reset:
			self.reset()

	def test_ai(self, genome, config):
		net = neat.nn.FeedForwardNetwork.create(genome, config)

		run = True
		while run:
			self.fps.get_start_time()

			output = net.activate((self.right_paddle.rect.y, self.ball.rect.y, abs(self.right_paddle.rect.x - self.ball.rect.x), self.ball.y_vel, -self.ball.x_vel/abs(self.ball.x_vel)))
			decision = output.index(max(output))

			if decision == 0:
				self.right_paddle.vel = 0
			elif decision == 1:
				self.right_paddle.vel = -5
			else:
				self.right_paddle.vel = +5

			self.game_loop()

			# Display Update
			pygame.display.update()
			self.clock.tick(self.fps_bound)

			self.fps.update()

	def ai_vs_ai(self, genome, config):
		net_1 = neat.nn.FeedForwardNetwork.create(genome, config)
		net_2 = neat.nn.FeedForwardNetwork.create(genome, config)

		run = True
		while run:
			self.fps.get_start_time()

			output_1 = net_1.activate((self.left_paddle.rect.y, self.ball.rect.y, abs(self.left_paddle.rect.x - self.ball.rect.x), self.ball.y_vel, -self.ball.x_vel/abs(self.ball.x_vel)))
			decision_1 = output_1.index(max(output_1))
			# print(output_1)

			if decision_1 == 0:
				self.left_paddle.vel = 0
			elif decision_1 == 1:
				self.left_paddle.vel = -5
			else:
				self.left_paddle.vel = +5

			output_2 = net_2.activate((self.right_paddle.rect.y, self.ball.rect.y, abs(self.right_paddle.rect.x - self.ball.rect.x), self.ball.y_vel, -self.ball.x_vel/abs(self.ball.x_vel)))
			decision_2 = output_2.index(max(output_2))

			if decision_2 == 0:
				self.right_paddle.vel = 0
			elif decision_2 == 1:
				self.right_paddle.vel = -5
			else:
				self.right_paddle.vel = +5

			self.game_loop()

			# Display Update
			pygame.display.update()
			self.clock.tick(self.fps_bound)

			self.fps.update()

	def train_ai(self,genome_1, genome_2, config):
		net_1 = neat.nn.FeedForwardNetwork.create(genome_1, config)
		net_2 = neat.nn.FeedForwardNetwork.create(genome_2, config)

		run = True
		while run:
			self.fps.get_start_time()

			output_1 = net_1.activate((self.left_paddle.rect.y, self.ball.rect.y, abs(self.left_paddle.rect.x - self.ball.rect.x), self.ball.y_vel, -self.ball.x_vel/abs(self.ball.x_vel)))
			decision_1 = output_1.index(max(output_1))
			# print(output_1)

			if decision_1 == 0:
				genome_1.fitness += 0.01
				self.left_paddle.vel = 0
			elif decision_1 == 1:
				self.left_paddle.vel = -5
			else:
				self.left_paddle.vel = +5

			output_2 = net_2.activate((self.right_paddle.rect.y, self.ball.rect.y, abs(self.right_paddle.rect.x - self.ball.rect.x), self.ball.y_vel, -self.ball.x_vel/abs(self.ball.x_vel)))
			decision_2 = output_2.index(max(output_2))

			if decision_2 == 0:
				genome_2.fitness += 0.01
				self.right_paddle.vel = 0
			elif decision_2 == 1:
				self.right_paddle.vel = -5
			else:
				self.right_paddle.vel = +5

			# Penalising for staying away from the center
			genome_1.fitness -= (abs(self.left_paddle.rect.center[1] - self.height/2))/5000
			genome_2.fitness -= (abs(self.right_paddle.rect.center[1] - self.height/2))/5000

			self.game_loop()

			# Display Update
			pygame.display.update()
			# self.clock.tick(self.fps_bound)

			self.fps.update()

			if self.score[0] >= 1 or self.score[1] >= 1 or self.no_of_hits[0] >= 50:
				self.calculate_fitness(genome_1, genome_2)
				break

	def calculate_fitness(self, genome_1, genome_2):
		genome_1.fitness += 5*self.no_of_hits[0]
		genome_2.fitness += 5*self.no_of_hits[1]
		genome_1.fitness += 8*self.score[0]
		genome_2.fitness += 8*self.score[1]

	def check_for_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				exit()

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_w:
					self.left_paddle.vel += -5
				if event.key == pygame.K_s:
					self.left_paddle.vel += 5
				if event.key == pygame.K_UP:
					self.right_paddle.vel += -5
				if event.key == pygame.K_DOWN:
					self.right_paddle.vel += 5

			if event.type == pygame.KEYUP:
				if event.key == pygame.K_w:
					self.left_paddle.vel += 5
				if event.key == pygame.K_s:
					self.left_paddle.vel += -5
				if event.key == pygame.K_UP:
					self.right_paddle.vel += 5
				if event.key == pygame.K_DOWN:
					self.right_paddle.vel += -5

	def display_fps(self):
		fps_surf = self.display_font.render(f'FPS: {self.fps.fps}', True, (255,255,255))
		fps_rect = fps_surf.get_rect(center = (self.width/2, self.height - 30))
		pygame.draw.rect(self.screen,'#262626',fps_rect)
		self.screen.blit(fps_surf, fps_rect)

	def display_score_or_hit(self, switch = 'hit' ):
		if switch == 'hit':
			hit_surf = self.display_font.render(f'{self.no_of_hits[0]}-{self.no_of_hits[1]}', True, (255,255,255))
			hit_rect = hit_surf.get_rect(center = (self.width/2, 30))
			pygame.draw.rect(self.screen,'#262626',hit_rect)
			self.screen.blit(hit_surf, hit_rect)
		else:
			score_surf = self.display_font.render(f'{self.score[0]}-{self.score[1]}', True, (255,255,255))
			score_rect = score_surf.get_rect(center = (self.width/2, 30))
			pygame.draw.rect(self.screen,'#262626',score_rect)
			self.screen.blit(score_surf, score_rect)

	def reset(self):
		self.ball.reset()
		self.left_paddle.reset()
		self.right_paddle.reset()


def ai_vs_ai(config):
	with open("best.pickle", "rb") as f:
		winner = pickle.load(f)

		game = Pong_Game()
		game.ai_vs_ai(winner, config)

def test_ai(config):
	with open("best.pickle", "rb") as f:
		winner = pickle.load(f)

		game = Pong_Game()
		game.test_ai(winner, config)

def eval_genomes(genomes, config):
	for i, (genome_id1, genome_1) in enumerate(genomes):
		genome_1.fitness = 0
		for genome_id2, genome_2 in genomes[i:]:
			genome_2.fitness = 0 if genome_2.fitness == None else genome_2.fitness
			game = Pong_Game()
			game.train_ai(genome_1, genome_2, config)

def run_neat(config):
	p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-120')
	# p = neat.Population(config)
	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats)
	p.add_reporter(neat.Checkpointer(1))

	winner = p.run(eval_genomes, 10)
	with open("best.pickle", "wb") as f:
		pickle.dump(winner, f)


if __name__ == '__main__':
	pygame.init()
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, "config_file.txt")
	config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
	# run_neat(config)
	test_ai(config)
	# ai_vs_ai(config)