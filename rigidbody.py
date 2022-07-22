import taichi as ti
import math

ti.init()

num_particles = 968
dim=3
world_scale_factor = 1.0/100.0
mu_N = 0.9 # normal velocity attenuation factor
mu_T = 0.2 # coulomb friction factor
dt = 1.0

positions = ti.Vector.field(dim, float, num_particles)
velocities = ti.Vector.field(dim, float, num_particles)
pos_draw = ti.Vector.field(dim, float, num_particles)
is_collided = ti.field(ti.i32, num_particles)
any_is_collided = ti.field(ti.i32, shape=())
paused = ti.field(ti.i32, shape=())
pos_draw_red = ti.Vector.field(dim, float, num_particles)
positions_inter = ti.Vector.field(dim, float, num_particles)
radius_vector = ti.Vector.field(dim, float, num_particles)

@ti.kernel
def init_particles():
    init_pos = ti.Vector([0.0, 10.0, 0.0])
    cube_size = 20 
    spacing = 2 
    num_per_row = (int) (cube_size // spacing) + 1
    num_per_floor = num_per_row * num_per_row
    for i in range(num_particles):
        floor = i // (num_per_floor) 
        row = (i % num_per_floor) // num_per_row
        col = (i % num_per_floor) % num_per_row
        positions[i] = ti.Vector([col*spacing, floor*spacing, row*spacing]) + init_pos


def init_velocities():
    velocities.fill(ti.Vector([0.0, -0.1, 0.0]))

@ti.kernel
def translation():
    for i in range(num_particles):
        positions[i] += velocities[i] * dt

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
    # if (any_is_collided[None] == True):
    #     print(f"at least one particle is collided!")

@ti.kernel
def collision_response_particle():
    n_dir = ti.Vector([1, ti.sqrt(3), 0]).normalized()

    for i in range(num_particles):
        if(is_collided[i] == True and velocities[i].dot(n_dir) < 0):
            vn = velocities[i].dot(n_dir) * n_dir
            vt = velocities[i] - vn
            
            vn_new = -mu_N * vn
            a = ti.max((1 - mu_T * (1 + mu_N) * vn.norm() / (vt.norm() + 1e-5) ), 0)
            vt_new = a * vt
            
            velocities[i] = vn_new + vt_new

            #move to the boundary
            phi = 0.1
            positions_inter[i] += ti.abs(phi) * n_dir

@ti.kernel
def shape_matching():
    #compute the radius vector 
    #(vector from the old center of mass to the point)
    sum = ti.Vector([0.0, 0.0, 0.0])
    for i in range(num_particles):
        sum += positions[i]
    center_mass = (1.0 / num_particles) * sum
    for i in range(num_particles):
        radius_vector[i] = positions[i] - center_mass
    print(center_mass)

    #compute the new center of mass
    sum = ti.Vector([0.0, 0.0, 0.0])
    for i in range(num_particles):
        sum += positions_inter[i]
    center_mass_new = (1.0 / num_particles) * sum
    print(center_mass_new)

    #compute the transformation matrix
    pass
    #polar decomposition and extract rotation
    pass
    R = ti.Matrix.identity(ti.f32, 3)

    #update the velocities and positions
    for i in range(num_particles):
        velocities[i] = (center_mass_new + R @ radius_vector[i] - positions[i]) / dt
        positions[i] = center_mass_new + R @ radius_vector[i]


@ti.kernel
def collision_response_force():
    n_dir = ti.Vector([1, ti.sqrt(3), 0]).normalized()
    k = 0.1
    eps = 2.0
    mass_inv = 1.0

    for i in range(num_particles):
        if(is_collided[i] == True and velocities[i].dot(n_dir) < 0):
            phi = positions[i].y
            penalty_force = k * (eps - phi) * n_dir
            velocities[i] += dt * mass_inv * penalty_force
            positions[i] += dt * velocities[i]

#dye the rebounced particle to red, for DEBUG use
@ti.kernel
def dye_rebounced_red():
    for i in pos_draw_red:
        pos_draw_red[i] = ti.Vector([-1e10, -1e10, -1e10]) # throw away from screen
        if is_collided[i] == True:
            pos_draw_red[i] = pos_draw[i]

def substep():
    is_collided.fill(0)
    any_is_collided.fill(0)
    translation()
    collision_detection()
    if any_is_collided[None] == True:
        collision_response_particle()
        # collision_response_force()
        shape_matching()
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
    init_velocities()

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
        dye_rebounced_red()
        scene.particles(pos_draw_red, radius=0.01, color=(1, 0, 0))

        #show the frame
        canvas.scene(scene)
        window.show()

if __name__ == '__main__':
    main()
