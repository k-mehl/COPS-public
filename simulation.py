from __future__ import print_function
from vehicle import *
import matplotlib.pyplot as plt
from matplotlib import animation

# create basic figure and axis object
fig = plt.figure(figsize=(22, 10))
#ax = plt.axes(xlim=(-1,21),ylim=(-1,21))

# add subplots
ax = fig.add_subplot(121)
ax1 = fig.add_subplot(122)

x_ax = list(range(-2,24,2))
for axis in (ax, ax1):
    axis.set_xlim(-1,21)
    axis.set_ylim(-1,21)
    # make ticks so we can know where we are 
    axis.set_xticks(x_ax)
    axis.set_yticks(x_ax)
    axis.grid(linestyle='--')

# add plotting objects
dot, = ax.plot([], [], 'ro')
path, = ax.plot([], [], 'b-', lw=2)
path2, = ax.plot([], [], 'r-', lw=2)
dot1, = ax1.plot([], [], 'ro')
path3, = ax1.plot([], [], 'b-', lw=2)
path4, = ax1.plot([], [], 'r-', lw=2)

# add vehicle objects, 2 for now
vec = Vehicle()
print("first vec")
vec.set_destination(18,18)
vec1 = Vehicle()

# the following like should be commented to see what happens when there is no
# information exchange
# it gives the information to vec1 about the route that vec plans to traverse
# hence vec1 changes the route it would otherwise traverse
print("second vec")
vec1.checked = vec.shortest_path
vec1.set_position(18,0)
vec1.set_destination(2,18)

# test vehicles (since there is no copy constructor we cant copy v1 to v2??)
# python has deep_copy...
vec2 = Vehicle()
vec2.set_position(18,0)
vec2.set_destination(2,18)
# dot1, = ax1.plot([], []) this gives an interesting plot connected with
# agreement protocol idea

# initialization function: plot the background of each frame
def init():
    for s in (dot, path, path2, dot1, path3, path4):
        s.set_data([], [])
    return dot, path, path2, dot1, path3, path4

# animation function.  This is called sequentially
def animate(i):
    for v in (vec, vec1, vec2):
        v.update()
    dot.set_data(*zip(vec.get_position(),vec1.get_position()))
    path.set_data(*zip(*vec.route))
    path2.set_data(*zip(*vec1.route))

    dot1.set_data(*zip(vec.get_position(),vec2.get_position()))
    path3.set_data(*zip(*vec.route))
    path4.set_data(*zip(*vec2.route))
    return dot, path, path2, dot1, path3, path4

# blit=True means only re-draw the parts that have changed, could be used to
# make smooth animation of traversed paths less expensive but doesnt work on
# Mac
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=60, interval=40, blit=True)

# doesnt work on my sys properly at the moment, codec...
# anim.save('race.mp4', fps=30)

plt.show()
