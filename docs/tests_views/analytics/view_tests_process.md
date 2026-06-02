# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.

# Objective

I want to create success and failure tests for the views associated with every process-related URL
(using the `Process` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new Process object.
- Only users with a role that has `can_add_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action.
- The new process created belongs to the campaign of the user creator. Test it.
- During creation, it is optional to include one mp3 file or a zip with multiple mp3 files. 
If that is the case, it will create Audio objects related to this new Process object. 
It will be mandatory to also include agent and agent date in the form. 
Test all situations.

### GET
- Returns a modal HTML with an empty form to create a new Process object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with model Typification
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action.

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Process object.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only edit Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can edit any Process from the Campaign. Test it.
- Form does not provide fields to include Audio objects, only to edit its own attrs. Test it.
- A Process object can be edited only when it is active and not running and its state is not `PROCESS_STATE_FINISHED`. Test it.

### GET
- Returns a modal HTML with a populated form with some attributes from a Process object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Process object.
- Users with a role that has the `can_delete_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- All Audio objects associated with the selected Process object are also soft-deleted.
- Users with scope `SCOPE_USER` can only soft-delete Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can soft-delete any Process from the Campaign. Test it.
- A Process object can be soft-deleted only when it is active and not running. Test it.

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Process object.
- Users with a role that has the `can_delete_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- All Audio objects associated with the selected Process object are also reactivated.
- Users with scope `SCOPE_USER` can only soft-delete Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can soft-delete any Process from the Campaign. Test it.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows watching details of an existent Process object when a User has no permission to edit.
- Users with a role that has the `can_list_process` and does not have `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only "read" Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "read" any Process from the Campaign. Test it.
- A Process object with state `PROCESS_STATE_FINISHED` can only be "read" despite the fact User has a role with `can_edit_process`, but respect scope. Test it.

### GET
- Returns a modal HTML with a populated form with some attributes from a Process object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Process object, even when soft-deleted.
- Users with a role that has the `can_history_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only "history" Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "history" any Process from the Campaign. Test it.

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Process object selected has been modified.


## API Action: `API_ACTION_LIST`
- Allows listing Process objects, even soft-deleted ones.
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only list Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can list any Process from the Campaign. Test it.

### GET
- Returns an HTML table with a row per every Process object.
- Table response is paginated
- If no Process objects return an empty table


## API Action: `API_ACTION_START`
- Allows setting a Process object to be processed by Celery tasks. Only when state is `PROCESS_STATE_READY`. Test it.
- Before that initializing Process object and Audio objects related to that process, setting is_running attribute to True. Test it.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only start Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can start any Process from the Campaign. Test it.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_CONTINUE`
- Allows setting a task to be processed by Celery worker later. Only when this process has been 
started before and was stopped manually or failed in execution (based on state attribute). Test it.
- Before that re-initializing Process object and Audio objects related to that process, setting is_running attribute to True. Test it.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only continue Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can continue any Process from the Campaign. Test it.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_PAUSE`
- Allows manually stopping a running Celery task associated with the Process object selected. Test it.
- Depending on which stage was the task, the final state could be any XXX_STOPPED. Test it.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only pause Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can pause any Process from the Campaign. Test it.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_RESTART`
- It allows manually full or partial reset of the whole process. Check for an extra param in the url.
- If extra param is `RESTART_EXTRA_FULL` is a full reset:
  - Process object state will be `PROCESS_STATE_READY`. Test it.
  - Audio objects will have `transcription` attribute deleted. Test it.
  - Then the Process object will be sent to be processed by a Celery task from scratch. Test it.
- If extra param is `RESTART_EXTRA_PARTIAL` is a partial reset:
  - Process object state will be `PROCESS_STATE_TRANSCRIBED`. Test it.
  - Then the Process object will be sent to be processed by a Celery task. Test it.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only restart Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can restart any Process from the Campaign. Test it.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_MAIN`
- It allows loading the correct action button to be executed on a selected Process object if an extra param is provided.
- If no extra param is provided in the url, it will show the regular "Añadir" button. Test it.
- If an extra param is provided, it will use it to get the Process object selected then, according to its state, provide a corresponding action button. Test it.
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can only "main" Process belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "main" any Process from the Campaign. Test it.

### GET
- Get an HTML button with a corresponding action to perform: "Añadir", "Procesar", "Pausar" or "Continuar", 
"Reprocesar" (this one with sub options: "Reprocesar todo" and "Volver a tipificar"). Test it


## API Action: `API_ACTION_RELATED`
- It is not a specific action, it is used to perform actions over child Audio objects from a parent Process object.
- Only some actions are allowed.

### API Action: `API_ACTION_ADD`
- Allows adding a new Audio object related to its Process parent object
- Only users with a role that has `can_add_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action.
- Users with scope `SCOPE_USER` can add only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can add Audio objects to Processes from the Campaign. Test it.
- The new Audio object created belongs to the campaign of the user creator and to the Process object related. Test it.
- During creation, can only add one audio per time. Test it.
- This action applies only when a Process object parent is active and not running and its state is not finished. Test it.

#### GET
- Returns a modal HTML with an empty form to create a new Audio object.

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_EDIT`
- Allows editing an existent Audio object related to its Process parent object
- Users with a role that has the `can_edit_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can edit only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can edit Audio objects to Processes from the Campaign. Test it.
- the Edit form will not have an input file to modify the audio attribute. Test it.
- This action applies only when a Process object parent is active and not running and its state is not finished. Test it.

#### GET
- Returns a modal HTML with a populated form with some attributes from an Audio object selected

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Audio object related to its Process parent object
- Users with a role that has the `can_delete_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can soft-delete only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can soft-delete Audio objects to Processes from the Campaign. Test it.
- When an Audio object is deleted, it must also hard-delete AudioSegments objects, ProcessResults objects and Elasticsearch documents associated if it exists. Test it.
- This action applies only when a Process object parent is active and not running. Test it.

#### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a reactivate Audio object related to its Process parent object
- Users with a role that has the `can_delete_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can reactivate only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can reactivate Audio objects to Processes from the Campaign. Test it.
- This action applies only when a Process object parent is active and not running and its state is not finished. Test it.

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_READ`
- Allows watching details of an existent Audio object, related to its Process parent object, when a User has no permission to edit.
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can "read" only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "read" Audio objects to Processes from the Campaign. Test it.
- This action applies only when a Process object parent is active and is running. Test it.

#### GET
- Returns a modal HTML with a populated form with some attributes from an Audio object selected


### API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Audio object, related to its Process parent object, even when soft-deleted.
- Users with a role that has the `can_history_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can "history" only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can "history" Audio objects to Processes from the Campaign. Test it.
- This action applies always even if the parent Process object is not active. Test it.

#### GET
- Returns a modal HTML with an accordion with accordion-items for every time an Audio object selected has been modified.


### API Action: `API_ACTION_LIST`
- Allows listing Audio objects related to its Process parent object, even soft-deleted ones.
- Users with a role that has the `can_list_process` with scope `SCOPE_CAMPAIGN` or `SCOPE_USER` are able to perform this action
- Users with scope `SCOPE_USER` can list only Audio objects to Processes belonging to them. Test it.
- Users with scope `SCOPE_CAMPAIGN` can list Audio objects to Processes from the Campaign. Test it.
- This action applies always even if the parent Process object is not active. Test it.

#### GET
- Returns an HTML table with a row per every Audio object.
- Table response is not paginated
- If no Process objects return an empty table


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_process` attributes. Process model uses 
all of them except SCOPE_GLOBAL. When scope is SCOPE_NONE cannot be performed any action at all.
* Tests for the Wordlist and Typification models are already implemented, you can use it as a reference but create a different test file.
* Readonly users generally only have the `can_history_process` attribute activated, thus activate the `can_list_process` property.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
* There is a folder named "audios_for_testing" with a MP3 audio and zip file (containing two mp3 audio files), to be used when those kinds of files are needed for testing.
* Make sure that all tests created passed.
