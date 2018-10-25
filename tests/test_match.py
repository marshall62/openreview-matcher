import unittest
import json
import matcher
import os
import openreview


def post_json(client, url, json_dict, headers=None):
    """Send dictionary json_dict as a json to the specified url """
    if headers:
        return client.post(url, data=json.dumps(json_dict), content_type='application/json', headers=headers)
    else:
        return client.post(url, data=json.dumps(json_dict), content_type='application/json')

def json_of_response(response):
    """Decode json from response"""
    return json.loads(response.data.decode('utf8'))


# N.B.  The app we are testing uses a logger that generates error messages when given bad inputs.  This test fixture does just that.
# It verifies that bad inputs result in correct error status returns.  However you will see stack dumps which are also produced by the logger
# These stack dumps do not represent test cases that are failing!
class TestFlaskApi(unittest.TestCase):

    def setUp (self):
        # Use env vars because Flask app needs to get them from there so it can call its OR Client.
        # Use of user/pw should not be necessary because I send a token to flask which then passes it to the OR Client.
        # But the Client class doesn't initialize properly with only a token if user/pw are not set.
        os.environ['OPENREVIEW_BASEURL'] = 'http://localhost:3000'
        os.environ['OPENREVIEW_USERNAME'] = 'OpenReview.net'
        os.environ['OPENREVIEW_PASSWORD'] = 'd0ntf33dth3tr0lls'
        self.app = matcher.app.test_client()
        matcher.app.testing = True
        self.or_client = openreview.Client()

    def tearDown (self):
        pass

    # A valid token and a valid config note id which is associated with meta data that the matcher can run with to produce results.
    # The config note of this test points to meta data for ICLR.  These tokens aren't easy to create in this test code though so
    # we don't do testing with valid inputs.  Instead we mock the openreview.Client class (see mock_or_client.py) so it will behave
    # as if all the calls to the API are valid.
    '''
    def test_valid_inputs(self):
        # TODO the headers are not working correctly when it reaches the endpoint
        response = post_json(self.app, '/match', {"configNoteId": self.config_note.id},
                             headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7Il9pZCI6IjViMDA2MDk5NzEyNjFiNWU0MGM2NzZjMyIsImlkIjoiT3BlblJldmlldy5uZXQiLCJlbWFpbGFibGUiOmZhbHNlLCJjZGF0ZSI6MTUzMTE3MDUyNzQ3NiwiZGRhdGUiOm51bGwsInRtZGF0ZSI6MTUzMTE3MDUyNzY4NSwidGRkYXRlIjpudWxsLCJ0YXV0aG9yIjoiT3BlblJldmlldy5uZXQiLCJzaWduYXR1cmVzIjpbIn5TdXBlcl9Vc2VyMSJdLCJzaWduYXRvcmllcyI6WyJPcGVuUmV2aWV3Lm5ldCJdLCJyZWFkZXJzIjpbIk9wZW5SZXZpZXcubmV0Il0sIm5vbnJlYWRlcnMiOltdLCJ3cml0ZXJzIjpbIk9wZW5SZXZpZXcubmV0Il0sIm1lbWJlcnMiOlsiflN1cGVyX1VzZXIxIl0sInByb2ZpbGUiOnsiaWQiOiJ-U3VwZXJfVXNlcjEiLCJmaXJzdCI6IlN1cGVyIiwibWlkZGxlIjoiIiwibGFzdCI6IlVzZXIiLCJlbWFpbHMiOlsib3BlbnJldmlldy5uZXQiXX19LCJkYXRhIjp7fSwiaXNzIjoib3BlbnJldmlldyIsIm5iZiI6MTUzOTcxMjk3NSwiaWF0IjoxNTM5NzEyOTc1LCJleHAiOjE1Mzk3OTkzNzV9.5Xodx6nzLmmZ6ECFPvh2AyKDqJ5JThNIRQbC5Ol0eKQ'})

        # response_json = json_of_response(response)
        assert response.status_code == 200
        # not sure how to take apart the json in response,  Its a string with a dict inside a list that has
        # the stuff from OpenReviewException
    '''

    # The Authorization header is missing and passed along with a working configNoteId.   Should get back a 400
    def test_missing_auth_header (self):
        response = post_json(self.app, '/match', {'configNoteId': 'ok'},
                             headers={'a': 'b'})
        assert response.status_code == 400


    # An invalid token is passed along with a working configNoteId.   Should get back a 400
    def test_invalid_token (self):
        response = post_json(self.app, '/match', {'configNoteId': 'ok'},
                             headers={'Authorization': 'Bearer BOGUS.TOKEN'})
        assert response.status_code == 400

    # A valid token is passed but a config note id that generates an internal error in OR client.   Should get back a 500 indicating violation
    def test_internal_error (self):
        response = post_json(self.app, '/match', {'configNoteId': 'internal error'},
                             headers={'Authorization': 'Bearer Valid'})
        assert response.status_code == 500


    # A valid token is passed but a config note id that has forbidden access.   Should get back a 403 indicating violation
    def test_forbidden_config (self):
        response = post_json(self.app, '/match', {'configNoteId': 'forbidden'},
                             headers={'Authorization': 'Bearer Valid'})
        assert response.status_code == 403

    
    # A valid token is passed but an invalid config note id.   Should get back a 404 indicating resource not found
    def test_nonExistent_config (self):
        response = post_json(self.app, '/match', {'configNoteId': 'nonExist'},
                             headers={'Authorization': 'Bearer Valid'})
        assert response.status_code == 404


    # A valid token and valid config note Id.  The match task will run and succeed.
    def test_valid_inputs (self):
        response = post_json(self.app, '/match', {'configNoteId': 'ok'},
                             headers={'Authorization': 'Bearer Valid'})
        assert response.status_code == 200


# if __name__ == "__main__":
#     unittest.main()