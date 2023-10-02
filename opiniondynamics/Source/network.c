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
#include "network.h"

void edgeList2Network(Network *network, EdgeList edgeList, bool verbose){
	network->vCount = edgeList.vCount;
	network->isDirected = edgeList.isDirected;
	network->invertedAdjlist = (unsigned int **) malloc(edgeList.vCount * sizeof(unsigned int*));
	network->neighborsCount = (unsigned int *) malloc(edgeList.vCount * sizeof(unsigned int));

	for (unsigned int i=0; i<edgeList.vCount; i++)
		network->neighborsCount[i] = 0;

	for (unsigned int i=0; i<edgeList.eCount; i++){
		if (verbose){ 
			PROGRESS_BAR(i, edgeList.eCount);
		}
		Edge edge = edgeList.edges[i];
		unsigned int source = edge.source;
		unsigned int target = edge.target;
		
		if(network->neighborsCount[target] == 0){//First alloc
			network->invertedAdjlist[target] = (unsigned int *) malloc(ARRAY_STEP * sizeof(unsigned int));//add memory to be able to store
		}else if(network->neighborsCount[target] % ARRAY_STEP == 0){
			network->invertedAdjlist[target] = (unsigned int *) realloc(network->invertedAdjlist[target], (network->neighborsCount[target] + ARRAY_STEP) * sizeof(unsigned int)); //add memory to be able to store
		}
		network->invertedAdjlist[target][network->neighborsCount[target]] = source; 
		network->neighborsCount[target]++;
		
		if (!edgeList.isDirected){ //For undirected the edges have to be added from the complementary direction
			if(network->neighborsCount[source] == 0){//First alloc
				network->invertedAdjlist[source] = (unsigned int *) malloc(ARRAY_STEP * sizeof(unsigned int));//add memory to be able to store
			}else if(network->neighborsCount[source] % ARRAY_STEP == 0){
				network->invertedAdjlist[source] = (unsigned int *) realloc(network->invertedAdjlist[source], (network->neighborsCount[source] + ARRAY_STEP) * sizeof(unsigned int)); //add memory to be able to store
			}
			network->invertedAdjlist[source][network->neighborsCount[source]] = target; 
			network->neighborsCount[source]++;
		}
	}
	if (verbose)
		printf("\n");
	return;
}

void network2EdgeList(Network *network, EdgeList *edgeList, bool verbose){
	unsigned int source = 0;
	edgeList->vCount = network->vCount;
	edgeList->isDirected = network->isDirected;
	edgeList->eCount = 0;
	edgeList->edges = (Edge*) malloc((edgeList->eCount + ARRAY_STEP) * sizeof(Edge));
	
	for (unsigned int target = 0; target < edgeList->vCount; target++){
		for (unsigned int sourceIndex = 0; sourceIndex < network->neighborsCount[target]; sourceIndex++){
			source = network->invertedAdjlist[target][sourceIndex];
			//realloc when necessary
			if (edgeList->eCount % ARRAY_STEP == 0)
				edgeList->edges = (Edge*) realloc(edgeList->edges, (edgeList->eCount + ARRAY_STEP) * sizeof(Edge));
			edgeList->edges[edgeList->eCount].source = source;
			edgeList->edges[edgeList->eCount].target = target;
			edgeList->eCount++;
		}
	}
	return;
}

void printNetwork(Network *network){
    if (network->isDirected)
        printf("Directed network with %u nodes.\n", network->vCount);
    else
        printf("Undirected network with %u nodes.\n", network->vCount);

	printf("Inverted edge list:\n");
	for (unsigned int target=0; target < network->vCount; target++){
		printf("%u <- ", target);
		for (unsigned int source=0; source<network->neighborsCount[target]; source++){
			printf("%u ", network->invertedAdjlist[target][source]);
		}
		printf("\n");
	}
	return;
}

void rewireConnectionNewTarget(Network *network, unsigned int nodeId, unsigned int target, unsigned int newTarget){
	unsigned int position = uintWhereInArray(nodeId, network->invertedAdjlist[target], network->neighborsCount[target]);

	network->invertedAdjlist[target][position] = network->invertedAdjlist[target][network->neighborsCount[target]-1];
	network->neighborsCount[target]--;
	
    //Reallocating the invertedAdjlist array, if necessary (to reduce the memory use).
    if(network->neighborsCount[target] == 0){//if 0 free because it will be allocated if necessary
		if (network->invertedAdjlist[target]){
			free(network->invertedAdjlist[target]);
			network->invertedAdjlist[target] = NULL;
		}
	}else if(network->neighborsCount[target] % ARRAY_STEP == 0){
		network->invertedAdjlist[target] = (unsigned int *) realloc(network->invertedAdjlist[target], (network->neighborsCount[target]) * sizeof(unsigned int));
    }

	//Creating a new edge
	if(network->neighborsCount[newTarget] == 0){//First alloc
		network->invertedAdjlist[newTarget] = (unsigned int *) malloc(ARRAY_STEP * sizeof(unsigned int));//add memory to be able to store
	}else if(network->neighborsCount[newTarget] % ARRAY_STEP == 0){
		network->invertedAdjlist[newTarget] = (unsigned int *) realloc(network->invertedAdjlist[newTarget], (network->neighborsCount[newTarget] + ARRAY_STEP) * sizeof(unsigned int)); //add memory to be able to store
	}
	network->invertedAdjlist[newTarget][network->neighborsCount[newTarget]] = nodeId;
	network->neighborsCount[newTarget]++;

    if(!network->isDirected){
        //Remove target from nodeId and replace by the new source
        position = uintWhereInArray(target, network->invertedAdjlist[nodeId], network->neighborsCount[nodeId]);
        network->invertedAdjlist[nodeId][position] = newTarget;
    }
	return;
}

bool rewireConnectionToRandom(Network *network, unsigned int target, unsigned int nodeId){
	//Return false if there is no possoble rewire
	unsigned int newTarget = (unsigned int) (lrand48() % network->vCount);
	unsigned int numberOfTries = 0;
	bool isDirected = network->isDirected;
	unsigned int maxNumberOfTries = network->vCount * 100;

	while (newTarget == target || newTarget == nodeId || uintIsInArray(nodeId, network->invertedAdjlist[newTarget], network->neighborsCount[newTarget]) == true){
        if (numberOfTries > maxNumberOfTries){
            printf("Caution: The maximum number of attempts has been reached and the rewiring has not been performed (in the rewireConnectionToRandom function).\n"); 
            return false;
		}
		newTarget = (unsigned int) (lrand48() % network->vCount);
		numberOfTries ++;
	}

	rewireConnectionNewTarget(network, nodeId, target, newTarget);
	return true;
}

unsigned int randomNeighbor(Network *network, unsigned int agent){
    return network->invertedAdjlist[agent][lrand48() % network->neighborsCount[agent]];
}

unsigned int randomNode(Network *network){
	 return (unsigned int) (lrand48() % network->vCount);
}

void destroyNetwork(Network *network){
	for (unsigned int i=0; i < network->vCount; i++){
        if (network->neighborsCount[i] > 0){
			if (network->invertedAdjlist[i]){
            	free(network->invertedAdjlist[i]);
				network->invertedAdjlist[i] = NULL;
			}
        }
    }
	if (network->invertedAdjlist){
		free(network->invertedAdjlist);
		network->invertedAdjlist = NULL;
	}
	if (network->neighborsCount){
		free(network->neighborsCount);
		network->neighborsCount = NULL;
	}
	network = NULL;
}