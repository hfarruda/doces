/*
MIT License

Copyright (c) 2023 Henrique F. de Arruda, Kleber A. Oliveira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

//This code is adapted from cxrandomwalk by Filipi Nascimento Silva.
//https://github.com/filipinascimento/cxrandomwalk

#define PY_SSIZE_T_CLEAN
#include "version.h"
#include "documentation.h"
#include <dynamics.h>
#include <Python.h>
// #include <pthread.h>

// #define NO_IMPORT_ARRAY
#define PY_ARRAY_UNIQUE_SYMBOL simulator_ARRAY_API
#include <numpy/arrayobject.h>


static PyArrayObject *
pyvector(PyObject *objin)
{
	return (PyArrayObject *)PyArray_ContiguousFromObject(objin, NPY_FLOAT, 1, 1);
}

static PyArrayObject *
convertToUIntegerArray(PyObject *object, int minDepth, int maxDepth)
{
	int flags = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ALIGNED;
	return PyArray_FromAny(
		object, PyArray_DescrFromType(NPY_UINT64), minDepth, maxDepth, flags, NULL);
}

static PyArrayObject *
convertToIntegerArray(PyObject *object, int minDepth, int maxDepth)
{
	int flags = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ALIGNED;
	return PyArray_FromAny(
		object, PyArray_DescrFromType(NPY_INT64), minDepth, maxDepth, flags, NULL);
}

static PyArrayObject *
convertToDoubleArray(PyObject *object, int minDepth, int maxDepth)
{
	int flags = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ALIGNED;
	return PyArray_FromAny(object,
							 PyArray_DescrFromType(NPY_FLOAT64),
							 minDepth,
							 maxDepth,
							 flags,
							 NULL);
}

static PyArrayObject *
convertToFLOATArray(PyObject *object, int minDepth, int maxDepth)
{
	int flags = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ALIGNED;
	return PyArray_FromAny(object,
							 PyArray_DescrFromType(NPY_FLOAT32),
							 minDepth,
							 maxDepth,
							 flags,
							 NULL);
}

/* ==== Create 1D Carray from PyArray ======================
																																Assumes PyArray
	 is contiguous in memory.             */
static void *
pyvector_to_Carrayptrs(PyArrayObject *arrayin)
{
	// int n;
	// n = arrayin->dimensions[0];
	return PyArray_DATA(arrayin); /* pointer to arrayin data as double */
}

/* ==== Check that PyArrayObject is a double (FLOAT) type and a vector
				 ============== return 1 if an error and raise exception */
static int
not_FLOATvector(PyArrayObject *vec)
{
	if (vec->descr->type_num != NPY_FLOAT) {
		PyErr_SetString(PyExc_ValueError,
						"In not_FLOATvector: array must be of "
						"type FLOAT and 1 dimensional (n).");
		return 1;
	}
	return 0;
}

/* ==== Check that PyArrayObject is a double (FLOAT) type and a vector
				 ============== return 1 if an error and raise exception */
// FIXME: make it work for 32bits
static int
not_intvector(PyArrayObject *vec)
{
	if (vec->descr->type_num != NPY_UINT64) {
		PyErr_SetString(
			PyExc_ValueError,
			"In not_intvector: array must be of type Long and 1 dimensional (n).");
		return 1;
	}
	return 0;
}

typedef struct _PyDynamics{//Colocar aqui as variáveis que seriam globais
	PyObject_HEAD Network *network;
	Feeds *feeds;
	PostList *postList;
	unsigned long int executedIterations;
	unsigned long int rewiringsCount;
	char postingFilterType;
	char receivingFilterType;
	char *postingFilterTypes;
	char *receivingFilterTypes;
	bool *stubborn;
	FLOAT *b;
	bool verbose;
} PyDynamics;

int PyDynamics_traverse(PyDynamics *self, visitproc visit, void *arg)
{
	// Py_VISIT(self->...);
	return 0;
}

