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

bool uintIsInArray(unsigned int number, unsigned int *array, unsigned int arraySize){
    for (unsigned int i=0; i<arraySize; i++){
        if (array[i] == number){
            return true;
        }
    }
    return false;
}

unsigned int uintWhereInArray(unsigned int item, unsigned int *array, unsigned int arraySize){
    for (unsigned int i=0; i<arraySize; i++){
        if (array[i] == item){
            return i;
        }
    }
    printf("Error: number not found in array!\n");
    return EXIT_FAILURE;
}

FLOAT drawRandomFLOATNumber(){
    // FLOAT number = (FLOAT) drand48();
    #ifdef _WIN32
        return (FLOAT) rand() / RAND_MAX; 
    #else// Non-Windows implementation using drand48() 
        return (FLOAT) drand48();
    #endif
}

unsigned int drawRandomUIntNumber(){
    // FLOAT number = (FLOAT) drand48();
    #ifdef _WIN32
        return return (unsigned int) rand();
    #else// Non-Windows implementation using drand48() 
        return (unsigned int) lrand48();
    #endif
}
