import re

from collections import defaultdict
from collections import Counter

from gensim.models.tfidfmodel import TfidfModel
from gensim import corpora
from openreview_matcher.models import preprocess
from openreview_matcher.models import base_model
from openreview_matcher.preprocessors import pos_regex

class Model(base_model.Model):
    def __init__(self, params=None):
        self.tfidf_dictionary = corpora.Dictionary()
        self.document_tokens = []

        # a dictionary keyed on reviewer signatures, containing a BOW representation of that reviewer's Archive (Ar)
        self.bow_by_signature = defaultdict(Counter)

        # a dictionary keyed on forum IDs, containing a BOW representation of the paper (P)
        self.bow_by_forum = defaultdict(Counter)

        if params:
            self.my_param = params['my_param']
            print "    parameter my_param loaded: ",self.my_param

    def fit(self, train_data, archive_data):
        """
        Fit the model to the data.

        Arguments
            @train_data: an iterator over records (dicts) that contains the training data.
            Records must have a "content" field containing a string and a "forum" field
            containing the record's forum ID.

            @archive_data: an iterator over records (dicts) that contains each reviewer's
            archive. Records must have a "content" field containing a string representing
            the archive, and a "reviewer_id" field with the reviewer's OpenReview ID.

        Returns
            None

        """

        for record in train_data:
            tokens = pos_regex.preprocess(record['content']['archive'], mode='chunks')
            self.tfidf_dictionary.add_documents([tokens])

            if 'forum' in record:
                self.bow_by_forum[record['forum']].update({t[0]:t[1] for t in self.tfidf_dictionary.doc2bow(tokens)})
            self.document_tokens += [tokens]

        for archive in archive_data:

            tokens = pos_regex.preprocess(record['content']['archive'], mode='chunks')
            self.tfidf_dictionary.add_documents([tokens])

            if 'reviewer_id' in archive:
                self.bow_by_signature[archive['reviewer_id']].update({t[0]:t[1] for t in self.tfidf_dictionary.doc2bow(tokens)})
            self.document_tokens += [tokens]

        # get the BOW representation for every document and put it in corpus_bows
        self.corpus_bows = [self.tfidf_dictionary.doc2bow(doc) for doc in self.document_tokens]

        # generate a TF-IDF model based on the entire corpus's BOW representations
        self.tfidf_model = TfidfModel(self.corpus_bows)

    def predict(self, note_record):
        """
        predict() should return a list of openreview user IDs, in descending order by
        expertise score in relation to the test record.

        Arguments
            @test_record: a note record (dict) representing the note to rank against.

            Testing records should have a "forum" field. This means that the record
            is identified in OpenReview by the ID listed in that field.

        Returns
            a list of reviewer IDs in descending order of expertise score

        """

        forum = note_record['forum']
        scores = [(signature, self.score(signature, forum)) for signature, _ in self.bow_by_signature.iteritems()]
        rank_list = [signature for signature, score in sorted(scores, key=lambda x: x[1], reverse=True)]

        return rank_list

    def score(self, signature, forum):
        """
        Returns a score from 0.0 to 1.0, representing the degree of fit between the paper and the reviewer

        """
        forum_bow = [(id,count) for id,count in self.bow_by_forum[forum].iteritems()]
        reviewer_bow = [(id,count) for id,count in self.bow_by_signature[signature].iteritems()]
        forum_vector = defaultdict(lambda: 0, {idx: score for (idx, score) in self.tfidf_model[forum_bow]})
        reviewer_vector = defaultdict(lambda: 0, {idx: score for (idx, score) in self.tfidf_model[reviewer_bow]})

        return sum([forum_vector[k] * reviewer_vector[k] for k in forum_vector])


