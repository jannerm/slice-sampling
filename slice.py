import numpy as np
import scipy.stats as stats
import math, random, time

from bokeh.layouts import row, column
from bokeh.models import Button, RadioButtonGroup
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc
from bokeh.models.widgets import PreText

np.random.seed(1)

class Elliptical:
	def __init__(self, x_low, x_high, x_step=0.01):
		self.mode = -1
		self.num_modes = 5
		self.update_fn = self.stepout
		## x range
		self.X = np.arange(x_low, x_high, x_step)
		## just some arbitrary f(x)
		self.Y = 1.75*stats.norm.pdf(self.X,-3,1.75) + .6*stats.norm.pdf(self.X,.75,.5) + stats.norm.pdf(self.X,3,1)
		## make a patch object over the uniform region under f(x) and above the x axis
		self.__find_patches(self.X, self.Y, 0)
		## initialize things so they are hidden
		self.slice = [-1, -1]
		self.curr_x = -1
		self.fx = -1
		self.curr_y = -1
		self.horizontal = -1
		## initialize figure
		self.figure = Figure(self.X, self.Y, self.patch_xs, self.patch_ys)

	'''
	Progress to the next mode.
	Modes are:
		0) Sample x from interval
		1) Evaluate f(x)
		2) Sample y from Unif(0, f(x))
		3) Show slice S
		4) Choose interval I with stepping out / doubling
	'''
	def next_step(self):
		self.mode = (self.mode + 1) % self.num_modes

		# sample x from slice
		if self.mode == 0: 
			self.curr_x = self.__sample_x()
			# reject x if not in slice
			while self.curr_y > self.__fx(self.curr_x):
				self.curr_x = self.__sample_x()
			# hide f(x), y, and horizontal line
			self.horizontal = -1
			self.fx = -1
			self.curr_y = -1

		## evaluate f(x)
		elif self.mode == 1:
			self.fx = self.__fx(self.curr_x)

		## sample y
		elif self.mode == 2:
			self.curr_y = np.random.uniform(low=0, high=self.fx)
			## hide slice so that it doesn't show up early
			self.slice=[-1,-1]

		## show slice
		elif self.mode == 3:
			self.horizontal = self.curr_y
			
		## show I (stepping out / doubling)
		elif self.mode == 4:
			self.slice = self.update_fn(self.curr_x, self.curr_y)

		self.__refresh()

	'''
	Sample x from interval
	'''
	def __sample_x(self):
		x = np.random.uniform(low=self.slice[0], high=self.slice[1])
		return x

	'''
	Choose the update function
	Called by the radio button
	'''
	def change_update_fn(self, fn):
		if fn == 0:
			self.update_fn = self.stepout
		elif fn == 1:
			self.update_fn = self.double
		else:
			raise RuntimeError(str(fn) + ' not an update function')

	'''
	Stepping out procedure for finding I
	'''
	def stepout(self, x, y, w=1, m=40):
		u = np.random.uniform()
		l = x - w*u
		r = l + w
		v = np.random.uniform()
		j = math.floor(m*v)
		k = m - 1 - j
		while j > 0 and y < self.__fx(l):
			l -= w
			j -= 1
			self.slice = [l, r]
			self.__refresh()
			time.sleep(.25)
		while k > 0 and y < self.__fx(r):
			r += w
			k -= 1
			self.slice = [l, r]
			self.__refresh()
			time.sleep(.25)
		return [l, r]

	'''
	Doubling procedure for finding I
	'''
	def double(self, x, y, w=.25, p=5):
		u = np.random.uniform()
		l = x - w*u
		r = l + w
		k = p
		while k > 0 and (y < self.__fx(l) or y < self.__fx(r)):
			v = np.random.uniform()
			width = r-l
			if v < 0.5:
				l = l - width
			else:
				r = r + width
			self.slice = [l, r]
			self.__refresh()
			time.sleep(.25)
		return [l, r]

	def __fx(self, x):
		ind = np.argmin(np.abs(self.X - x))
		y = self.Y[ind]
		return y

	'''
	Makes bokeh patch objects defined by the the region
	above threshold and below Y over values in X
	'''
	def __find_patches(self, X, Y, threshold):
		## list of patch x coordinates
		patch_xs = []
		## list of patch y coordinates
		patch_ys = []
		signs = np.sign(Y - threshold)
		diff = np.diff(signs)
		for i in range(1,len(diff)):
			if diff[i-1] != 0:
				diff[i] = 0
		
		intersections = np.argwhere(diff != 0).reshape(-1).tolist()
		## insert start and end points to intersections
		intersections.insert(0, 0)
		intersections.append(len(X))
		
		## make dim of X match that of intersections
		X = X.tolist()
		X.insert(0, X[0])
		X.append(X[-1])

		for ind in range(1, len(intersections)):
			start = intersections[ind-1]
			end = intersections[ind]
			midpoint = int(math.floor( (start + end)/2 ))
			above = Y[midpoint] >= threshold
			if above:
				patch_xs.append([])
				patch_ys.append([])
				for ind in range(end, start, -1):
					patch_xs[-1].append(X[ind])
					patch_ys[-1].append(threshold)
				for ind in range(start, end):
					patch_xs[-1].append(X[ind])
					patch_ys[-1].append(Y[ind])

		self.patch_xs = patch_xs
		self.patch_ys = patch_ys

	'''
	Refreshes display
	'''
	def __refresh(self):
		self.figure.refresh(self.X, self.Y, self.curr_x, self.fx, self.curr_y, self.horizontal, self.slice, self.patch_xs, self.patch_ys, self.mode)



