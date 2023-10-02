""""
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
"""
import numpy as np
import opiniondynamics_core as core

#Variables used to define probabilities
COSINE = 0 #COS_X
STRETCHED_HALF_COSINE = 1 #COS_X_2
UNIFORM = 2 #EQUAL_TRANSMISSION
HALF_COSINE = 3 #COS_X_CUT
RANDOM_DISTR = 4 #MIXED_TRANSMISSION
CUSTOM = 5 #This shall be used when the postng filter types are manually defined

class Opinion_dynamics(core.Dynamics):
    """
    Class for the simulation of the dynamics.
    Parameters
    ----------
        vertex_count : integer
                Number of network vertices.
                
        edges : numpy array
            Array of the graph edges, with the shape of (number of edges, 2).
        
        directed: boolean
            Directed network (True) or undirected network (False). True by default.
        
        verbose: boolean
            If True verbose is on.
    """
    def __init__(self, vertex_count, edges, directed = True, verbose = True):
        edges = np.array(edges)
        directed = int(directed)
        core.Dynamics.__init__(self, vertex_count = vertex_count, edges = edges, directed = directed, verbose = verbose)
        #These variables are used to avoid creating the dictionaries multiple times.
        self.generated_cascade_stats_dict = False
        self._cascade_stats_dict = None
        self.generated_post_id2stats_dict = False
        self._post_id2stats_dict = None
        ################################################################################
        self.__version__ = core.__version__

    def simulate_dynamics(self,
                          number_of_iterations,
                          phi,
                          mu, 
                          posting_filter, 
                          receiving_filter,
                          b = None,
                          feed_size = 5,
                          rewire = True,
                          cascade_stats_output_file = None,
                          min_opinion = -1, 
                          max_opinion = 1,
                          delta = 0.1,
                          verbose = True,
                          rand_seed = None):
        """
        Write doccumentation here!!!
        """
        kwargs = {"number_of_iterations": number_of_iterations,
                  "min_opinion": min_opinion, 
                  "max_opinion": max_opinion,
                  "phi": phi,
                  "mu": mu,
                  "delta": delta,
                  "posting_filter": posting_filter, 
                  "receiving_filter": receiving_filter,
                  "rewire": rewire,
                  "feed_size": feed_size,
                  "cascade_stats_output_file": cascade_stats_output_file,
                  "verbose": verbose,
                  "rand_seed": rand_seed
                }
        kwargs = {key:kwargs[key] for key in kwargs.keys() if kwargs[key] != None}
        if b is not None:
            b = np.array(b, dtype = np.single)
            kwargs.update({"b": b})
        core.Dynamics._simulate_dynamics(self, **kwargs)
        out = {"b": self.opinions, "edges": self.edge_list}

        #To allow the variables to be updated
        self.generated_cascade_stats_dict = False
        self._cascade_stats_dict = None
        self.generated_post_id2stats_dict = False
        self._post_id2stats_dict = None
        #####################################
        return out
    
    def set_posting_filter(self, posting_filter):
        """
        Write doccumentation here!
        Parameters
        ----------
        posting_filter : numpy array of integers (the array len needs to be vertex_count).
        """
        posting_filter = np.array(posting_filter, dtype=int)
        core.Dynamics._set_posting_filter(self, posting_filter)

    def set_receiving_filter(self, receiving_filter):
        """
        Write doccumentation here!
        Parameters
        ----------
        receiving_filter : numpy array of integers (the array len needs to be vertex_count).
        """
        receiving_filter = np.array(receiving_filter, dtype=int)
        core.Dynamics._set_receiving_filter(self, receiving_filter)

    def set_stubborn(self, stubborn):
        """
        Write doccumentation here!
        Set nodes that never change their opinions (numpy array of integers).
        Parameters
        ----------
        stubborn : numpy array of integers (the array len needs to be vertex_count).
        """
        stubborn = np.array(stubborn, dtype=int)
        core.Dynamics._set_stubborn(self, stubborn)

    def get_cascade_stats_dict(self):
        if self.generated_cascade_stats_dict:
            return self._cascade_stats_dict
        
        self._cascade_stats_dict = dict()
        self._cascade_stats_dict['post_id'] = self.post_ids
        self._cascade_stats_dict['theta'] = self.post_thetas
        self._cascade_stats_dict['count'] = self.post_posted_counts
        self._cascade_stats_dict['cascade_size'] = self.post_cascade_sizes
        self._cascade_stats_dict['birth'] = self.post_births
        self._cascade_stats_dict['death'] = self.post_deaths
        self._cascade_stats_dict['live_posts'] = self.post_live_post_counts
        self._cascade_stats_dict['user_opinion'] = self.post_user_opinions
        self.generated_cascade_stats_dict = True
        return self._cascade_stats_dict

    def get_cascade_stats_post_id2stats_dict(self):
        if self.generated_post_id2stats_dict:
            return self._post_id2stats_dict
        
        self._cascade_stats_dict = self.get_cascade_stats_dict()
        properties = ['theta', 'count', 'cascade_size', 'birth', 'death', 'live_posts', 'user_opinion']
        self._post_id2stats_dict = {post_id: {prop: self._cascade_stats_dict[prop][i] for prop in properties} for i,post_id in enumerate(self.post_ids)}
        self.generated_post_id2stats_dict = True
        return self._post_id2stats_dict
    
    # def __del__(self):
    #     print("Destructor")
    #     core.Dynamics.force_dealloc(self)