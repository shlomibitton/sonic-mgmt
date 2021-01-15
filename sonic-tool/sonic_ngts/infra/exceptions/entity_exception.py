"""
This is a base class for exception handling that occurred during a topology entity setup
"""


class TopologyEntityError(Exception):

    '''
        An abstract exception class for Regression Errors
    '''

    def __init__(self, msg):
        super(TopologyEntityError, self).__init__(msg)
