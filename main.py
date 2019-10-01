"""
Intelligence Artifielle pour Flappy Bird.
"""

import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500 #Largeur de la fenêtre
WIN_HEIGHT = 800 #Longueur de la fenêtre
GEN = 0 #Numéro de la génération actuelle. (Utilisé pour l'affichage).


BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),  #Images pour l'oiseau. 3 images, 3 états de "battage d'ailes"
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "BottomPipe.png"))) #Image du tuyau
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png"))) #Image du sol qui défile
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png"))) #Image de fond

STAT_FONT = pygame.font.SysFont("comicsans", 50) #Setup de la police d'écriture pour l'affichage

class Bird:
    """
    Classe de l'oiseau.
    """
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Méthode d'initialisation de l'objet.
        param x: Coordonnée x de départ de l'oiseau. (Int)
        param y: Coordonnée y de départ de l'oiseau. (Int)
        return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Méthode utilisée pour faire sauter l'oiseau.
        return : None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        Méthode utilisée pour faire bouger l'oiseau.
        return : None
        """
        self.tick_count += 1

        #Gère l'accélération vers le bas.
        d = self.vel*self.tick_count + 1.5*self.tick_count**2 #How much does the bird move

        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50: #Oriente l'oiseau vers le haut
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else: #Oriente l'oiseau vers le bas
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Méthode utilisée pour dessiner l'oiseau.
        param win: pygame.window / pygame.Surface
        return : None
        """
        self.img_count += 1

        #L'animation de l'oiseau (Cycle des images)
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME *2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME *3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME *4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME *4 +1:
            self.img = self.IMGS[0]
            self.img_count = 0

        #Quand l'oiseau pique vers le bas, ses ailes ne battent pas.
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect =  rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        """
        Masque de l'image actuelle de l'oiseau.
        Utilisé pour gérer les collisions.
        return : None
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    Objet gérant les Tuyaux.
    """
    GAP = 200
    VEL = 5

    def __init__(self, x):
        """
        initialisation de l'objet.
        param x: int.
        return : None
        """
        self.x = x
        self.height = 0

        #Setup du haut et du bas du tuyau.
        self.top = 0
        self.bottom = 0

        #initialisation des deux images.
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) #On retourne l'image pour que le tuyau soit à l'envers en haut.
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        """
        Génération d'un nombre qui sera la hauteur du tuyau, et setup de cette hauteur.
        return : None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Fais bouger les tuyaux.
        Vitesse = VEL
        return : None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        Dessine le haut et le bas du tuyau.
        param win: pygame.window / pygame.Surface
        return : None
        """
        win.blit(self.PIPE_TOP, (self.x, self.top)) #Dessine le haut
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom)) #Dessine le bas

    def collide(self, bird):
        """
        Gère les collisions.
        Renvoie 'True' si un point du masque de l'oiseau touche un tuyau.
        Sinon, renvoie 'False'
        return : Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True
        return False


class Base:
    """
    Classe du sol mouvant.
    """
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        """
        initialisation de l'objet.
        param y: Int
        return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Mouvement continu du sol pour qu'il semble être infini.
        return : None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Dessine le sol : Deux images qui bougent, et qui s'alterne.
        Quand l'une sort de l'écran, elle se met derrière l'autre et prend sa place, etc.
        param win: pygame.Surface / pygame.window
        return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score, gen):
    """
    Création de la fenêtre de jeu, et ajout des objets.
    param win: pygame.window / pygame.Surface
    param birds: Liste des objets Bird.
    param pipes: Liste des tuyaux.
    param base: Objet 'Base'
    param score: Score actuel.
    param gen: Génération actuelle.
    """
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score :" + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH-10-text.get_width(), 10))

    text = STAT_FONT.render("Gen :" + str(gen), 1, (255,255,255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds: #Dessine les oiseaux.
        bird.draw(win)
    pygame.display.update()

def main(genomes, config):
    """
    Lance la simulation de la population actuelle,
    et attribue les points Fitness en fonction de
    la distance parcourue.
    """
    global GEN
    GEN += 1

    #Création de listes, contenant le génome, le neural network et l'oiseau les utilisants.
    #Ces trois objets auront le même index.
    nets = [] #Neural Networks
    ge = [] #Génomes
    birds = [] #Oiseaux

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config) #Création des NN
        nets.append(net) #On ajoue le NN à la liste.
        birds.append(Bird(230, 350)) #On ajoute l'oiseau à la liste
        g.fitness = 0 #On commence avec un fitness de 0.
        ge.append(g) #On ajoute le génome à la liste


    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -=1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

            if add_pipe:
                score += 1
                for g in ge:
                    g.fitness += 5
                pipes.append(Pipe(600))
                break

            for r in rem:
                pipes.remove(r)

            for x, bird in enumerate(birds):
                if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)

def run(config_path):
    """
    Lance l'algorithme NEAT pour entraîner les Neural Networks.
    param config_path: Chemin d'accès au fichier de configuration de NEAT.
    return : None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_path)

    p = neat.Population(config) #Création de la population

    p.add_reporter(neat.StdOutReporter(True)) #Reporter qui montre la progression dans le terminal.
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main,50) #Run 50 générations maximum.

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
