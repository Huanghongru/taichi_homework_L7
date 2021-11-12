import taichi as ti
import numpy as np
import argparse
from ray_tracing_models import Ray, Camera, Hittable_list, Sphere, PI, Box
# from taichi_ray_tracing.ray_tracing_models import Box

ti.init(arch=ti.gpu, debug=True)
PI = 3.14159265

# Canvas
aspect_ratio = 1.0
image_width = 800
image_height = int(image_width / aspect_ratio)
canvas = ti.Vector.field(3, dtype=ti.f32, shape=(image_width, image_height))

# Rendering parameters
samples_per_pixel = 4
max_depth = 10

# direction controller
step = 0.5
dx = {"w": 0, "a": 1, "s": 0, "d": -1, "UP": 0, "DOWN": 0, "LEFT": 1, "RIGHT": -1}
dy = {"w": 1, "a": 0, "s": -1, "d": 0, "UP": 1, "DOWN": -1, "LEFT": 0, "RIGHT": 0}

@ti.kernel
def render():
    for i, j in canvas:
        u = (i + ti.random()) / image_width
        v = (j + ti.random()) / image_height
        color = ti.Vector([0.0, 0.0, 0.0])
        for n in range(samples_per_pixel):
            ray = camera.get_ray(u, v)
            color += ray_color(ray)
        color /= samples_per_pixel
        canvas[i, j] += color

@ti.func
def ray_color(ray):
    default_color = ti.Vector([1.0, 1.0, 1.0])
    scattered_origin = ray.origin
    scattered_direction = ray.direction
    is_hit, hit_point, hit_point_normal, front_face, material, color = scene.hit(Ray(scattered_origin, scattered_direction))
    if is_hit:
        default_color = color
    return default_color


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Naive Ray Tracing')
    parser.add_argument(
        '--max_depth', type=int, default=1, help='max depth (default: 10)')
    parser.add_argument(
        '--samples_per_pixel', type=int, default=4, help='samples_per_pixel  (default: 4)')
    args = parser.parse_args()

    max_depth = args.max_depth
    assert max_depth == 1
    samples_per_pixel = args.samples_per_pixel

    scene = Hittable_list()

    # Light source
    scene.add(Sphere(center=ti.Vector([0, 5.4, -1]), radius=3.0, material=0, color=ti.Vector([10.0, 10.0, 10.0])))
    # Ground
    scene.add(Sphere(center=ti.Vector([0, -100.5, -1]), radius=100.0, material=1, color=ti.Vector([0.8, 0.8, 0.8])))
    # ceiling
    scene.add(Sphere(center=ti.Vector([0, 102.5, -1]), radius=100.0, material=1, color=ti.Vector([0.8, 0.8, 0.8])))
    # back wall
    scene.add(Sphere(center=ti.Vector([0, 1, 101]), radius=100.0, material=1, color=ti.Vector([0.8, 0.8, 0.8])))
    # right wall
    scene.add(Sphere(center=ti.Vector([-101.5, 0, -1]), radius=100.0, material=1, color=ti.Vector([0.6, 0.0, 0.0])))
    # left wall
    scene.add(Sphere(center=ti.Vector([101.5, 0, -1]), radius=100.0, material=1, color=ti.Vector([0.0, 0.6, 0.0])))

    # Metal ball
    scene.add(Sphere(center=ti.Vector([-0.8, 0.2, -1]), radius=0.7, material=2, color=ti.Vector([0.6, 0.8, 0.8])))
    # Diffuse ball
    scene.add(Sphere(center=ti.Vector([0, -0.2, -1.5]), radius=0.3, material=1, color=ti.Vector([0.8, 0.3, 0.3])))
    # Glass ball
    # scene.add(Sphere(center=ti.Vector([0.7, 0, -0.5]), radius=0.5, material=3, color=ti.Vector([1.0, 1.0, 1.0])))
    # Metal ball-2
    # scene.add(Sphere(center=ti.Vector([0.6, -0.3, -2.0]), radius=0.2, material=2, color=ti.Vector([0.8, 0.6, 0.2])))
    # Metal Box
    scene.add(Box(low=ti.Vector([0.7, -0.5, -0.5]), high=ti.Vector([0.2, 1.3, -0.2]), material=2, color=ti.Vector([0.8, 0.6, 0.2])))

    gui = ti.GUI("Ray Tracing - Color Only", res=(image_width, image_height))
    canvas.fill(0)
    cnt = 0
    k = 0
    camera = Camera(fov=60)
    while gui.running:
        render()
        cnt += 1
        gui.set_image(np.sqrt(canvas.to_numpy() / cnt))
        gui.show(f"frames/{k}.png")
        k += 1
        
        for e in gui.get_events(ti.GUI.MOTION, ti.GUI.PRESS):
            if e.key == ti.GUI.MOVE:    # move your mouse to change look-at point
                new_lookat_x = e.pos[0] * camera.cam_horizontal[None][0]
                new_lookat_y = e.pos[1] * camera.cam_vertical[None][1]
                new_lookat_z = -1.0
                
                canvas.fill(0.0)
                camera.reset(new_lookat_x, new_lookat_y, new_lookat_z, 0)
                cnt = 0
            elif e.key == ti.GUI.LMB:   # left-mouse-click to make camera step forward
                new_lookfrom_x = camera.lookfrom[None][0]
                new_lookfrom_y = camera.lookfrom[None][1]
                new_lookfrom_z = camera.lookfrom[None][2] + 0.1*step
                
                canvas.fill(0.0)
                camera.reset(new_lookfrom_x, new_lookfrom_y, new_lookfrom_z, 1)
                cnt = 0
            elif e.key == ti.GUI.RMB:   # right-mouse-click to make camera step backward
                new_lookfrom_x = camera.lookfrom[None][0]
                new_lookfrom_y = camera.lookfrom[None][1]
                new_lookfrom_z = camera.lookfrom[None][2] - 0.1*step
                
                canvas.fill(0.0)
                camera.reset(new_lookfrom_x, new_lookfrom_y, new_lookfrom_z, 1)
                cnt = 0
            elif e.key in ['w', 'a', 's', 'd', 'LEFT', "RIGHT", "UP", "DOWN"]:  # camera four-direction movements
                new_lookfrom_x = camera.lookfrom[None][0] + dx[e.key] * step
                new_lookfrom_y = camera.lookfrom[None][1] + dy[e.key] * step
                new_lookfrom_z = camera.lookfrom[None][2]
                new_lookat_x = camera.lookat[None][0] + dx[e.key] * step
                new_lookat_y = camera.lookat[None][1] + dy[e.key] * step
                new_lookat_z = camera.lookat[None][2]
                
                canvas.fill(0.0)
                camera.reset(new_lookfrom_x, new_lookfrom_y, new_lookfrom_z, 1)
                camera.reset(new_lookat_x, new_lookat_y, new_lookat_z, 0)
                cnt = 0