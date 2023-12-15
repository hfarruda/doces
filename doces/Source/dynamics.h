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

#include "post.h"
#include "utils.h"

// Posting and receiving probabilities
#define COSINE 0
#define STRETCHED_HALF_COSINE 1
#define UNIFORM 2
#define HALF_COSINE 3
#define RANDOM_DISTR 4
#define CUSTOM 5

bool drawRewire(FLOAT bOfTheSelectedNode, FLOAT neighborB);
FLOAT defineProbabilityFunction(FLOAT y, FLOAT phi, char transmissionType);
FLOAT postingFilter(FLOAT theta, FLOAT b, FLOAT phi, char probabilityFunction);
FLOAT receivingFilter(FLOAT b, FLOAT neighborB, FLOAT phi, char probabilityFunction);
FLOAT attraction(FLOAT b, FLOAT theta, FLOAT change);
FLOAT repulsion(FLOAT b, FLOAT theta, FLOAT change, FLOAT minOpinion, FLOAT maxOpinion);
FLOAT csi(FLOAT theta, FLOAT neighborB, FLOAT minOpinion, FLOAT maxOpinion);
char establishRandomDistType();
void initilizePostingFilterTypes(char *postingFilterTypes, char postingFilterType, unsigned int vCount);
void destroyPostingFilterTypes(char *postingFilterTypes);
void printProbabilityTypeName(char probType);
unsigned long int simulate( FLOAT *b, //The opinions change here
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
                            bool verbose);

//Transmission probaiblity -> postingFilter
//Distribution probability -> receivingFilter
