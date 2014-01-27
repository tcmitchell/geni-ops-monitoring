#!/usr/bin/python

# tutorial
# http://docs.python.org/2/library/json.html

import json


def main():

    vals = [0.5, 0.6, 0.7, 0.8, 0.9]
    times = [1,2,3,4,5]
    j = json.dumps({'data-response': [
                      {'aggregate-name':'ig-bbn'},
                      {'aggregate-id':'urn=3243+ig-bbn'},
                      {'data-type':'memory-util'},
                      {'values': [
                        {'value':vals[0],'time':times[0]},
                        {'value':vals[1],'time':times[1]},
                        {'value':vals[2],'time':times[2]},
                        {'value':vals[3],'time':times[3]},
                        {'value':vals[4],'time':times[4]}
                        ]}
                      ] })
   
    print j

if __name__ == "__main__":
    main()
