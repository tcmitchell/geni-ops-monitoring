#!/usr/bin/python

# tutorial
# http://docs.python.org/2/library/json.html

import json
#import time



def get_values():

    vals = [0.5, 0.6, 0.7, 0.8, 0.9]
    times = [1,2,3,4,5]
   
    j = json.dumps({'response-type': 'data-poll',
                    'aggregate-name':'ig-bbn',
                    'aggregate-id':'urn=3243+ig-bbn',
                    'data-type':'memory-util',
                    'num-values':5,
                    'values': (vals[0],vals[1],vals[2],vals[3],vals[4]),
                    'times': (times[0],times[1],times[2],times[3],times[4])
                    })

    return j
    

if __name__ == "__main__":
    get_values()
