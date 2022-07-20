import taichi as ti

ti.init()

num_particles = 968
dim=3

positions = ti.Vector.field(dim, float, num_particles)

@ti.kernel
def init_particles():
    init_pos = ti.Vector([0.0, 0.0, 0.0]) /100.0 
    cube_size = 20 /100.0
    spacing = 2 /100.0
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

def substep():
    translation(ti.Vector([0, 0.01, 0.0]) / 100.0)
    pass

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
        #do the simulation in each step
        for i in range(5):
            substep()

        #set the camera, you can move around by pressing 'wasdeq'
        camera.track_user_inputs(window, movement_speed=0.03, hold_key=ti.ui.RMB)
        scene.set_camera(camera)

        #set the light
        scene.point_light(pos=(0, 1, 2), color=(1, 1, 1))
        scene.point_light(pos=(0.5, 1.5, 0.5), color=(0.5, 0.5, 0.5))
        scene.ambient_light((0.5, 0.5, 0.5))
        
        #draw particles
        scene.particles(positions, radius=0.01, color=(0, 1, 1))

        #show the frame
        canvas.scene(scene)
        window.show()

if __name__ == '__main__':
    main()