int PyDynamics_clear(PyDynamics *self)
{
	// Py_CLEAR(self->...);
	return 0;
}

void PyDynamics_dealloc(PyDynamics *self)
{
	Py_TYPE(self)->tp_free((PyObject *)self);
}

PyObject * 
PyDynamics_del(PyDynamics *self)
{
	if (self->verbose){
		printf("Cleaning variables ...\n");
		PROGRESS_BAR(0, 8);
	}
	
	destroyFeed(self->feeds, self->network->vCount);
	if (self->verbose)  
		PROGRESS_BAR(1, 8);
	
	destroyPostList(self->postList);
	if (self->verbose)	
		PROGRESS_BAR(2, 8);
	
	if (self->postingFilterTypes){
		free(self->postingFilterTypes);
		self->postingFilterTypes = NULL;
	}
	if (self->verbose)
		PROGRESS_BAR(3, 8);

	if (self->receivingFilterTypes){
		free(self->receivingFilterTypes);
		self->receivingFilterTypes = NULL;
	}
	if (self->verbose)
		PROGRESS_BAR(4, 8);

	destroyNetwork(self->network);
	if (self->verbose)
		PROGRESS_BAR(5, 8);

	if (self->b){
		free(self->b);
		self->b = NULL;
	}
	if (self->verbose)
		PROGRESS_BAR(6, 8);

	if (self->stubborn){
		free(self->stubborn);
		self->stubborn = NULL;
	}

	if (self->verbose)
		PROGRESS_BAR(7, 8);

	return Py_BuildValue("", NULL);
}

PyObject *
PyDynamics_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyDynamics *self;
	self = (PyDynamics *)type->tp_alloc(type, 0);
	// self->network = NULL;

	return (PyObject *)self;
}

int PyDynamics_init(PyDynamics *self, PyObject *args, PyObject *kwds){
	static char *kwlist[] = {
		"vertex_count",
		"edges",
		"directed",
		"verbose",
		NULL
	};
	
	PyObject *edgesObject = NULL;
	PyArrayObject *edgesArray = NULL;
	Py_ssize_t vertexCount = 0;
	int isDirected = 0;
	int isVerbose = 0;

	if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									 "nOp|p",
									 kwlist,
									 &vertexCount,
									 &edgesObject,
									 &isDirected,
									 &isVerbose)) {
		return EXIT_FAILURE;
	}

	if (vertexCount <= 0) {
		PyErr_SetString(PyExc_TypeError,
						"The number of nodes (vertexCount) must be a positive integer.");
		return EXIT_FAILURE;
	}

	if (!(edgesArray = convertToIntegerArray(edgesObject, 1, 2))) {
		PyErr_SetString(PyExc_TypeError,
						"Error creating edge arrays.");
		return EXIT_FAILURE;
	}

	unsigned long int edgeCount = (unsigned long int) PyArray_SIZE(edgesArray) / 2;
	npy_int64 *edges = PyArray_DATA(edgesArray);

	self->verbose = (bool) isVerbose;

	if (self->verbose)
		printf("Loading the edge list with %lu edges:\n", edgeCount);
	
	//Creating edge list in C
	unsigned int source;
	unsigned int target;
	EdgeList *edgeList = malloc(sizeof(EdgeList));
	edgeList->vCount = (unsigned int) vertexCount;
	edgeList->eCount = edgeCount;
	edgeList->edges = (Edge*) malloc(edgeCount * sizeof(Edge));
	edgeList->isDirected = isDirected;
	
	for (unsigned int i=0; i<edgeCount; i++) {
		if (self->verbose){ 
			PROGRESS_BAR(i, edgeCount);
		}
		source = (unsigned int) edges[2 * i];
		target = (unsigned int) edges[2 * i + 1];
		if (source >= vertexCount || target >= vertexCount) {
			PyErr_SetString(
				PyExc_TypeError,
				"Edge indices should not be higher than the number of vertices.");
			Py_XDECREF(edgesArray);
			free(edgeList->edges);
			free(edgeList);
			printf("\n\n\n ERROR!!! \n\n\n");
			return EXIT_FAILURE;
		}
		edgeList->edges[i].source = source;
		edgeList->edges[i].target = target;
	}

	if (self->verbose){
		printf("\nCreating the inverted Adj. list.\n");
	}

	self->network = malloc(sizeof(Network));
 	edgeList2Network(self->network , *edgeList, self->verbose);
	if (self->verbose && self->network->vCount < 50) 
		printNetwork(self->network);
	
	free(edgeList->edges);
	free(edgeList);

	self->executedIterations = 1;//Starts at 1 because 0 is when the first posts are created.
	self->rewiringsCount = 0;
	// if (self->postList){
	// 	destroyPostList(self->postList);
	// }
	self->postList = NULL;

	// if (self->feeds){
	// 	destroyFeed(self->feeds, self->feeds->feedSize);
	// }
	self->feeds = NULL;

	//To be sure that it will be correctly initialized
	self->postingFilterType = -1;
	self->receivingFilterType = -1;


	if (self->verbose){
		printf("========================================\n");
		printf("Network summary:\n");
		printf("========================================\n");
		printf("Directed:");
		if (self->network->isDirected)
			printf(" True \n");	
		else
			printf(" False \n");
		printf("Vertices: %d\n", (int) self->network->vCount);
		printf("========================================\n");
	}
	
	self->stubborn = (bool*) malloc(self->network->vCount * sizeof(bool));
	for (unsigned int i = 0; i < self->network->vCount; i++){//initialize with zeros
		self->stubborn[i] = false;
	}

	Py_XDECREF(edgesArray);
	// Py_XDECREF(edges);
	return EXIT_SUCCESS;
}

