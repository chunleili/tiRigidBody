import taichi as ti
import math

ti.init()

num_particles = 968
dim=3
world_scale_factor = 1.0/100.0

positions = ti.Vector.field(dim, float, num_particles)
velocities = ti.Vector.field(dim, float, num_particles)
pos_draw = ti.Vector.field(dim, float, num_particles)
is_collided = ti.field(ti.i32, num_particles)
any_is_collided = ti.field(ti.i32, shape=())
paused = ti.field(ti.i32, shape=())

@ti.kernel
def init_particles():
    init_pos = ti.Vector([0.0, 0.0, 0.0])
    cube_size = 20 
    spacing = 2 
    num_per_row = (int) (cube_size // spacing) + 1
    num_per_floor = num_per_row * num_per_row
    for i in range(num_particles):
        floor = i // (num_per_floor) 
        row = (i % num_per_floor) // num_per_row
        col = (i % num_per_floor) % num_per_row
        positions[i] = ti.Vector([col*spacing, floor*spacing, row*spacing]) + init_pos

@ti.kernel
def translation(x: ti.types.vector(3, ti.f32)):
    for i in range(num_particles):
        positions[i] += x

@ti.kernel
def rotation():
    theta = 0.1 / 180.0 * math.pi
    R = ti.Matrix([
    [ti.cos(theta), -ti.sin(theta), 0.0], 
    [ti.sin(theta), ti.cos(theta), 0.0], 
    [0.0, 0.0, 1.0]
    ])
    for i in range(num_particles):
        positions[i] = R@positions[i]

@ti.kernel
def collision_detection():
    for i in range(num_particles):
        if (positions[i].y < 0):
            is_collided[i] = True
            # print(f"particle {i} is collied!")
            any_is_collided[None] = True
    if (any_is_collided[None] == True):
        print(f"at least one particle is collided!")


def substep():
    translation(ti.Vector([0, -0.1, 0.0]) )
    # collision_detection()
    # rotation()

@ti.kernel
def world_scale():
    for i in range(num_particles):
        pos_draw[i] = positions[i] * world_scale_factor

#init the window, canvas, scene and camerea
window = ti.ui.Window("rigidbody", (1024, 1024),vsync=True)
canvas = window.get_canvas()
scene = ti.ui.Scene()
camera = ti.ui.make_camera()

#initial camera position
camera.position(0.5, 1.0, 1.95)
camera.lookat(0.5, 0.3, 0.5)
camera.fov(55)

def main():
    init_particles()

    while window.running:
        if window.get_event(ti.ui.PRESS):
            #press space to pause the simulation
            if window.event.key == ti.ui.SPACE:
                paused[None] = not paused[None]

        #do the simulation in each step
        if (paused[None] == False) :
            for i in range(1):
                substep()

        #set the camera, you can move around by pressing 'wasdeq'
        camera.track_user_inputs(window, movement_speed=0.03, hold_key=ti.ui.RMB)
        scene.set_camera(camera)

        #set the light
        scene.point_light(pos=(0, 1, 2), color=(1, 1, 1))
        scene.point_light(pos=(0.5, 1.5, 0.5), color=(0.5, 0.5, 0.5))
        scene.ambient_light((0.5, 0.5, 0.5))
        
        #draw particles
        world_scale()
        scene.particles(pos_draw, radius=0.01, color=(0, 1, 1))

        #show the frame
        canvas.scene(scene)
        window.show()

if __name__ == '__main__':
    main()
