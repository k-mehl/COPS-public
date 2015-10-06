from vehicle import *
import matplotlib.pyplot as plt
from matplotlib import animation


x_ax = list(range(-2,24,2))
fig = plt.figure()
ax = plt.axes(xlim=(-1,21),ylim=(-1,21))
ax.grid(linestyle='--')
ax.set_xticks(x_ax)
ax.set_yticks(x_ax)

line, = ax.plot([], [], 'ro')
path, = ax.plot([], [], 'b-', lw=2)
path2, = ax.plot([], [], 'r-', lw=2)


vec = Vehicle()
vec.set_destination(18,18)
vec1 = Vehicle()
vec1.checked = vec.shortest_path
vec1.set_position(18,0)
vec1.set_destination(2,18)

# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    path.set_data([], [])
    path2.set_data([], [])
    return line, path, path2

# animation function.  This is called sequentially
def animate(i):
    vec.update()
    vec1.update()
    line.set_data(*zip(vec.get_position(),vec1.get_position()))
    path.set_data(*zip(*vec.route))
    path2.set_data(*zip(*vec1.route))
    return line, path, path2

# call the animator.  blit=True means only re-draw the parts that have changed.
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=100, interval=40, blit=True)

# doesnt work on my sys properly at the moment, codec...
# anim.save('race.mp4', fps=30)

plt.show()