// PyMemberDef PyDynamics_members[] = {
// 	{NULL} /* Sentinel */
// };

PyListObject * PyGetOpinions(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* b = NULL;
	b = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->network->vCount; i++){
			value = Py_BuildValue("f", self->b[i]);
			PyList_Append(b, value);
			Py_DECREF(value);
		}
	return b;
}

PyListObject *PyGetEdgeList(PyDynamics *self){
	PyListObject* measurementList = PyList_New(0);
	if (self->network && self->network && self->network->vCount>0){
		PyObject *value = NULL;
		EdgeList *edgeListOut = malloc(sizeof(EdgeList));
		network2EdgeList(self->network, edgeListOut, self->verbose);
		PyListObject* pyEdge = NULL;
		for (unsigned long int i=0; i<edgeListOut->eCount; i++){
			pyEdge = PyList_New(0);
			value = Py_BuildValue("i", edgeListOut->edges[i].source);
			PyList_Append(pyEdge, value);
			Py_DECREF(value);

			value = Py_BuildValue("i", edgeListOut->edges[i].target);
			PyList_Append(pyEdge, value);
			Py_DECREF(value);

			PyList_Append(measurementList, pyEdge);
			Py_DECREF(pyEdge);
		}
		free(edgeListOut->edges);
		free(edgeListOut);
	}
	return measurementList;
}

Py_ssize_t PyGetRewireCounts(PyDynamics *self){
	return Py_BuildValue("n", self->rewiringsCount);
}