class Figure:
	def __init__(self, X, Y, patch_xs, patch_ys):
		self.workspace = figure(x_range=[x_low-2,x_high+2], y_range=[0,.6], toolbar_location=None)
		self.plot = self.workspace.line(x=X, y=Y, line_width=4)
		
		self.point = self.workspace.circle(x=[0], y=[-1], size=10, color="red")
		self.fx = self.workspace.circle(x=[0], y=[-1], size=10, color="red")
		self.sample_y = self.workspace.circle(x=[0], y=[-1], size=10, color="black")
		self.vertical = self.workspace.line(x=[0,0], y=[0,0], color="red", line_width=2)
		self.horizontal = self.workspace.line(x=[0,0], y=[0,0], color="red", line_width=2)
		self.slice = self.workspace.line(x=[0,0], y=[0,0], color="black", line_width=4)
		self.patches = self.workspace.patches(patch_xs, patch_ys, alpha=.3, line_width=2)

		## yeah, this is awful. I don't know 
		## how to center vertically in bokeh
		self.filler1 = PreText(text='', width=200, height=250)
		self.filler2 = PreText(text='', width=200, height=250)

		## for choosing update function
		self.radio = RadioButtonGroup(
		    labels=['Stepping out', 'Doubling'], active=0)
		self.radio.on_click(self.radio_handler)

		## for progressing demo
		self.button = Button(label="Next")
		self.button.on_click(self.callback)

		curdoc().add_root(row(column(self.filler1, self.button), self.workspace, column(self.filler2, self.radio)))

	def radio_handler(self, new):
		e.change_update_fn(new)

	def refresh(self, X, Y, curr_x, fx, curr_y, horizontal, slice_endpoints, patch_xs, patch_ys, mode):
		self.point.data_source.data = {'x': [curr_x], 
											'y': [0]}

		self.fx.data_source.data = {'x': [curr_x], 
											'y': [fx]}

		self.sample_y.data_source.data = {'x': [curr_x], 
											'y': [curr_y]}

		self.vertical.data_source.data = {'x': [curr_x, curr_x],
											'y': [0, fx]}
		self.horizontal.data_source.data = {'x': [-100, 100], 
											'y': [horizontal, horizontal]}

		self.slice.data_source.data = {'x': slice_endpoints,
											'y': [curr_y, curr_y]}

		self.patches.data_source.data = {'xs': patch_xs, 'ys': patch_ys}

	def callback(self):
	    e.next_step()

x_low, x_high = -8, 8

e = Elliptical(x_low, x_high)






