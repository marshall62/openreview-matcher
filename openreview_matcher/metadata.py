import abc
import openreview
import pdb

class OpenReviewFeature(object):
    """
    Defines an abstract base class for OpenReview matching features.

    Classes that extend this object must implement a method called "score" with the following arguments: (signature, forum)

    Example:

    def score(signature, forum):
        ## compute feature score
        return score

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def score(self, signature, forum):
        """
        @signature - tilde ID of user
        @forum - forum of paper

        """
        return 0.0


def generate_metadata(forum_ids, groups, features, invitation, metadata=[]):
    """
    Generates metadata notes for each paper in @papers, with features defined in the list @features, for each group in
    the list @groups

    Arguments:
        @forum_ids - a list of forum IDs. Generate and return a metadata note for every forum in this list.
        @groups - a list of openreview.Group objects. Metadata notes will have a separate record for each group in the
            list. Features will be computed against every paper in @papers and every member of each group in @groups.
        @features - a list of OpenReviewFeature objects. Each OpenReviewFeature has a method, "score()", which computes
            a value given a user signature and a forum ID.
        @conference - the group ID of the conference that this metadata applies to.
        @metadata (optional) - a list of openreview.Note objects representing existing metadata notes to be overwritten.
            Use if metadata has already been posted before.

    Returns:
        a list of openreview.Note objects representing metadata. Each metadata note is added to the forum that it refers to.

    """
    for f in features:
        assert isinstance(f, OpenReviewFeature), 'all features must be of type features.OpenReviewFeature'

    metadata_by_forum = {n.forum: n for n in metadata}

    conference = invitation.split('/-/')[0]

    empty_metadata_params = {
        'invitation': invitation,
        'readers': [conference],
        'writers': [conference],
        'signatures': [conference]
    }

    for forum in forum_ids:
        content = {'groups': {group.id: {} for group in groups.values()}}

        if forum not in metadata_by_forum:
            metadata_by_forum[forum] = openreview.Note(forum = forum, content = content, **empty_metadata_params.copy())
        else:
            metadata_by_forum[forum].content = content

        for group in groups.values():

            for signature in group.members:
                featurevec = {f.name: f.score(signature, forum) for f in features if f.score(signature, forum) > 0}
                if featurevec != {}:
                    metadata_by_forum[forum].content['groups'][group.id][signature] = featurevec


    return metadata_by_forum.values()
