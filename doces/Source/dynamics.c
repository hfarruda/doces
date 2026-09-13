/*
MIT License

Copyright (c) 2023 Henrique F. de Arruda, Kleber A. Oliveira, and Yamir Moreno

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

#include "dynamics.h"

bool drawRewire(FLOAT bOfTheSelectedNode, FLOAT neighborB){
    FLOAT y = fabs(bOfTheSelectedNode - neighborB);
    FLOAT probability = 0.;
    FLOAT drawnNumber = 0.;
    if (y > 1.){
        probability = pow(cos(PI/2. * y), 2.);
        if (drawRandomFLOATNumber() < probability){
            return true;
        }
    }
    return false;
}

FLOAT defineProbabilityFunction(FLOAT y, FLOAT phi, char functionType){
    FLOAT chosenProbability = 1.;
    switch (functionType){
        case STRETCHED_HALF_COSINE: chosenProbability = pow(cos((y * PI)/4. + phi), 2.);
        break;
        case COSINE: chosenProbability = pow(cos(PI/2. * y + phi), 2.);
        break;
        case UNIFORM: chosenProbability = 1.;
        break;
        case HALF_COSINE: 
            if (y < 1.) 
                chosenProbability = pow(cos(PI/2. * y), 2.); 
            else 
                chosenProbability = 0.;
        break;
        case REVERSED_HALF_COSINE:
            if (y > 1.)
                chosenProbability = pow(cos(PI/2. * y), 2.);
            else
                chosenProbability = 0.;
        break;
        default: printf("ERROR (defineProbabilityFunction): unknown functionType: %u.\n", (unsigned int) functionType); 
        break;
    }
    return chosenProbability;
}

FLOAT evaluateFilter(FLOAT difference, FLOAT phi, const FilterConfiguration *configuration, unsigned int node){
    int64_t selector = configuration->nodeFilters[node];
    if (selector >= 0)
        return defineProbabilityFunction(difference, phi, (char) selector);

    const ProbabilityTable *table = &configuration->tables[(size_t) (-selector - 1)];
    double value = (double) difference;
    size_t lower = 0;
    size_t upper = table->size - 1;

    /* Coverage is validated before simulation; clamp endpoint rounding. */
    if (value <= table->differences[lower])
        return (FLOAT) table->probabilities[lower];
    if (value >= table->differences[upper])
        return (FLOAT) table->probabilities[upper];

    while (upper - lower > 1){
        size_t middle = lower + (upper - lower) / 2;
        if (value < table->differences[middle])
            upper = middle;
        else
            lower = middle;
    }

    if (table->interpolation == INTERPOLATION_PREVIOUS)
        return (FLOAT) table->probabilities[lower];

    double fraction = (value - table->differences[lower]) /
                      (table->differences[upper] - table->differences[lower]);
    return (FLOAT) (table->probabilities[lower] + fraction *
                   (table->probabilities[upper] - table->probabilities[lower]));
}

static bool drawConfiguredRewire(FLOAT bOfTheSelectedNode, FLOAT neighborB,
                                 const FilterConfiguration *configuration, unsigned int node){
    /* Retain the original threshold and random draws for the default formula. */
    if (configuration == NULL || configuration->nodeFilters[node] == REVERSED_HALF_COSINE)
        return drawRewire(bOfTheSelectedNode, neighborB);

    FLOAT difference = (FLOAT) fabs(bOfTheSelectedNode - neighborB);
    FLOAT probability = evaluateFilter(difference, 0., configuration, node);
    return drawRandomFLOATNumber() < probability;
}

FLOAT postingFilter(FLOAT theta, FLOAT b, FLOAT phi, char probabilityFunction){
    FLOAT y = (FLOAT) fabs(theta - b);
    return defineProbabilityFunction(y, phi, probabilityFunction);
}

FLOAT receivingFilter(FLOAT b, FLOAT neighborB, FLOAT phi, char probabilityFunction){
    FLOAT x =  (FLOAT) fabs(b - neighborB);
    return defineProbabilityFunction(x, phi, probabilityFunction);
}

