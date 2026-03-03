

import os
from os.path import join
import pygame 
import math
import random

pygame.init()


#display setup
width = 800
height = 600
display = pygame.display.set_mode((width, height))
pygame.display.set_caption("Rain Drop")

#colors
white = (255, 255, 255)
black = (0, 0, 0)
blue = (0, 0, 255)
ocean_blue = (0, 105, 148)
persian_blue = (28, 57, 187)

#game specific variables
ball_x = 400
ball_y = 100
ball_radius = 200  #size of the rain drop
ball_speed_x = 0
ball_speed_y = 0


max_clouds = 7

#CLOCK 
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 55)

#Sprite class for the rain drop
class rain_drop(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(join("rain_drop.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (ball_radius, ball_radius - 50))
        self.rect = self.image.get_rect(center = (ball_x, ball_y))   
        self.hitbox = self.rect.inflate(-150, -190)  # shrink hitbox
        self.hitbox.center = self.rect.center  # align hitbox with rect
#Sprite class for clouds
class Cloud:
    def __init__(self):
        self.image = pygame.image.load(join("cloud.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (500, 250))
        lanes = [150, 400, 650]
        x = random.choice(lanes)
        y = height + 50
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.hitbox = self.rect.inflate(-250, -190)  # shrink hitbox
        self.cloudspeed = random.randint(4, 7)
        self.passed = False  # flag to check if cloud has been passed by the rain drop

    def update(self):
        self.rect.y -= self.cloudspeed
        self.hitbox.center = self.rect.center
        
#sprite for power up 
class PowerUp:
    def __init__(self):
        self.image = pygame.image.load(join("rain_drop.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (60, 50))
        x = random.randint(50, width - 50)
        y = random.randint(20, height - 50)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.inflate(-10, -10)  # shrink hitbox
        self.duration = 300  # duration of power-up effect in frames
    def update(self):
        self.hitbox.center = self.rect.center  # align hitbox with rect
        self.rect.y += 2  # power-up slowly falls down

#text display function
def text_screen(text, color, x, y, font_size=65):
    screen_text = pygame.font.SysFont(None, font_size).render(text, True, color)
    display.blit(screen_text, [x,y])

             
def game_loop():
        
        #game specific variables
        exit_game = False
        game_over = False
        fps = 60
        clouds = []
        power_ups = []
        cloudspeed = 5
        player = rain_drop()
        score = 0
        cloudspeed += 0.001  # gradual speed increase
        init_vel= 5
        #check if high score file exists
        if not os.path.exists("high_score.txt"):
                with open("high_score.txt", "w") as f:
                    f.write("0")
        with open("high_score.txt", "r") as f:
                high_score = int(f.read())
   
                    
        #GAME LOOP
        while not exit_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game = True
            display.fill(ocean_blue)
            
            if random.randint(1, 300) == 1 and len(power_ups) < 3:  #spawn power up with low probability and limit number of power ups on screen
                power_ups.append(PowerUp())
                too_near = False
                for power_up in power_ups:
                    if abs(power_up.rect.centerx - player.rect.centerx) < 200:
                        too_near = True
                        break
                if too_near:
                    power_ups.pop()  # remove the power-up if it's too close to the player
                if not too_near:
                    power_ups.append(PowerUp())
            for power_up in power_ups:
                power_up.update()
                display.blit(power_up.image, power_up.rect)
                if power_up.hitbox.colliderect(player.hitbox):
                    init_vel += 2  # increase speed when power-up is collected
                    power_ups.remove(power_up)  # remove power-up after collection
                    
            if random.randint(1, 60) == 1 and len(clouds) < max_clouds:
                new_cloud = Cloud()

                too_close = False
                for cloud in clouds:
                    if abs(new_cloud.rect.centerx - cloud.rect.centerx) < 350:
                        too_close = True
                        break

                if not too_close:
                    clouds.append(new_cloud)
            for cloud in clouds:
                if not cloud.passed and cloud.rect.bottom < player.rect.top:
                    score += 1
                     
                    #add sound effect when player passes a cloud
                    cloud.passed = True
                    pygame.mixer.music.load("score.mp3")
                    pygame.mixer.music.play()
                cloud.update()
                display.blit(cloud.image, cloud.rect)
            
            clouds = [cloud for cloud in clouds 
                if cloud.rect.bottom > 0 and cloud.rect.top < height]
            
            #input 
            key = pygame.key.get_pressed()

            player.rect.x += int(key[pygame.K_RIGHT] - key[pygame.K_LEFT]) * init_vel
            player.rect.x = max(25, min(player.rect.x, width - 150))  # keep player within bounds
            player.rect.y += int(key[pygame.K_DOWN] - key[pygame.K_UP]) * init_vel
            player.rect.y = max(150, min(player.rect.y, height - 150))  # keep player within bounds
            player.hitbox.center = player.rect.center  # update hitbox position
            
            #checking for collision of rain drop with clouds
            if any(cloud.hitbox.colliderect(player.hitbox) for cloud in clouds):
                game_over = True
            #pygame.draw.rect(display, (255,0,0), player.hitbox, 2)


            #for cloud in clouds:
            #    pygame.draw.rect(display, (0,255,0), cloud.hitbox, 2)
                

            display.blit(player.image, player.rect)
            #when score == high score, play sound effect
            if score > int(high_score):
                high_score = score
                with open("high_score.txt", "w") as f:
                    f.write(str(high_score))
                    pygame.mixer.music.load("high_score.mp3")
                    pygame.mixer.music.play()
            
            if game_over:
                text_screen("Rain Drop couldn't", black, 300, 200)
                text_screen(" reach the sea :(", black, 300, 250)
                text_screen(f"Your Score: {score} , high score: {high_score}", black, 0,0, 40) #top left corner of the screen
                text_screen("Press Enter To Continue", white, 250, 350 , 40)
                game_overbgm = pygame.mixer.music.load("game_over.mp3")
                pygame.mixer.music.play()
                pygame.display.update()
                
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            quit()
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_RETURN:
                                waiting = False
                                return  # exit game loop and return to welcome screen
            text_screen("Score: " + str(score), white, 10, 10)
            clock.tick(fps)  
            pygame.display.update()
            
def welcome_screen():
    waiting = True

    while waiting:
        display.fill(ocean_blue)
        text_screen("Welcome to Rain Drop!", white, 200, 250)
        text_screen("Press Enter To Start", white, 200, 300)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

        pygame.display.update()
        clock.tick(60)

    
running = True

while running:
    welcome_screen()
    game_loop()

pygame.quit()

        
        
        
