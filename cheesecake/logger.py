import sys, re

########################################################
############### PRODUCERS ##############################
########################################################

class Message(object): 
    def __init__(self, keywords, args): 
        self.keywords = keywords 
        self.args = args 

    def content(self): 
        return " ".join(map(str, self.args))

    def prefix(self): 
        return "[%s] " % (":".join(self.keywords))

    def __str__(self): 
        return self.prefix() + self.content() 

class Producer(object):
    """ Log producer API which sends messages to be logged
        to a 'consumer' object, which then prints them to stdout,
        stderr, files, etc.
    """
    
    Message = Message  # to allow later customization 
    keywords2consumer = {}

    def __init__(self, keywords): 
        if isinstance(keywords, str): 
            keywords = tuple(keywords.split())
        self.keywords = keywords

    def __repr__(self):
        return "<Producer %s>" % ":".join(self.keywords) 

    def __getattr__(self, name):
        if name[0] == '_': 
            raise AttributeError, name
        producer = self.__class__(self.keywords + (name,))
        setattr(self, name, producer)
        return producer 
    
    def __call__(self, *args):
        func = self._getconsumer(self.keywords)
        if func is not None:
            func(self.Message(self.keywords, args))
 
    def _getconsumer(self, keywords):
        for i in range(len(self.keywords), 0, -1):
            try:
                return self.keywords2consumer[self.keywords[:i]]
            except KeyError:
                continue
        return self.keywords2consumer.get('default', default_consumer)

default = Producer('default')

def default_consumer(msg): 
    print str(msg) 

Producer.keywords2consumer['default'] = default_consumer 

class MultipleProducer(Producer):

    def __call__(self, *args, **kwargs):
        for func in self._getconsumer(self.keywords):
            if func is not None:
                return func(self.Message(self.keywords, args), **kwargs)

    def _getconsumer(self, keywords):
        found_consumer = False
        for keyword in keywords:
            consumer = self.keywords2consumer.get((keyword,))
            found_consumer = True
            yield consumer
        if not found_consumer:
            yield self.keywords2consumer.get('default', default_consumer)

########################################################
############### CONSUMERS ##############################
########################################################

class File(object): 
    def __init__(self, f): 
        assert hasattr(f, 'write')
        assert isinstance(f, file) or not hasattr(f, 'open') 
        self._file = f 

    def __call__(self, msg): 
        print >>self._file, str(msg)

class Path(File): 
    def __init__(self, filename, append=False): 
        mode = append and 'a' or 'w'
        f = open(str(filename), mode, buffering=1)
        super(Path, self).__init__(f) 

def STDOUT(msg): 
    print >>sys.stdout, str(msg) 

def STDERR(msg): 
    print >>sys.stderr, str(msg) 
    
def setconsumer(keywords, consumer): 
    # normalize to tuples 
    if isinstance(keywords, str): 
        keywords = tuple(map(None, keywords.split()))
    elif not isinstance(keywords, tuple): 
        raise TypeError("key %r is not a string or tuple" % (keywords,))
    if consumer is not None and not callable(consumer): 
        if not hasattr(consumer, 'write'): 
            raise TypeError("%r should be None, callable or file-like" % (consumer,))
        consumer = File(consumer)
    #print "setting consumer for " + str(keywords) + "to " + str(consumer)
    Producer.keywords2consumer[keywords] = consumer 

