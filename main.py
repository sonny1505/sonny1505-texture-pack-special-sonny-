from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
from math import sqrt

app = Ursina()

# Flags
game_started = False
reloading = False
reload_time = 1.5
reload_timer = 0

# Containers
enemies = []
projectiles = []
pickups = []

# UI elements that will be created on game start
hp_bar = None
ammo_text = None
crosshair = None
game_over_text = None
win_text = None

# ------------------------------------------------------------
# Menu setup
# ------------------------------------------------------------

menu = Entity(parent=camera.ui)
Text('Simple FPS', parent=menu, y=0.3, scale=2)

start_btn = Button(text='Start', parent=menu, color=color.azure,
                   scale=(0.3, 0.1), y=0.1)
quit_btn = Button(text='Quit', parent=menu, color=color.red,
                  scale=(0.3, 0.1), y=-0.05)


def start_game():
    menu.disable()
    setup_game()


def quit_game():
    application.quit()

start_btn.on_click = start_game
quit_btn.on_click = quit_game


# ------------------------------------------------------------
# Game setup
# ------------------------------------------------------------

def setup_game():
    global player, weapon, ammo, hp_bar, crosshair, ammo_text
    global game_over_text, win_text

    # Terrain simple
    Entity(model='plane', scale=60, texture='white_cube',
           texture_scale=(60, 60), collider='box')
    AmbientLight()

    # Murs
    walls = [
        Entity(model='cube', scale=(60, 8, 1), position=(0, 4, 30), collider='box', color=color.gray),
        Entity(model='cube', scale=(60, 8, 1), position=(0, 4, -30), collider='box', color=color.gray),
        Entity(model='cube', scale=(1, 8, 60), position=(30, 4, 0), collider='box', color=color.gray),
        Entity(model='cube', scale=(1, 8, 60), position=(-30, 4, 0), collider='box', color=color.gray),
    ]

    # Joueur
    player = FirstPersonController(y=2, speed=5)
    player.cursor.visible = False
    mouse.locked = True
    player.health = 100

    # Arme (pistolet)
    weapon = Entity(parent=camera, model='cube', texture='brick',
                    color=color.white, scale=(0.3, 0.2, 0.6), position=(0.4, -0.25, 0.6))
    ammo = 10

    # Ennemis
    for i in range(5):
        enemy = Entity(model='sphere', color=color.red, scale=1.5,
                        position=(random.uniform(-10, 10), 1.5, random.uniform(5, 15)),
                        collider='box')
        enemy.health = 100
        enemy.speed = 2
        enemy.shoot_timer = random.uniform(1, 3)
        enemy.hp_bg = Entity(parent=enemy, model='quad', color=color.black,
                             scale=(1, 0.1), position=(0, 1.2, 0), billboard=True)
        enemy.hp = Entity(parent=enemy, model='quad', color=color.green,
                          scale=(1, 0.1), position=(0, 1.2, 0.01), billboard=True)
        enemies.append(enemy)

    # Quelques packs de soin sur la carte
    for i in range(3):
        pack = Entity(model='cube', color=color.green, scale=0.5,
                      position=(random.uniform(-8, 8), 0.25, random.uniform(-8, 8)),
                      collider='box')
        pack.type = 'health'
        pickups.append(pack)

    # HUD
    crosshair = Entity(parent=camera.ui, model='quad', color=color.white, scale=0.008)

    hp_bg = Entity(parent=camera.ui, model='quad', color=color.black,
                   scale=(0.3, 0.03), position=(-0.7, 0.45), origin=(-0.5, 0.5))
    hp_bar = Entity(parent=camera.ui, model='quad', color=color.lime,
                    scale=(0.3, 0.03), position=(-0.7, 0.45), origin=(-0.5, 0.5))

    ammo_text = Text(text=f'Ammo: {ammo}', parent=camera.ui,
                     position=(0.55, 0.45), scale=1.2)

    game_over_text = Text('GAME OVER', origin=(0,0), scale=2, enabled=False)
    win_text = Text('YOU WIN', origin=(0,0), scale=2, enabled=False)


# ------------------------------------------------------------
# Fonction de tir du joueur
# ------------------------------------------------------------

def shoot():
    global ammo
    if ammo <= 0 or reloading:
        return

    ammo -= 1
    ammo_text.text = f'Ammo: {ammo}'

    flash = Entity(model='quad', color=color.yellow,
                   position=weapon.world_position + weapon.forward * 0.3,
                   parent=scene, scale=0.1)
    destroy(flash, delay=0.05)

    hit_info = raycast(camera.world_position, camera.forward, distance=50, ignore=[player])
    if hit_info.hit and hit_info.entity in enemies:
        target = hit_info.entity
        target.health -= 25
        target.hp.scale_x = target.health / 100
        if target.health <= 0:
            enemies.remove(target)
            drop = None
            if random.random() < 0.5:
                drop = Entity(model='cube', color=color.green, scale=0.5,
                               position=target.position + (0,0.5,0), collider='box')
                drop.type = 'health'
                pickups.append(drop)
            destroy(target)


# ------------------------------------------------------------
# Gestion de l'entrée clavier/souris
# ------------------------------------------------------------

def input(key):
    if not game_started:
        return

    if key == 'left mouse down' and player.health > 0:
        shoot()
    if key == 'r':
        start_reload()


# ------------------------------------------------------------
# Reload
# ------------------------------------------------------------

def start_reload():
    global reloading, reload_timer
    if reloading:
        return
    if ammo >= 10:
        return
    reloading = True
    reload_timer = reload_time


# ------------------------------------------------------------
# Boucle update principale
# ------------------------------------------------------------

def update():
    global reload_timer, reloading, ammo
    global game_started

    if not game_started and not menu.enabled:
        # menu has been disabled -> game started
        game_started = True

    if not game_started:
        return

    if player.health <= 0:
        game_over_text.enabled = True
        mouse.locked = False
        return

    if len(enemies) == 0:
        win_text.enabled = True
        mouse.locked = False
        return

    # Gestion reload
    if reloading:
        reload_timer -= time.dt
        if reload_timer <= 0:
            ammo = 10
            ammo_text.text = f'Ammo: {ammo}'
            reloading = False

    # Ennemis suivent le joueur et tirent
    for enemy in enemies:
        direction = (player.position - enemy.position).normalized()
        enemy.position += direction * enemy.speed * time.dt
        enemy.look_at(player)
        enemy.shoot_timer -= time.dt
        if enemy.shoot_timer <= 0:
            proj = Entity(model='sphere', color=color.orange, scale=0.3,
                           position=enemy.position + enemy.forward*1.5,
                           collider='box')
            proj.direction = enemy.forward
            proj.speed = 6
            projectiles.append(proj)
            enemy.shoot_timer = random.uniform(1.0, 2.5)

    # Projectiles ennemis
    for proj in projectiles[:]:
        proj.position += proj.direction * proj.speed * time.dt
        if proj.intersects(player).hit:
            player.health -= 15
            destroy(proj)
            projectiles.remove(proj)
        elif distance(proj.position, player.position) > 50:
            destroy(proj)
            projectiles.remove(proj)

    # Mise à jour HUD santé
    player.health = max(player.health, 0)
    hp_bar.scale_x = player.health / 100

    # Récupération des pickups
    for p in pickups[:]:
        if player.intersects(p).hit:
            if getattr(p, 'type', None) == 'health':
                player.health = min(100, player.health + 30)
            pickups.remove(p)
            destroy(p)


def distance(a, b):
    return sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)


app.run()
