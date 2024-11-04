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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>
#include <math.h>

#define __STRINGIFY(x) #x
#define TOKENTOSTRING(x) __STRINGIFY(x)
#define DOCTOSTRING(x) __STRINGIFY(x)

#define FLOAT float //double
#define USE_FLOAT_32

#define PI 3.14159265358979

#define ARRAY_STEP 50//Use it for mallocs and reallocs

#define PROGRESS_BAR(_iteration, _total) \
    if(_total < 100 || _iteration % (unsigned long int)(_total/100) == 0 || _iteration == _total-1){ \
        double _progress = (double) (_iteration+1) / (double) _total; \
        unsigned char _bar_width = 20; \
        unsigned char _num_bars = (char)(_progress * _bar_width); \
        printf("Progress: [%.*s%*s] %3.0f%%\r", \
                _num_bars, "====================", \
                _bar_width - _num_bars, "", \
                _progress * 100); \
        fflush(stdout); \
    }

bool uintIsInArray(unsigned int number, unsigned int *array, unsigned int arraySize);
unsigned int uintWhereInArray(unsigned int item, unsigned int *array, unsigned int arraySize);
FLOAT drawRandomFLOATNumber(void);
unsigned int drawRandomUIntNumber(void);
