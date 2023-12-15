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
#include "utils.h"
#include "network.h"

typedef struct {
    unsigned long int id;
    FLOAT theta;
    unsigned int postedCount; //memorization
    unsigned int cascadeSize; //Number of times it was posted
    unsigned long int birth;
    unsigned long int death;
    unsigned int livePosts;
    FLOAT userOpinion; //Opinion of the user that posted
} PostInformation;

typedef struct {
    PostInformation *post;
    unsigned long int numberOfPosts;
    unsigned long int maximunNumberOfPosts; //To control the size of the array
} PostList;

typedef struct {
    unsigned long int **feed; //Store the IDs
    unsigned int *initialPos;
    unsigned int *numberOfElements;
    unsigned int feedSize;
} Feeds;

void createPostList(PostList *postList);
void printPostList(PostList *postList);
unsigned long int createNewPost(unsigned int iteration, PostList *postList, FLOAT userOpinion, FLOAT theta);
void incrementPostedCount(PostList *postList, unsigned int  postId);
void incrementCountCascade(PostList *postList, unsigned int  postId);
void createFeeds(Feeds *feeds, Network *network, unsigned int feedSize);
unsigned int getFeedSize(Feeds *feeds, unsigned int v);
void pushFeed(Feeds *feeds, PostList *postList, unsigned int v, unsigned int postId, unsigned long iteration);
void insertPostWithoutPriority(Feeds *feeds, PostList *postList, unsigned int v, unsigned int postId, unsigned long iteration);
unsigned int popFeed(Feeds *feeds, unsigned int v);
unsigned int getPostFromFeed(Feeds *feeds, unsigned int v);
bool postInFeed(Feeds *feeds, unsigned int v, unsigned long int post_id);
void printFeeds(Feeds *feeds, unsigned int adjlistSize);
void destroyPost(PostList *postList, unsigned int  postId, unsigned long int iteration);
void destroyFeed(Feeds *feeds, unsigned int NetworkVCount);
void destroyPostList(PostList *postList);
void populateFeedRandom(Network *network, Feeds *feeds, PostList *postList, FLOAT *b, FLOAT maxB, FLOAT minB, unsigned int feedSize);
void savePostList(PostList *postList, char *nameOut);
