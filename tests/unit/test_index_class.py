"""
Prepare enviornment.
    >>> import _path_cheesecake
    >>> from cheesecake.cheesecake_index import Index
    >>> from _helper_cheesecake import Glutton

*****

Default maximum value for an index should be 0.
    >>> index = Index()
    >>> index.max_value
    0

To learn a class name, ask for its representation.
    >>> Index
    <Index class: unnamed>
    >>> class NamedIndex(Index):
    ...     pass
    >>> NamedIndex
    <Index class: NamedIndex>

*****

Create two indices.
    >>> big_index = Index()
    >>> index = Index()
    >>> index.name = 'small_index'

Add one index to another.
    >>> big_index.add_subindex(index)
    >>> index in big_index.subindices
    True

Try to add non-Index object as a subindex.
    >>> big_index.add_subindex(42)
    Traceback (most recent call last):
      ...
    ValueError: subindex has to be instance of Index

Now remove subindex.
    >>> big_index.remove_subindex('small_index')
    >>> index in big_index.subindices
    False

*****

Test passing subindices to index constructor.
    >>> def create_index(name):
    ...     idx = Index()
    ...     idx.name = name
    ...     return idx

    >>> index_one = create_index('one')
    >>> index_two = create_index('two')
    >>> index_three = create_index('three')
    >>> index = Index(index_one, index_two, index_three)

    >>> def get_names(indices):
    ...     return map(lambda idx: idx.name, indices)

    >>> get_names(index.subindices)
    ['one', 'two', 'three']
    >>> index.remove_subindex('one')
    >>> get_names(index.subindices)
    ['two', 'three']

*****

Test requirements.
    >>> class NewIndex(Index):
    ...     def compute(self, one, two, three):
    ...         pass
    >>> new = NewIndex()
    >>> new.requirements
    ['one', 'two', 'three']

Now create other index and add it to the NewIndex.
    >>> class OtherIndex(Index):
    ...     def compute(self, four):
    ...         pass
    >>> other = OtherIndex()
    >>> other.requirements
    ['four']
    >>> new.add_subindex(other)
    >>> new.requirements
    ['one', 'two', 'three', 'four']

*****

Index which throws an Exception during computation will
get removed from the list of subindices.
    >>> class BadIndex(Index):
    ...     max_value = 10
    ...     def compute(self):
    ...         raise Exception("No reason.")
    >>> bad_index = BadIndex()
    >>> index = Index(bad_index)
    >>> bad_index in index.subindices
    True
    >>> index.compute_with(Glutton())
    0
    >>> bad_index in index.subindices
    False
    >>> index.max_value
    0
"""
