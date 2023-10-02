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

#include "post.h"

void createPostList(PostList *postList){
    postList->numberOfPosts = 0;
    postList->post = (PostInformation *) malloc(ARRAY_STEP * sizeof(PostInformation));
    postList->maximunNumberOfPosts = ARRAY_STEP;
    return;
}

void printPostList(PostList *postList){
    if (postList->numberOfPosts == 0){
        printf("Empty list\n");
    }
    else{
        for (unsigned int i=0; i < postList->numberOfPosts; i++){
            printf("%lu -> theta=%lf, count=%u, cascadeSize=%u, birth=%lu, death=%lu, livePosts=%u, user opinion=%lf\n", postList->post[i].id, postList->post[i].theta, postList->post[i].postedCount, postList->post[i].cascadeSize, postList->post[i].birth, postList->post[i].death, postList->post[i].livePosts, postList->post[i].userOpinion);
        }
    }
}

unsigned long int createNewPost(unsigned int iteration, PostList *postList, FLOAT userOpinion, FLOAT theta){
    unsigned int id = postList->numberOfPosts;
    if (postList->numberOfPosts >= postList->maximunNumberOfPosts){
        postList->maximunNumberOfPosts += ARRAY_STEP;
        postList->post = (PostInformation *) realloc(postList->post, postList->maximunNumberOfPosts * sizeof(PostInformation));
    }
    postList->post[id].id = id;
    postList->post[id].theta = theta;
    postList->post[id].postedCount = 0;
    postList->post[id].birth = iteration;
    postList->post[id].death = 0;
    postList->post[id].livePosts = 0;
    postList->post[id].cascadeSize = 0;
    postList->post[id].userOpinion = userOpinion;
    postList->numberOfPosts++;
    return postList->post[id].id;
}

void incrementPostedCount(PostList *postList, unsigned int  postId){
    if (postId >= postList->numberOfPosts){
        printf("Error (incrementPostedCount): this post doesn't exist!\n");
        return;
    }
    postList->post[postId].postedCount++;
    postList->post[postId].livePosts++;
}

void incrementCountCascade(PostList *postList, unsigned int  postId){
    if (postId >= postList->numberOfPosts){
        printf("Error (incrementCountCascade): this post doesn't exist!\n");
        return;
    }
    postList->post[postId].cascadeSize++;
}

void createFeeds(Feeds *feeds, Network *network, unsigned int feedSize){
    feeds->feedSize = feedSize;
    feeds->feed = (unsigned long int **) malloc(network->vCount * sizeof(unsigned long int*));
    feeds->initialPos = (unsigned int *) malloc(network->vCount * sizeof(unsigned int));
    feeds->numberOfElements = (unsigned int *) malloc(network->vCount * sizeof(unsigned int));

    for (unsigned int i=0; i < network->vCount; i++){
        feeds->feed[i] = (unsigned long int *) malloc(feedSize * sizeof(unsigned long int));
        for (unsigned int j=0; j < feeds->feedSize; j++)
            feeds->feed[i][j] = j;
            
        feeds->initialPos[i] = 0;
        feeds->numberOfElements[i] = 0;
    }
    return;
}

unsigned int getFeedSize(Feeds *feeds, unsigned int v){
    return feeds->numberOfElements[v];
}

//Rever esta funçao com cuidado (aonde usa ela):
void pushFeed(Feeds *feeds, PostList *postList, unsigned int v, unsigned int postId, unsigned long iteration){
    unsigned int position = 0;
    if (feeds->numberOfElements[v] == 0){
        feeds->numberOfElements[v] = 1;
        feeds->initialPos[v] = 0;
    }
    else{
        feeds->initialPos[v] = (feeds->initialPos[v] + 1) % feeds->feedSize;//insert in the next position of the circular array
        if (feeds->numberOfElements[v] < feeds->feedSize)
            feeds->numberOfElements[v] ++; 
        else{//(feeds->numberOfElements[v] == feeds->feedSize) 
            destroyPost(postList, feeds->feed[v][feeds->initialPos[v]], iteration);//if overwrite, it is necessary to decrement the feed count in the PostInformation
            //remember that feeds->feed[v][feeds->initialPos[v]] will be overwritten
        }
    }
    feeds->feed[v][feeds->initialPos[v]] = postId;
    return;
}

void insertPostWithoutPriority(Feeds *feeds, PostList *postList, unsigned int v, unsigned int postId, unsigned long iteration){
    unsigned int position = 0;
    unsigned int postIdOld = 0;
    if (feeds->numberOfElements[v] == 0){//If there is no post this one will be the first
        feeds->numberOfElements[v] = 1;
        feeds->initialPos[v] = 0;
    }
    else{
        if (feeds->numberOfElements[v] == feeds->feedSize){
            position = (feeds->initialPos[v] + feeds->feedSize - feeds->numberOfElements[v] + 1) % feeds->feedSize;
            // destroyPost(postList, feeds->feed[v][feeds->initialPos[v]], iteration);
            postIdOld = feeds->feed[v][position];
            postList->post[postIdOld].livePosts--;
            if (postList->post[postIdOld].livePosts == 0)
                postList->post[postIdOld].death = iteration;
        }else{
            position = (feeds->initialPos[v] + feeds->feedSize - feeds->numberOfElements[v]) % feeds->feedSize;
            //insert in the next position of the circular array, but in this case do not move the pointer
            feeds->numberOfElements[v] ++;
        }
    }
    feeds->feed[v][position] = postId;
}