PyListObject * PyGetPostIds(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].id);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostThetas(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("d", self->postList->post[i].theta);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostPostedCounts(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].postedCount);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostCascadeSizes(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].cascadeSize);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostBirthdays(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].birth);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostDeaths(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].death);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostLivePosts(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("l", self->postList->post[i].livePosts);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

PyListObject * PyGetPostUserOpinios(PyDynamics *self){
	PyObject* value = NULL;
	PyListObject* pyList = NULL;
	pyList = PyList_New(0);
	if (self->b && self->network)
		for (unsigned int i=0; i<self->postList->numberOfPosts; i++){
			value = Py_BuildValue("d", self->postList->post[i].userOpinion);
			PyList_Append(pyList, value);
			Py_DECREF(value);
		}
	return pyList;
}

static PyGetSetDef PyDynamics_getsetters[] = {
	{"opinions",
	 (PyCFunction)PyGetOpinions,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of agent opinions."},
	 {"edge_list",
	 (PyCFunction)PyGetEdgeList,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get edgelist."},
	 {"rewiring_count",
	 (PyCFunction)PyGetRewireCounts,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get rewiring count."},
	 {"post_ids",
	 (PyCFunction)PyGetPostIds,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of post ids."},
	 {"post_thetas",
	 (PyCFunction)PyGetPostThetas,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the post thetas."},
	 {"post_posted_counts",
	 (PyCFunction)PyGetPostPostedCounts,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the number of posted counts."},
	 {"post_cascade_sizes",
	 (PyCFunction)PyGetPostCascadeSizes,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the number of posted counts."},
	 {"post_births",
	 (PyCFunction)PyGetPostBirthdays,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the post births."},
	 {"post_deaths",
	 (PyCFunction)PyGetPostDeaths,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the post deaths."},
	 {"post_live_post_counts",
	 (PyCFunction)PyGetPostLivePosts,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of live post counts."},
	 {"post_user_opinions",
	 (PyCFunction)PyGetPostUserOpinios,
	 METH_VARARGS | METH_KEYWORDS,
	 "Get a list of the post user opinions."},
	{NULL} /* Sentinel */
};

PyObject * PyDynamicsSimulateDynamics(PyDynamics *self, PyObject *args, PyObject *kwds){
	static char *kwlist[] = {
		"number_of_iterations",
		"min_opinion", 
		"max_opinion",
 		"phi",
		"mu", 
		"delta",
		"posting_filter", 
		"receiving_filter",
		"rewire",
		"b",
		"feed_size",
		"cascade_stats_output_file",
		"verbose", 
		"rand_seed",
		NULL
	};

	PyObject *bObject = NULL;
	PyArrayObject *bArray = NULL;
	Py_ssize_t pyNumberOfIterations = 0;
	unsigned long int numberOfIterations = 0;
	FLOAT minOpinion = 0.;
	FLOAT maxOpinion = 0.;	
	FLOAT phi = 0.;
	FLOAT mu = 0.;
	FLOAT delta = 0.;
	int postingFilter = 0;
	int receivingFilter = 0;
	int allowRewire = 1;
	int feedSize = 5;
	char* cascadeStatsOutputFile = NULL; 
	int isVerbose = (int) self->verbose;
	FLOAT *b;
	int randSeed = NULL;

	#ifdef USE_FLOAT_32
	if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									"nfffffiip|Oispi",
									 kwlist,
									 &pyNumberOfIterations,
									 &minOpinion,
									 &maxOpinion,
									 &phi,
									 &mu,
									 &delta,
									 &postingFilter,
									 &receivingFilter,
									 &allowRewire,
									 &bObject,
									 &feedSize,
									 &cascadeStatsOutputFile,
									 &isVerbose,
									 &randSeed)){
		PyErr_SetString(PyExc_TypeError,
		"Wrong args in simulate_dynamics.");
		return NULL;
	}
	#else//double
		if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									"ndddddiip|Oispi",
									 kwlist,
									 &pyNumberOfIterations,
									 &minOpinion,
									 &maxOpinion,
									 &phi,
									 &mu,
									 &delta,
									 &postingFilter,
									 &receivingFilter,
									 &allowRewire,
									 &bObject,
									 &feedSize,
									 &cascadeStatsOutputFile,
									 &isVerbose,
									 &randSeed)){
		PyErr_SetString(PyExc_TypeError,
		"Wrong args in simulate_dynamics.");
		return NULL;
	}
	#endif

	numberOfIterations = (unsigned long int) pyNumberOfIterations;
	if (!randSeed){
		randSeed = time(NULL);
	}else{
		if (self->verbose)
			printf("Setting rand. seed to: %u.\n", randSeed);
	}
	srand48((unsigned int) randSeed);

	if (!self->network){
		PyErr_SetString(PyExc_TypeError, "Set the network before executing the dyanamics (set_network).");
		return NULL;
	}

	self->verbose = (bool) isVerbose;
	bool rewire = (bool) allowRewire;
	// printf("rewire: %d\n", rewire);

	unsigned long int bCount = 0;
	if (bObject){
		if (self->verbose)
			printf("Setting b values.\n");

		#ifdef USE_FLOAT_32
			if (bObject && !(bArray = convertToFLOATArray(bObject, 1, 1))) {
				PyErr_SetString(PyExc_TypeError,
				"The b attribute must be a FLOAT32 numpy array.");
				Py_XDECREF(bArray);
				return NULL;
			}
		#else//double
			if (bObject && !(bArray = convertToDoubleArray(bObject, 1, 1))) {
				PyErr_SetString(PyExc_TypeError,
				"The b attribute must be a FLOAT64 numpy array.");
				Py_XDECREF(bArray);
				return NULL;
			}
		#endif
		
		if (bArray) {
			bCount = (unsigned long int) PyArray_SIZE(bArray);
			b = PyArray_DATA(bArray);
		}else{
			PyErr_SetString(PyExc_TypeError, "The list of opinions, b, has not been loaded.");
			return NULL;
		}
		
		if (b && bCount != self->network->vCount) {
			PyErr_SetString(
				PyExc_TypeError, "The list of opinions, b, should have the same dimension as the number of vertices.");
			Py_XDECREF(bArray);
			return NULL;
		}

		//Copy b to self->b
		if (self->b){
			free(self->b);
		}
		self->b = (FLOAT *) malloc(bCount * sizeof(FLOAT));

		for (unsigned int i = 0; i<bCount; i++){
			if (b[i] > maxOpinion || b[i] < minOpinion){
				PyErr_SetString(PyExc_TypeError, "b is out of range. The b values should be between min_opinion and max_opinion.\n");
				return NULL;
			}
			self->b[i] = (FLOAT) b[i];
		}
	}
	
	if (!self->b){
		PyErr_SetString(PyExc_TypeError, "b was not previously defined.\n");
		return NULL;
	}

	if (!self->postList){
		if (self->verbose)
			printf("Creating the post list.\n");
		self->postList = malloc(sizeof(PostList));
		createPostList(self->postList);
	}
	
	if (!self->feeds){
		if (self->verbose)
			printf("Creating feeds.\n");
		self->feeds = malloc(sizeof(Feeds));
		createFeeds(self->feeds, self->network, feedSize);
		if (self->verbose)
			printf("Randomly populate feeds.\n");
		populateFeedRandom(self->network, self->feeds, self->postList, self->b, maxOpinion, minOpinion, self->feeds->feedSize);
	}

	//Stablishing receiving filter
	if (receivingFilter == CUSTOM && self->receivingFilterType != CUSTOM){
		PyErr_SetString(PyExc_TypeError, "The CUSTOM receiving filter should be previously defined (use set_receiving_filter).\n");
		return NULL;
	}

	if (!self->receivingFilterTypes || self->receivingFilterType != receivingFilter){
		if (self->receivingFilterTypes){
			if (self->verbose)
				printf("Cleaning receiving filter types.\n");
			free(self->receivingFilterTypes);
			self->receivingFilterTypes = NULL;
		}
		if (self->verbose)
			printf("Initializing receiving filter types.\n");
		self->receivingFilterTypes = (char *) malloc(self->network->vCount * sizeof(char));
		initilizePostingFilterTypes(self->receivingFilterTypes, receivingFilter,  self->network->vCount);
	}

	//Stablishing posting filters
	if (postingFilter == CUSTOM && self->postingFilterType != CUSTOM){
		PyErr_SetString(PyExc_TypeError, "The CUSTOM posting filter should be previously defined (use set_posting_filter).\n");
		return NULL;
	}

	if (!self->postingFilterTypes || self->postingFilterType != postingFilter){
		if (self->postingFilterTypes){
			if (self->verbose)
				printf("Cleaning posting filter types.\n");
			free(self->postingFilterTypes);
			self->postingFilterTypes = NULL;
		}
		if (self->verbose)
			printf("Initializing posting filter types.\n");
		self->postingFilterTypes = (char *) malloc(self->network->vCount * sizeof(char));
		initilizePostingFilterTypes(self->postingFilterTypes, postingFilter,  self->network->vCount);
	}

	self->postingFilterType = postingFilter;
	self->receivingFilterType = receivingFilter;

	if (self->verbose){
		printf("========================================\n");
		printf("Dynamics symmary:\n");
		printf("========================================\n");
	}

	if (self->verbose){
		if (self->network->vCount < 50){
			printf("b: [");
			unsigned int bLength = 3;
			if (bLength > self->network->vCount)
				bLength = self->network->vCount;
			for (unsigned int i=0; i<bLength; i++){
				printf(" %f", self->b[i]);
			}
			if (self->network->vCount <= 3)
				printf("]\n");
			else
				printf(" ...]\n");
		}else{
			printf("b array has been loaded.\n");
		}		
	}
	
	if (self->verbose){
		printf("number_of_iterations: %u\n", (unsigned int) numberOfIterations);
		printf("min_opinion: %f\n", minOpinion);
		printf("max_opinion: %f\n", maxOpinion);	
		printf("phi: %f\n", phi);
		printf("mu: %f\n", mu);
		printf("delta: %f\n", delta);
		printf("posting_filter: ");  
		printProbabilityTypeName(postingFilter);
		printf("\n");
		printf("receiving_filter: ");
		printProbabilityTypeName(receivingFilter);
		printf("\n");
		if (rewire)
			printf("Dynamics with rewiring\n");
		else
			printf("Dynamics without rewiring\n");
		printf("feed_size: %d\n",feedSize);
		if (cascadeStatsOutputFile)
			printf("cascade_stats_output_file: %s.csv\n", cascadeStatsOutputFile); 
	}
	
	if (self->verbose){
		printf("========================================\n");
	}

	//Executing the dynamics
	FLOAT phiPosting = 0.;//fixed value, but in futire we can change it.
	self->rewiringsCount += simulate(self->b, self->network, self->feeds, self->postList, self->postingFilterTypes, self->receivingFilterTypes, self->stubborn, feedSize, mu, delta, phiPosting, phi, maxOpinion, minOpinion, (unsigned long int) numberOfIterations, self->executedIterations, rewire, self->verbose);

	//Setting the executed iterations
	self->executedIterations += (unsigned long int) numberOfIterations;

	//Save post list
	if (cascadeStatsOutputFile){
		if (self->verbose)
			printf("Saving file: %s.csv\n", cascadeStatsOutputFile);
		savePostList(self->postList, cascadeStatsOutputFile);
	}

	Py_XDECREF(bArray);
	
	if (self->verbose)
		printf("Done!\n");

	// return pyOutputDict;
	return Py_BuildValue("", NULL);
}

PyObject *PySetPostingFilter(PyDynamics *self, PyObject *args, PyObject *kwds){
	static char *kwlist[] = {
		"posting_filter",
		NULL
	};

	PyObject *postingFilterObject = NULL;
	PyArrayObject *postingFilterArray = NULL;

	if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									 "O",
									 kwlist,
									 &postingFilterObject)) {
		return NULL;
	}
	
	if (!(postingFilterArray = convertToIntegerArray(postingFilterObject, 1, 1))) {
		PyErr_SetString(PyExc_TypeError,
						"Error creating posting filter array.");
		return NULL;
	}

	unsigned long int size = (unsigned long int) PyArray_SIZE(postingFilterArray);

	if(size != self->network->vCount){
		PyErr_SetString(PyExc_TypeError,
						"The list of posting filters, should have the same dimension as the number of vertices.");
		return EXIT_FAILURE;
	}

	npy_int64 *postingFilterData = PyArray_DATA(postingFilterArray);
	
	//Stablishing the posting filters
	if (self->postingFilterTypes){
		if (self->verbose)
			printf("Cleaning posting filter types.\n");
		free(self->postingFilterTypes);
		self->postingFilterTypes = NULL;
	}
	if (self->verbose)
		printf("Initializing posting filter types.\n");
	self->postingFilterTypes = (char *) malloc(self->network->vCount * sizeof(char));
	// escrever o for aqui
	for (unsigned int i = 0; i<self->network->vCount; i++){
		self->postingFilterTypes[i] = (char) postingFilterData[i];
	}
	self->postingFilterType = CUSTOM;

	Py_XDECREF(postingFilterArray);
	// Py_XDECREF(postingFilterData);
	return Py_BuildValue("", NULL);
}

PyObject *PySetReceivingFilter(PyDynamics *self, PyObject *args, PyObject *kwds){
	static char *kwlist[] = {
		"receiving_filter",
		NULL
	};

	PyObject *ReceivingFilterObject = NULL;
	PyArrayObject *ReceivingFilterArray = NULL;

	if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									 "O",
									 kwlist,
									 &ReceivingFilterObject)) {
		return NULL;
	}
	
	if (!(ReceivingFilterArray = convertToIntegerArray(ReceivingFilterObject, 1, 1))) {
		PyErr_SetString(PyExc_TypeError,
						"Error creating receiving filter array.");
		return NULL;
	}
	unsigned long int size = (unsigned long int) PyArray_SIZE(ReceivingFilterArray);

	if(size != self->network->vCount){
		PyErr_SetString(PyExc_TypeError,
						"The list of receiving filters, should have the same dimension as the number of vertices.");
		return EXIT_FAILURE;
	}
	npy_int64 *receivingFilterData = PyArray_DATA(ReceivingFilterArray);
	
	//Stablishing the receiving filters
	if (self->receivingFilterTypes){
		if (self->verbose)
			printf("Cleaning receiving filter types.\n");
		free(self->receivingFilterTypes);
		self->receivingFilterTypes = NULL;
	}
	if (self->verbose)
		printf("Initializing receiving filter types.\n");
	self->receivingFilterTypes = (char *) malloc(self->network->vCount * sizeof(char));
	
	for (unsigned int i = 0; i<self->network->vCount; i++){
		self->receivingFilterTypes[i] = (char) receivingFilterData[i];
	}
	self->receivingFilterType = CUSTOM;

	Py_XDECREF(ReceivingFilterArray);
	// Py_XDECREF(receivingFilterData);
	return Py_BuildValue("", NULL);
}

PyObject *PySetStubborn(PyDynamics *self, PyObject *args, PyObject *kwds){
	static char *kwlist[] = {
		"stubborn",
		NULL
	};

	PyObject *StubbornObject = NULL;
	PyArrayObject *StubbornArray = NULL;

	if (!PyArg_ParseTupleAndKeywords(args,
									 kwds,
									 "O",
									 kwlist,
									 &StubbornObject)) {
		return NULL;
	}
	
	if (!(StubbornArray = convertToIntegerArray(StubbornObject, 1, 1))) {
		PyErr_SetString(PyExc_TypeError,
						"Error creating stubborn array.");
		return NULL;
	}
	unsigned long int size = (unsigned long int) PyArray_SIZE(StubbornArray);

	if(size != self->network->vCount){
		PyErr_SetString(PyExc_TypeError,
						"The list of stubborn, should have the same dimension as the number of vertices.");
		return NULL;
	}
	npy_int64 *stubbornData = PyArray_DATA(StubbornArray);
	
	for (unsigned int i = 0; i<self->network->vCount; i++){
		self->stubborn[i] = (bool) stubbornData[i];
	}

	Py_XDECREF(StubbornArray);
	return Py_BuildValue("", NULL);
}


PyObject *PyDestroyNetwork(PyDynamics *self){
	if (self->network)
		destroyNetwork(self->network);
	return Py_BuildValue("", NULL);
}

PyObject *PyPrintFeed(PyDynamics *self){
	if (self->network && self->feeds)
		printFeeds(self->feeds, self->network->vCount);
	else
		printf ("Empty feed.\n");
	return Py_BuildValue("", NULL);
}

PyObject *PyForceDealloc(PyDynamics *self){
	return PyDynamics_del(self);
}

static PyMethodDef PyDynamics_methods[] = {
	{"_simulate_dynamics",
	 (PyCFunction)PyDynamicsSimulateDynamics,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(SIMULATE_DYNAMICS_DOC)},
	 {"print_feeds",
	 (PyCFunction)PyPrintFeed,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(PRINT_FEEDS_DOC)},
	 {"destroy_network",
	 (PyCFunction)PyDestroyNetwork,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(DESTROY_NETWORK_DOC)},
	 {"_set_posting_filter",
	 (PyCFunction)PySetPostingFilter,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(SET_POSTING_FILTER_DOC)},
	 {"_set_receiving_filter",
	 (PyCFunction)PySetReceivingFilter,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(SET_RECEIVING_FILTER_DOC)},
	 {"_set_stubborn",
	 (PyCFunction)PySetStubborn,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(SET_STUBBORN_DOC)},
	 {"force_dealloc",
	 (PyCFunction)PyForceDealloc,
	 METH_VARARGS | METH_KEYWORDS,
	 DOCTOSTRING(FORCE_DEALLOC_DOC)},
	//  {"set_network",
	//  (PyCFunction)PySetNetwork,
	//  METH_VARARGS | METH_KEYWORDS,
	//  DOCTOSTRING(SET_NETWORK_DOC)},
	{NULL} /* Sentinel */
};

static PyTypeObject PyDynamicsType = {
	PyVarObject_HEAD_INIT(NULL, 0).tp_name = "core.Simulator",
	.tp_doc = "PyDynamics objects",
	.tp_basicsize = sizeof(PyDynamics),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	.tp_new = PyDynamics_new,
	.tp_init = (initproc) PyDynamics_init,
	.tp_dealloc = (destructor) PyDynamics_dealloc,
	.tp_finalize = PyDynamics_del,
	.tp_traverse = NULL, 
	.tp_clear = NULL,
	// .tp_members = PyDynamics_members,
	.tp_members = NULL,
	.tp_methods = PyDynamics_methods,
	.tp_getset = PyDynamics_getsetters,
};

char simulatorDocs[] = "This is the C module of opiniondyanmics.";

static PyModuleDef simulator_mod = {PyModuleDef_HEAD_INIT,
										 .m_name = "simulator",
										 .m_doc = simulatorDocs,
										 .m_size = -1,
										 .m_methods = NULL,
										 .m_slots = NULL,
										 .m_traverse = NULL,
										 .m_clear = NULL,
										 .m_free = NULL};

PyMODINIT_FUNC
PyInit_opiniondynamics_core(void)
{
	import_array();

	PyObject *m;
	if (PyType_Ready(&PyDynamicsType) < 0) {
		return NULL;
	}
	m = PyModule_Create(&simulator_mod);
	if (m == NULL) {
		return NULL;
	}
	Py_INCREF(&PyDynamicsType);
	if (PyModule_AddObject(m, "Dynamics", (PyObject *)&PyDynamicsType) < 0) {
		Py_DECREF(&PyDynamicsType);
		Py_DECREF(m);
		return NULL;
	}

	if (PyModule_AddStringConstant(m,"__version__", TOKENTOSTRING(ODVersion))<0) {
		Py_DECREF(m);
		return NULL;
	}

	return m;
}