FLOAT attraction(FLOAT b, FLOAT theta, FLOAT delta){
    FLOAT resultantB = b;
    if (b < theta){
        resultantB = b + delta;
        if (resultantB > theta)
            resultantB = theta;
    }else if (b > theta){
        resultantB = b - delta;
        if (resultantB < theta)
            resultantB = theta;
    }
    //If b == theta, there is neither attraction nor repulsion.
    return resultantB;
}

FLOAT repulsion(FLOAT b, FLOAT theta, FLOAT delta, FLOAT minOpinion, FLOAT maxOpinion){
    FLOAT resultantB = b;
    if (b < theta){ 
        resultantB = b - delta; 
        if (resultantB < minOpinion)
            resultantB = minOpinion;
    }else if (b > theta){
        resultantB = b + delta;
        if (resultantB > maxOpinion)
            resultantB = maxOpinion;
    }
    //If b == theta, there is neither attraction nor repulsion.
    return resultantB;
}

FLOAT csi(FLOAT theta, FLOAT neighborB, FLOAT minOpinion, FLOAT maxOpinion){
    //Remember that this function is defined inverted in the paper code (both are right).
    FLOAT difference = maxOpinion - minOpinion;
    return (FLOAT) 1. - fabs(theta - neighborB)/(difference);
}

char establishRandomDistType(){
    char distribution = 0;
    unsigned int selected = 0;
    selected = (unsigned int) (drawRandomUIntNumber() % 3);
    switch (selected){
        case 0: distribution = COSINE;
        break;
        case 1: distribution = UNIFORM;
        break;
        case 2: distribution = HALF_COSINE;
        break;
        default: printf("ERROR: unknown distribution type in establishRandomDistType: %d\n", selected); 
        break;
    }
    return distribution; 
}

void initilizePostingFilterTypes(char *postingFilterTypes, char postingFilterType, unsigned int vCount){
    //Passar isso para outra funcao para poder medir temporal
    for (unsigned int i=0; i < vCount; i++){
         if (postingFilterType == RANDOM_DISTR){
            //Define here a vector of P_t^{all} (the same probability for each of the cases)
            postingFilterTypes[i] = establishRandomDistType();
         }else{
            postingFilterTypes[i] = postingFilterType;
         }
    }
    return;
}

void destroyPostingFilterTypes(char *postingFilterTypes){
    if (postingFilterTypes)
        free(postingFilterTypes);
    return;
}

void printProbabilityTypeName(char probType){
    switch (probType){
        case COSINE: printf("COSINE");
        break;
        case STRETCHED_HALF_COSINE: printf("STRETCHED_HALF_COSINE");
        break;
        case UNIFORM: printf("UNIFORM");
        break;
        case HALF_COSINE: printf("HALF_COSINE");
        break;
        case RANDOM_DISTR: printf("RANDOM_DISTR");
        break;
        case CUSTOM: printf("CUSTOM");
        break;
        case REVERSED_HALF_COSINE: printf("REVERSED_HALF_COSINE");
        break;
        default: printf("\nERROR: unknown prob. type.\n"); 
        break;
    }
    return;
}

