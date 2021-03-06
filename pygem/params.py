"""
Utilities for reading and writing parameters files to perform the Free Form Deformation (FFD)
"""
import os
import ConfigParser
import numpy as np
import pygem.affine as at


class FFDParameters(object):
	"""
	Class that handles the Free Form Deformation parameters in terms of FFD bounding box and
	weight of the FFD control points.

	:param list n_control_points: number of control points in the x, y, and z direction.
		If not provided it is set to [2, 2, 2].

	:cvar float length_box_x: length of the FFD bounding box in the x direction
		(local coordinate system).
	:cvar float length_box_y: length of the FFD bounding box in the y direction
		(local coordinate system).
	:cvar float length_box_z: length of the FFD bounding box in the z direction
		(local coordinate system).

	:cvar numpy.ndarray origin_box: a 3-by-1 vector of float numbers representing the x, y and z
		coordinates of the origin of the FFD bounding box.

	:cvar float rot_angle_x: rotation angle around x axis of the FFD bounding box.
	:cvar float rot_angle_y: rotation angle around y axis of the FFD bounding box.
	:cvar float rot_angle_z: rotation angle around z axis of the FFD bounding box.

	:cvar list n_control_points: list of 3 int representing the number of control points in the
		x, y, and z direction.

	:cvar numpy.ndarray array_mu_x: collects the displacements (weights) along x,
		normalized with the box lenght x.
	:cvar numpy.ndarray array_mu_y: collects the displacements (weights) along y,
		normalized with the box lenght y.
	:cvar numpy.ndarray array_mu_z: collects the displacements (weights) along z,
		normalized with the box lenght z.

	:cvar numpy.ndarray psi_mapping: map from the pysical domain to the reference domain.
	:cvar numpy.ndarray inv_psi_mapping: map from the reference domain to the physical domain.

	:cvar numpy.ndarray rotation_matrix: rotation matrix (according to rot_angle_x,
		rot_angle_y, rot_angle_z).

	:cvar numpy.ndarray position_vertex_0: position of the first vertex of the FFD bounding box.
		It is always equal to the member `origin_box`.
	:cvar numpy.ndarray position_vertex_1: position of the second vertex of the FFD bounding box.
	:cvar numpy.ndarray position_vertex_2: position of the third vertex of the FFD bounding box.
	:cvar numpy.ndarray position_vertex_3: position of the fourth vertex of the FFD bounding box.

	:Example:

	>>> import pygem.params as ffdp

	>>> # Reading an existing file
	>>> params1 = ffdp.FFDParameters()
	>>> params1.read_parameters(filename='tests/test_datasets/parameters_test_ffd_identity.prm')

	>>> # Creating a defaul paramters file with the right dimensions (if the file does not exists
	>>> # it is created with that name). So it is possible to manually edit it and read it again.
	>>> params2 = ffdp.FFDParameters(n_control_points=[2, 3, 2])
	>>> params2.read_parameters(filename='parameters_test.prm')
	
	.. note::
		Four vertex (non coplanar) are sufficient to uniquely identify a parallelepiped.
		If the four vertex are coplanar, an assert is thrown when affine_points_fit is used.

    """
	def __init__(self, n_control_points=None):
		self.conversion_unit = 1.

		self.lenght_box_x = 1.
		self.lenght_box_y = 1.
		self.lenght_box_z = 1.

		self.origin_box = np.array([0., 0., 0.])

		self.rot_angle_x = 0.
		self.rot_angle_y = 0.
		self.rot_angle_z = 0.

		if n_control_points is None:
			n_control_points = [2, 2, 2]
		self.n_control_points = n_control_points

		self.array_mu_x = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))
		self.array_mu_y = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))
		self.array_mu_z = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))

		self.psi_mapping = np.diag([1./self.lenght_box_x, 1./self.lenght_box_y, 1./self.lenght_box_z])
		self.inv_psi_mapping = np.diag([self.lenght_box_x, self.lenght_box_y, self.lenght_box_z])

		self.rotation_matrix = np.eye(3)
		self.position_vertex_0 = self.origin_box
		self.position_vertex_1 = np.array([1., 0., 0.])
		self.position_vertex_2 = np.array([0., 1., 0.])
		self.position_vertex_3 = np.array([0., 0., 1.])


	def read_parameters(self, filename='parameters.prm'):
		"""
		Reads in the parameters file and fill the self structure.

		:param string filename: parameters file to be read in.
		"""
		if not isinstance(filename, basestring):
			raise TypeError("filename must be a string")

		# Checks if the parameters file exists. If not it writes the default class into filename.
		if not os.path.isfile(filename):
			self.write_parameters(filename)
			return
		
		config = ConfigParser.RawConfigParser()
		config.read(filename)

		self.n_control_points[0] = config.getint('Box info', 'n control points x')
		self.n_control_points[1] = config.getint('Box info', 'n control points y')
		self.n_control_points[2] = config.getint('Box info', 'n control points z')

		self.lenght_box_x = config.getfloat('Box info', 'box lenght x')
		self.lenght_box_y = config.getfloat('Box info', 'box lenght y')
		self.lenght_box_z = config.getfloat('Box info', 'box lenght z')

		origin_box_x = config.getfloat('Box info', 'box origin x')
		origin_box_y = config.getfloat('Box info', 'box origin y')
		origin_box_z = config.getfloat('Box info', 'box origin z')
		self.origin_box = np.array([origin_box_x, origin_box_y, origin_box_z])

		self.rot_angle_x = config.getfloat('Box info', 'rotation angle x')
		self.rot_angle_y = config.getfloat('Box info', 'rotation angle y')
		self.rot_angle_z = config.getfloat('Box info', 'rotation angle z')

		self.array_mu_x = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))
		mux = config.get('Parameters weights', 'parameter x')
		lines = mux.split('\n')
		for line in lines:
			values = line.split()
			self.array_mu_x[int(values[0])][int(values[1])][int(values[2])] = float(values[3])

		self.array_mu_y = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))
		muy = config.get('Parameters weights', 'parameter y')
		lines = muy.split('\n')
		for line in lines:
			values = line.split()
			self.array_mu_y[int(values[0])][int(values[1])][int(values[2])] = float(values[3])

		self.array_mu_z = np.zeros((self.n_control_points[0], self.n_control_points[1], \
			self.n_control_points[2]))
		muz = config.get('Parameters weights', 'parameter z')
		lines = muz.split('\n')
		for line in lines:
			values = line.split()
			self.array_mu_z[int(values[0])][int(values[1])][int(values[2])] = float(values[3])

		self.rotation_matrix = at.angles2matrix(self.rot_angle_z * np.pi/180, \
				self.rot_angle_y * np.pi/180, self.rot_angle_x * np.pi/180)

		self.position_vertex_0 = self.origin_box
		self.position_vertex_1 = self.position_vertex_0 + \
			np.dot(self.rotation_matrix, [self.lenght_box_x, 0, 0])
		self.position_vertex_2 = self.position_vertex_0 + \
			np.dot(self.rotation_matrix, [0, self.lenght_box_y, 0])
		self.position_vertex_3 = self.position_vertex_0 + \
			np.dot(self.rotation_matrix, [0, 0, self.lenght_box_z])

		self.psi_mapping = np.diag([1./self.lenght_box_x, 1./self.lenght_box_y, 1./self.lenght_box_z])
		self.inv_psi_mapping = np.diag([self.lenght_box_x, self.lenght_box_y, self.lenght_box_z])

	
	def write_parameters(self, filename='parameters.prm'):
		"""
		This method writes a parameters file (.prm) called `filename` and fills it with all
		the parameters class members.
		
		:param string filename: parameters file to be written out.
		"""
		if not isinstance(filename, basestring):
			raise TypeError("filename must be a string")

		with open(filename, 'w') as output_file:
			output_file.write('\n[Box info]\n')
			output_file.write('# This section collects all the properties of the FFD bounding box.\n')

			output_file.write('\n# n control points indicates the number of control points in each direction (x, y, z).\n')
			output_file.write('# For example, to create a 2 x 3 x 2 grid, use the following: n control points: 2, 3, 2\n')
			output_file.write('n control points x: ' + str(self.n_control_points[0]) + '\n')
			output_file.write('n control points y: ' + str(self.n_control_points[1]) + '\n')
			output_file.write('n control points z: ' + str(self.n_control_points[2]) + '\n')

			output_file.write('\n# box lenght indicates the length of the FFD bounding box along the three canonical directions (x, y, z).\n')
			output_file.write('# It uses the local coordinate system.\n')
			output_file.write('# For example to create a 2 x 1.5 x 3 meters box use the following: lenght box: 2.0, 1.5, 3.0\n')
			output_file.write('box lenght x: ' + str(self.lenght_box_x) + '\n')
			output_file.write('box lenght y: ' + str(self.lenght_box_y) + '\n')
			output_file.write('box lenght z: ' + str(self.lenght_box_z) + '\n')

			output_file.write('\n# box origin indicates the x, y, and z coordinates of the origin of the FFD bounding box. That is center of\n')
			output_file.write('# rotation of the bounding box. It corresponds to the point coordinates with position [0][0][0].\n')
			output_file.write('# See section "Parameters weights" for more details.\n')
			output_file.write('# For example, if the origin is equal to 0., 0., 0., use the following: origin box: 0., 0., 0.\n')
			output_file.write('box origin x: ' + str(self.origin_box[0]) + '\n')
			output_file.write('box origin y: ' + str(self.origin_box[1]) + '\n')
			output_file.write('box origin z: ' + str(self.origin_box[2]) + '\n')

			output_file.write('\n# rotation angle indicates the rotation angle around the x, y, and z axis of the FFD bounding box in degrees.\n')
			output_file.write('# The rotation is done with respect to the box origin.\n')
			output_file.write('# For example, to rotate the box by 2 deg along the z direction, use the following: rotation angle: 0., 0., 2.\n')
			output_file.write('rotation angle x: ' + str(self.rot_angle_x) + '\n')
			output_file.write('rotation angle y: ' + str(self.rot_angle_y) + '\n')
			output_file.write('rotation angle z: ' + str(self.rot_angle_z) + '\n')

			output_file.write('\n\n[Parameters weights]\n')
			output_file.write('# This section describes the weights of the FFD control points.\n')
			output_file.write('# We adopt the following convention:\n')
			output_file.write('# For example with a 2x2x2 grid of control points we have to fill a 2x2x2 matrix of weights.\n')
			output_file.write('# If a weight is equal to zero you can discard the line since the default is zero.\n')
			output_file.write('#\n')
			output_file.write('# | x index | y index | z index | weight |\n')
			output_file.write('#  --------------------------------------\n')
			output_file.write('# |    0    |    0    |    0    |  1.0   |\n')
			output_file.write('# |    0    |    1    |    1    |  0.0   | --> you can erase this line without effects\n')
			output_file.write('# |    0    |    1    |    0    | -2.1   |\n')
			output_file.write('# |    0    |    0    |    1    |  3.4   |\n')
			
			output_file.write('\n# parameter x collects the displacements along x, normalized with the box lenght x.')
			output_file.write('\nparameter x:')
			offset = 1
			for i in range(0, self.n_control_points[0]):
				for j in range(0, self.n_control_points[1]):
					for k in range(0, self.n_control_points[2]):
						output_file.write(offset * ' ' + str(i) + '   ' + str(j) + '   ' + str(k) + \
							'   ' + str(self.array_mu_x[i][j][k]) + '\n')
						offset = 13

			output_file.write('\n# parameter y collects the displacements along y, normalized with the box lenght y.')
			output_file.write('\nparameter y:')
			offset = 1
			for i in range(0, self.n_control_points[0]):
				for j in range(0, self.n_control_points[1]):
					for k in range(0, self.n_control_points[2]):
						output_file.write(offset * ' ' + str(i) + '   ' + str(j) + '   ' + str(k) + \
							'   ' + str(self.array_mu_y[i][j][k]) + '\n')
						offset = 13

			output_file.write('\n# parameter z collects the displacements along z, normalized with the box lenght z.')
			output_file.write('\nparameter z:')
			offset = 1
			for i in range(0, self.n_control_points[0]):
				for j in range(0, self.n_control_points[1]):
					for k in range(0, self.n_control_points[2]):
						output_file.write(offset * ' ' + str(i) + '   ' + str(j) + '   ' + str(k) + \
							'   ' + str(self.array_mu_z[i][j][k]) + '\n')
						offset = 13


	def print_info(self):
		"""
		This method prints all the FFD parameters on the screen. Its purpose is for debugging.
		"""
		print 'conversion_unit = ' + str(self.conversion_unit) + '\n'
		print '(lenght_box_x, lenght_box_y, lenght_box_z) = (' + str(self.lenght_box_x) + \
			', ' + str(self.lenght_box_y) + ', ' + \
		str(self.lenght_box_z) + ')'
		print 'origin_box = ' + str(self.origin_box)
		print 'n_control_points = ' + str(self.n_control_points)
		print '(rot_angle_x, rot_angle_y, rot_angle_z) = (' + str(self.rot_angle_x) + \
			', ' + str(self.rot_angle_y) + ', ' + \
		str(self.rot_angle_z) + ')'
		print '\narray_mu_x ='
		print self.array_mu_x
		print '\narray_mu_y ='
		print self.array_mu_y
		print '\narray_mu_z ='
		print self.array_mu_z
		print '\npsi_mapping ='
		print self.psi_mapping
		print '\ninv_psi_mapping ='
		print self.inv_psi_mapping
		print '\nrotation_matrix ='
		print self.rotation_matrix
		print '\nposition_vertex_0 ='
		print self.position_vertex_0
		print '\nposition_vertex_1 ='
		print self.position_vertex_1
		print '\nposition_vertex_2 ='
		print self.position_vertex_2
		print '\nposition_vertex_3 ='
		print self.position_vertex_3