unsigned int popFeed(Feeds *feeds, unsigned int v){
    unsigned int postId = -1;
    if (getFeedSize(feeds, v) > 0){
        postId = feeds->feed[v][feeds->initialPos[v]];
    }
    feeds->initialPos[v] = (feeds->initialPos[v] + feeds->feedSize - 1) % feeds->feedSize;
    feeds->numberOfElements[v] --;
    return postId;
}

//test if this is working!
unsigned int getPostFromFeed(Feeds *feeds, unsigned int v){
    unsigned int postId = 0;
    unsigned int position = 0;
    if (getFeedSize(feeds, v) > 0){
        postId = feeds->feed[v][feeds->initialPos[v]];
    }
    if (feeds->numberOfElements[v] != feeds->feedSize){ //If it is not full it is necessary to move
        position = (feeds->initialPos[v] + feeds->feedSize - feeds->numberOfElements[v]) % feeds->feedSize;
        feeds->feed[v][position] = postId;
    }
    feeds->initialPos[v] = (feeds->initialPos[v] + feeds->feedSize - 1) % feeds->feedSize;
    return postId;
}

bool postInFeed(Feeds *feeds, unsigned int v, unsigned long int post_id){
    unsigned int feedPosition = 0;
    for (unsigned int j=0; j < getFeedSize(feeds, v); j++){
        feedPosition = (feeds->initialPos[v] + feeds->feedSize - j) % feeds->feedSize;//"+ feeds.feedSize" to avoid negative numbers
        if (feeds->feed[v][feedPosition] == post_id)
            return true;
    }
    return false;
}

void printFeeds(Feeds *feeds, unsigned int adjlistSize){
    unsigned int feedPosition = 0;
    for (unsigned int i=0; i < adjlistSize; i++)
    {
        printf("%u (%u) -> ", i, getFeedSize(feeds, i));
        if (getFeedSize(feeds, i) > 0)
            for (unsigned int j=0; j < getFeedSize(feeds, i); j++){
                feedPosition = (feeds->initialPos[i] + feeds->feedSize - j) % feeds->feedSize;//"+ feeds.feedSize" to avoid negative numbers
                printf("%lu ", feeds->feed[i][feedPosition]);
            }
        else{
            printf ("empty");
        }
        printf("\n");
    }
}

void destroyPost(PostList *postList, unsigned int  postId, unsigned long int iteration){
    if (postId >= postList->numberOfPosts){
        printf("Error (destroyPost): this post doesn't exist!\n");
        printf("%u %lu\n\n", postId, postList->numberOfPosts);
        return;
    }
    if (postList->post[postId].livePosts == 0){
        printf("Error (destroyPost): post %u is already destroyed!\n", postId);
        return;
    }
    else{
        postList->post[postId].livePosts--;
        if (postList->post[postId].livePosts == 0)
            postList->post[postId].death = iteration;
    }
}

void destroyFeed(Feeds *feeds, unsigned int NetworkVCount){
    if (feeds){
        if (feeds->initialPos){
            free(feeds->initialPos);
            feeds->initialPos = NULL;
        }
        if (feeds->numberOfElements){
            free(feeds->numberOfElements);
            feeds->numberOfElements = NULL;
        }
        for (unsigned int i=0; i<NetworkVCount; i++){
            if (feeds->feed[i]){
                free(feeds->feed[i]);
                feeds->feed[i] = NULL;
            }
        }
        if (feeds->feed){
            free(feeds->feed);
            feeds->feed = NULL;
        }
        free(feeds);
        feeds = NULL;
    }
    return;
}

void destroyPostList(PostList *postList){
    if (postList){
        if (postList->post)
            free(postList->post);
        free(postList);
        postList = NULL;
    }
    return;
}

void populateFeedRandom(Network *network, Feeds *feeds, PostList *postList, FLOAT *b, FLOAT maxB, FLOAT minB, unsigned int feedSize){
    unsigned long int postId;
    unsigned long int iteration = 0;
    FLOAT theta = 0;
    for (unsigned int i=0; i < network->vCount; i++){
        for (unsigned int j=0; j < feedSize; j++){
            theta = drand48();
            theta *= (maxB - minB);
            theta += minB;
            postId = createNewPost(iteration, postList, b[i], theta);
            pushFeed(feeds, postList, i, postId, iteration);
            incrementCountCascade(postList, postId);
            incrementPostedCount(postList, postId);
        }
    }
    return;
}

void savePostList(PostList *postList, char *nameOut){
    FILE * fp;
    char file_name[200];
    strcpy(file_name, nameOut);
    strcat(file_name, ".csv");
    fp = fopen (file_name, "w");
    
    fprintf(fp,"post_id,theta,count,cascade_size,birth,death,live_posts,user_opinion\n");
    if (postList->numberOfPosts == 0){
        printf("Empty list\n");
    }
    else{
        for (unsigned int i=0; i < postList->numberOfPosts; i++){
            fprintf(fp, "%lu,%lf,%u,%u,%lu,%lu,%u,%lf\n", postList->post[i].id, postList->post[i].theta, postList->post[i].postedCount, postList->post[i].cascadeSize, postList->post[i].birth, postList->post[i].death, postList->post[i].livePosts, postList->post[i].userOpinion);
        }
    }
    fclose(fp);
}

