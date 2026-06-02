# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.


# Objective

I want to create success and failure tests for the views associated with every agent-related URL
(using the `Agent` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new Agent object.
- Users with a role that has `can_add_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a modal HTML with an empty form to create a new Agent object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with a model Agent object
- Users with a role that has the `can_list_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Agent object.
- Users with a role that has the `can_edit_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with a populated form with some attributes from an Agent object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Agent object.
- Users with a role that has the `can_delete_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Agent object.
- Users with a role that has the `can_delete_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent Agent object when a User has no permission to edit.
- Users with a role that has the `can_list_agent` and does not have `can_edit_agent` are able to perform this action.
Also needs scope `SCOPE_CAMPAIGN`.

### GET
- Returns a modal HTML with a populated form with some attributes from an Agent object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Agent object, even when soft-deleted.
- Users with a role that has the `can_history_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with an accordion with accordion-items for every time an Agent object selected was changed.


## API Action: `API_ACTION_LIST`
- Allows listing Agent objects, even soft-deleted ones.
- Users with a role that has the `can_list_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns an HTML table with a row per every Agent object.
- Table response is paginated
- If no Agent objects return an empty table


## API Action: `API_ACTION_RESET`
- This action is not allowed for this model.


## API Action: `API_ACTION_EXPORT`
- Allows downloading an Excel file (xlsx) with a list of all Agent objects
- Users with a role that has the `can_export_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action
- There is a column named "id" which can be used to validate data from an Excel file downloaded

### GET
- Downloads an Excel file with Agent objects per every row.


## API Action: `API_ACTION_IMPORT`
- Allows creating Agent objects with an Excel file uploaded. Not updating or deleting allowed, just creation.
- Users with a role that has the `can_import_agent` with scope `SCOPE_CAMPAIGN` are able to perform this action
- New agents imported will belong to the same campaign of the user creator.
- Not duplicated names are allowed

### GET
- Returns a modal Form to upload an Excel file

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_agent` attributes. 
For the Agent model only 
SCOPE_NONE and SCOPE_CAMPAIGN apply.
* Tests for the User, Role, Campaign and Config models are already implemented, you can use it as a reference but create a different test file.
* Readonly users generally only have the `can_history_agent` attribute activated, thus activate the `can_list_agent` property.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