unsigned long int simulate(FLOAT *b, //The opinions change here
              Network *network,
              Feeds *feeds,
              PostList *postList,
              char *postingFilterTypes,
              char *receivingFilterTypes,
              bool *stubborn,
              unsigned int feedSize,
              FLOAT mu,
              FLOAT delta,
              FLOAT phiPosting, 
              FLOAT phiReceiving, 
              FLOAT maxOpinion, 
              FLOAT minOpinion, 
              unsigned long int nIterations, 
              unsigned long int firstIteration,
              bool rewire,
              bool verbose,
              const FilterConfiguration *postingConfiguration,
              const FilterConfiguration *receivingConfiguration,
              const FilterConfiguration *rewiringConfiguration){
    //defining variables
    unsigned int selectedNode = 0;
    unsigned long int postId = 0;
    unsigned long int neighborIndex = 0;
    FLOAT bOfTheSelectedNode = 0.;
    FLOAT theta = 0.;
    FLOAT neighborB = 0.;
    FLOAT postingFilterProbability = 0.;
    unsigned long int rewiringsCount = 0;
    bool thereIsPost = false;
    bool isNewPost = false;
    unsigned int iterationBar = 0;

    if (verbose)
        printf("Executing the dynamics.\n");

    unsigned long int lastIteration = firstIteration + nIterations + 1;
    unsigned int numberOfIterations = lastIteration-firstIteration;
    for (unsigned long int iteration = firstIteration; iteration < lastIteration; iteration++){
        if (verbose){ 
			PROGRESS_BAR(iterationBar, numberOfIterations);
            iterationBar++;
		}
        selectedNode = randomNode(network);
        bOfTheSelectedNode = b[selectedNode];
        thereIsPost = false;
        isNewPost = false;

        if (drawRandomFLOATNumber() < mu){//probability to create a new post
            //Here we define only theta because we create only the posts that will be distributed
            theta = drawRandomFLOATNumber();
            theta *= (maxOpinion - minOpinion);
            theta += minOpinion;
            isNewPost = true;
        }else{//use a post from the feed
            if (getFeedSize(feeds, selectedNode) > 0){//test if there is at least one post in the feed
                //postId = popFeed(feeds, selectedNode);
                postId = getPostFromFeed(feeds, selectedNode);
                theta = postList->post[postId].theta;
                thereIsPost = true;
            }
        }
        if (thereIsPost == true || isNewPost == true){
            if (postingConfiguration == NULL)
                postingFilterProbability = postingFilter(theta, bOfTheSelectedNode, phiPosting, postingFilterTypes[selectedNode]);
            else
                postingFilterProbability = evaluateFilter((FLOAT) fabs(theta - bOfTheSelectedNode), phiPosting, postingConfiguration, selectedNode);

            if (drawRandomFLOATNumber() < postingFilterProbability){
                if (isNewPost == true){
                    postId = createNewPost(iteration, postList, bOfTheSelectedNode, theta);
                }
                incrementCountCascade(postList, postId);
                incrementPostedCount(postList, postId);
                insertPostWithoutPriority(feeds, postList, selectedNode, postId, iteration);

                for (unsigned int neighborPos = 0; neighborPos < network->neighborsCount[selectedNode]; neighborPos++){
                    neighborIndex = network->invertedAdjlist[selectedNode][neighborPos];
                    neighborB = b[neighborIndex];
                    FLOAT receivingFilterProbability;
                    if (receivingConfiguration == NULL)
                        receivingFilterProbability = receivingFilter(bOfTheSelectedNode, neighborB, phiReceiving, receivingFilterTypes[selectedNode]);
                    else
                        receivingFilterProbability = evaluateFilter((FLOAT) fabs(bOfTheSelectedNode - neighborB), phiReceiving, receivingConfiguration, selectedNode);
                    if (drawRandomFLOATNumber() < receivingFilterProbability){
                        //only for the users that receive
                        if (postInFeed(feeds, neighborIndex, postId) == false){
                            incrementPostedCount(postList, postId);
                            pushFeed(feeds, postList, neighborIndex, postId, iteration);
                        }
                        
                        if(stubborn[neighborIndex] == false){//the stubborn agents do not change their oppinions
                            if (drawRandomFLOATNumber() <= csi(theta, neighborB, minOpinion, maxOpinion)){
                                neighborB = attraction(neighborB, theta, delta);
                            }
                            else{
                                neighborB = repulsion(neighborB, theta, delta, minOpinion, maxOpinion);
                                if (rewire){
                                    if (drawConfiguredRewire(bOfTheSelectedNode, neighborB, rewiringConfiguration, (unsigned int) neighborIndex)){
                                        rewireConnectionToRandom(network, selectedNode, neighborIndex);
                                        rewiringsCount ++;
                                    }
                                }
                            }
                            b[neighborIndex] = neighborB;
                        }else if (rewire){//stubborn can rewire even without changing opinion
                            if (drawRandomFLOATNumber() > csi(theta, neighborB, minOpinion, maxOpinion))//this is the condition for repulsion
                                if (drawConfiguredRewire(bOfTheSelectedNode, neighborB, rewiringConfiguration, (unsigned int) neighborIndex)){
                                    rewireConnectionToRandom(network, selectedNode, neighborIndex);
                                    rewiringsCount ++;
                                }
                        }

                    } 
                }
            }
        }
    }
    if (verbose)
		printf("\n");
    
    return rewiringsCount;
}

