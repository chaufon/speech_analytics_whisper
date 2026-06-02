# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models 
are inherited from base classes provided by that package.


# Objective

I want to create success and failure tests for the views associated with every audiosegment-related
URL(using the `AudioSegment` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_RELATED`
- It is not a specific action, it is used to perform actions over child AudioSegments objects 
from a parent Audio object. 
- It is the only Audio-url related, no need to be tested.
- Only some actions are allowed.

### API Action: `API_ACTION_ADD`
- It is not allowed


### API Action: `API_ACTION_EDIT`
- Allows editing an existent AudioSegment object related to its Audio parent object
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can edit only AudioSegment objects to Audios belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can edit AudioSegment objects to Audios from the Campaign. Test it.
- This action applies only when a Process object parent is active and not running and its state is not finished. Test it.

#### GET
- Returns a modal HTML with a populated form with some attributes from an AudioSegment object selected

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_DELETE`
- It is not allowed at all.


### API Action: `API_ACTION_REACTIVATE`
- It is not allowed at all.


### API Action: `API_ACTION_READ`
- Allows watching details of an existent AudioSegment object, related to its Audio parent object, when a User has no permission to edit.
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can "read" only AudioSegment objects to Audios belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "read" AudioSegment objects to Audios from the Campaign. Test it.

#### GET
- Returns a partial template from aa AudioSegment showing some attributes.


### API Action: `API_ACTION_HISTORY`
- It is not allowed at all.


### API Action: `API_ACTION_LIST`
- Allows listing AudioSegment objects related to its Audio parent object.
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can list only AudioSegment objects to Audios belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can list AudioSegment objects to Audios from the Campaign. Test it.
- This action applies always even if the parent Process object is not active. Test it.

#### GET
- Returns a modal with an accordion with every AudioSegment object grouped by minute.
- If an Audio object has no transcription, returns only the audio player


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_process` attributes. Process model uses 
all of them except SCOPE_GLOBAL. When scope is SCOPE_NONE cannot be performed any action at all.
* Tests for the Wordlist, Typification and Process models are already implemented; you can use them 
as a reference but create a different test file.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
* There is a folder named "audios_for_testing" with a mp3 audio and zip file (containing two mp3 audio files), to be used when those kinds of files are needed for testing.
* Make sure that all tests created passed.
